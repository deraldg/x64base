#!/usr/bin/env python3
"""
stack_audit_v1.py -- one deterministic, read-only audit of the lower documentation stack.

Turns the one-off checks from the 2026-07-26 session into a repeatable gate.
Every finding it reports was, that day, discovered by hand -- and one of them
(CSV_VS_TABLE) was the root cause of a near-miss that would have erased
maintainer decisions from a canonical table.

Checks (all READ-ONLY; this tool never writes a table, never mutates source):

  A. CSV_VS_TABLE   Each *_IMPORT_v1.csv vs its live DBF. Catches the trap where a
                    tool reads a stale CSV snapshot and reports it as canonical
                    coverage. Flags STALE_CSV, EMPTY_TABLE, and NAME_DIVERGENCE.
  B. BANNER_CENSUS  @dottalk.file coverage over tracked src/ + include/, plus
                    authored-vs-derived provenance (a banner estate that is 100%
                    machine-derived carries no authority, however complete it looks).
  C. CONTRACT_QA    @dottalk.usage anomalies: non-canonical dialects, mention-only
                    false positives that inflate command counts, duplicate/invalid
                    command identities.
  D. SRCFILE_DRIFT  Live SRCFILE.dbf path set vs the current tracked tree
                    (uncollected additions / phantom rows).
  E. DOTREF_COV     dotref.hpp coverage measured against the LIVE SYSCMD table,
                    never against a CSV.
  F. EMBEDDED_BOM   Repo-wide scan for a UTF-8 BOM after byte 0 in C/C++ sources
                    (breaks MSVC: C3872/C2014/C2143). The prepush gate blocks these
                    at commit; this catches any already sitting in the tree.

Exit codes:  0 PASS  .  3 WARN (divergence/drift/anomaly)  .  1 FAIL (embedded BOM,
             or a WARN count that regressed against the recorded baseline).

Usage:
  python tools/fullstack_docs/stack_audit_v1.py                     # audit, compare to baseline
  python tools/fullstack_docs/stack_audit_v1.py --out-dir <DIR>     # write evidence bundle
  python tools/fullstack_docs/stack_audit_v1.py --write-baseline    # record current state as baseline
  python tools/fullstack_docs/stack_audit_v1.py --json              # machine-readable summary only

Determinism: repeated runs over an unchanged tree produce byte-identical output
except for the `generated_at` stamp (excluded from the baseline comparison).

Owner: member.derald  .  steward: member.ai.claude.cowork  .  lane: full_stack_documentation
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path

# Membership rule, settled 2026-07-26 (member.derald): git ls-files over these
# roots. Must stay identical to tools/comments/reharvest_source_comment_catalog.py
# and tools/fullstack_docs/source_census.py -- when the harvester and the guard
# disagree about what "the source set" is, every drift finding is noise. The
# 2026-07-26 reload proved it: the harvester walked the filesystem over
# {src, include, bindings} while this guard used git over {src, include}, so
# stack_audit reported 10 PHANTOM + 1 UNCOLLECTED rows that were entirely an
# artifact of the two tools answering different questions.
SRC_DIRS = ("src", "include", "bindings")
# Widened 2026-07-26 to match the harvester's DEFAULT_EXTENSIONS. Zero tracked
# .c/.inl/.ipp exist under the roots today, so this changes no count -- it closes
# a latent trap: the first such file added would otherwise be harvested into the
# catalog and then reported PHANTOM by this guard.
EXTS = {".cpp", ".hpp", ".h", ".cc", ".cxx", ".hxx", ".c", ".inl", ".ipp"}
UTF8_BOM = b"\xef\xbb\xbf"

BANNER_RE = re.compile(r"// @dottalk\.file v1\n(?://[^\n]*\n)+")
USAGE_SLASH_RE = re.compile(r"// @dottalk\.usage v1\n(?://[^\n]*\n)+")
USAGE_BLOCK_RE = re.compile(r"/\*\s*\n?\s*@dottalk\.usage v1\n(.*?)\*/", re.DOTALL)
BANNER_FIELDS = ["subsystem", "layer", "owns", "project", "lane", "owner", "status"]

# lane table  ->  (live DBF, canonical import CSV)
LANES = {
    "SYSCMD":  ("dottalkpp/data/metadata/SYSCMD.dbf",
                "dottalkpp/data/scripts/metadata/SYSCMD_IMPORT_v1.csv"),
    "SYSARGS": ("dottalkpp/data/metadata/SYSARGS.dbf",
                "dottalkpp/data/scripts/metadata/SYSARGS_IMPORT_v1.csv"),
    "SYSFUNC": ("dottalkpp/data/metadata/SYSFUNC.dbf",
                "dottalkpp/data/scripts/metadata/SYSFUNC_IMPORT_v1.csv"),
    "SYSMSG":  ("dottalkpp/data/metadata/SYSMSG.dbf",
                "dottalkpp/data/scripts/metadata/SYSMSG_IMPORT_v1.csv"),
}
SRCFILE_DBF = "dottalkpp/data/comments/SRCFILE.dbf"
DOTREF_HPP = "include/dotref.hpp"


# --------------------------------------------------------------------------- #
# minimal read-only DBF reader (handles the x64 0x64 variant used here)
# --------------------------------------------------------------------------- #
def dbf_header(path: Path):
    """(record_count, header_len, record_len) without loading the body."""
    with open(path, "rb") as fh:
        head = fh.read(12)
    if len(head) < 12:
        return (0, 0, 0)
    return (struct.unpack("<I", head[4:8])[0],
            struct.unpack("<H", head[8:10])[0],
            struct.unpack("<H", head[10:12])[0])


def dbf_fields(blob: bytes):
    """Field descriptors, defensively: keep only printable-ASCII names."""
    out, off = [], 32
    while off + 32 <= len(blob) and blob[off] != 0x0D:
        raw = blob[off:off + 11].split(b"\x00")[0]
        try:
            name = raw.decode("ascii")
        except UnicodeDecodeError:
            name = ""
        ftype = chr(blob[off + 11]) if blob[off + 11] < 128 else "?"
        flen = blob[off + 16]
        if name and name.isprintable() and ftype.isalpha():
            out.append((name, ftype, flen))
        off += 32
        if len(out) > 64:
            break
    return out


def dbf_column(path: Path, column: str):
    """Read one character column as a list of trimmed strings. Read-only."""
    blob = open(path, "rb").read()
    nrec, hlen, rlen = dbf_header(path)
    fields = dbf_fields(blob)
    offset, width = None, None
    cursor = 1  # skip the deleted flag
    for name, _ftype, flen in fields:
        if name.upper() == column.upper():
            offset, width = cursor, flen
            break
        cursor += flen
    if offset is None:
        return []
    body, vals = blob[hlen:], []
    for i in range(nrec):
        rec = body[i * rlen:(i + 1) * rlen]
        if len(rec) < offset + width:
            break
        vals.append(rec[offset:offset + width].decode("latin-1").strip())
    return vals


def csv_rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def tracked_sources(root: Path):
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", *SRC_DIRS], text=True)
        rels = out.splitlines()
    except Exception:
        rels = []
        for d in SRC_DIRS:
            base = root / d
            if base.is_dir():
                for p in base.rglob("*"):
                    if p.is_file():
                        rels.append(str(p.relative_to(root)).replace(os.sep, "/"))
    return sorted({r for r in rels if Path(r).suffix in EXTS})


def head_text(path: Path, n: int = 8192) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")[:n]
    except Exception:
        return ""


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def check_csv_vs_table(root: Path):
    """A. The stale-snapshot trap. A number is only canonical if its input is."""
    findings, detail = [], {}
    for lane, (dbf_rel, csv_rel) in LANES.items():
        dbf, csvp = root / dbf_rel, root / csv_rel
        rec = dbf_header(dbf)[0] if dbf.is_file() else None
        rows = len(csv_rows(csvp)) if csvp.is_file() else None
        detail[lane] = {"table_rows": rec, "csv_rows": rows}
        if rec is None or rows is None:
            findings.append({"check": "CSV_VS_TABLE", "lane": lane,
                             "code": "MISSING_INPUT", "severity": "WARN",
                             "message": f"{lane}: table={rec} csv={rows} (input absent)"})
            continue
        if rec == 0 and rows > 0:
            findings.append({"check": "CSV_VS_TABLE", "lane": lane,
                             "code": "EMPTY_TABLE", "severity": "WARN",
                             "message": f"{lane}: canonical table is EMPTY but CSV holds "
                                        f"{rows} rows -- lane is unseeded"})
        elif rec != rows:
            worse = "table AHEAD of csv" if rec > rows else "csv AHEAD of table"
            findings.append({"check": "CSV_VS_TABLE", "lane": lane,
                             "code": "STALE_CSV", "severity": "WARN",
                             "message": f"{lane}: table={rec} csv={rows} ({worse}) -- any "
                                        f"tool reading the CSV reports a non-canonical number"})
    return findings, detail


def check_banner_census(root: Path, files):
    """B. Coverage AND provenance. Completeness without authorship is not authority."""
    findings = {}
    covered = 0
    prov = {f: {"A": 0, "D": 0, "E": 0} for f in BANNER_FIELDS}
    zero_authored = 0
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import source_census as sc
    except Exception:
        sc = None
    for rel in files:
        text = head_text(root / rel)
        m = BANNER_RE.search(text)
        if not m:
            continue
        covered += 1
        block = m.group(0)
        vals = {f: (re.search(rf"//[ \t]*{f}:[ \t]*(.*)", block).group(1).strip()
                    if re.search(rf"//[ \t]*{f}:[ \t]*(.*)", block) else "")
                for f in BANNER_FIELDS}
        derived = {}
        if sc is not None:
            try:
                db = sc.derive_block(rel, text)
                derived = {f: (re.search(rf"//[ \t]*{f}:[ \t]*(.*)", db).group(1).strip()
                               if re.search(rf"//[ \t]*{f}:[ \t]*(.*)", db) else "")
                           for f in BANNER_FIELDS}
            except Exception:
                derived = {}
        authored_any = False
        for f in BANNER_FIELDS:
            v = vals[f]
            if not v:
                prov[f]["E"] += 1
            elif derived and v == derived.get(f, ""):
                prov[f]["D"] += 1
            else:
                prov[f]["A"] += 1
                authored_any = True
        if not authored_any:
            zero_authored += 1
    total = len(files)
    detail = {"total_source": total, "with_banner": covered,
              "coverage_pct": round(100.0 * covered / total, 1) if total else 0.0,
              "files_zero_authored_fields": zero_authored,
              "provenance": prov}
    out = []
    if covered < total:
        out.append({"check": "BANNER_CENSUS", "code": "UNCOVERED", "severity": "WARN",
                    "message": f"{total - covered} tracked source file(s) carry no @dottalk.file banner"})
    if covered and zero_authored:
        pct = 100.0 * zero_authored / covered
        out.append({"check": "BANNER_CENSUS", "code": "DERIVED_ONLY", "severity": "WARN",
                    "message": f"{zero_authored}/{covered} ({pct:.1f}%) banners carry ZERO authored "
                               f"fields -- backfill defaults, not collected knowledge. Do not treat "
                               f"status/owner/project as authority."})
    return out, detail


def check_contract_qa(root: Path, files):
    """C. Contract-space identity hygiene."""
    findings, contracts, dialects = [], [], {"slash": 0, "block": 0}
    names, mention_only = {}, []
    for rel in files:
        text = head_text(root / rel, 20000)
        blocks = [(b, "slash") for b in USAGE_SLASH_RE.findall(text)]
        blocks += [(b, "block") for b in USAGE_BLOCK_RE.findall(text)]
        if not blocks:
            if "@dottalk.usage" in text:
                mention_only.append(rel)
            continue
        for blk, dialect in blocks:
            dialects[dialect] += 1
            m = (re.search(r"(?m)^\s*(?://)?\s*command:\s*(\S+)", blk)
                 or re.search(r"(?m)^\s*(?://)?\s*surface:\s*(\S+)", blk))
            nm = m.group(1).strip().upper() if m else ""
            contracts.append(nm)
            if nm:
                names.setdefault(nm, []).append(rel)
            if dialect == "block":
                findings.append({"check": "CONTRACT_QA", "code": "NON_CANONICAL_DIALECT",
                                 "severity": "WARN",
                                 "message": f"{rel}: block-comment dialect (surface:/forms:) for {nm or '?'}"})
    if mention_only:
        findings.append({"check": "CONTRACT_QA", "code": "MENTION_ONLY", "severity": "WARN",
                         "message": f"{len(mention_only)} file(s) mention @dottalk.usage with no parseable "
                                    f"contract -- naive marker counts are inflated by these: "
                                    + ", ".join(sorted(mention_only)[:6])})
    for nm, where in sorted(names.items()):
        if nm in {"NONE", ""} or "/" in nm:
            findings.append({"check": "CONTRACT_QA", "code": "INVALID_IDENTITY", "severity": "WARN",
                             "message": f"non-identity command name {nm!r} in {where[0]}"})
        elif len(where) > 1:
            findings.append({"check": "CONTRACT_QA", "code": "DUPLICATE_IDENTITY", "severity": "WARN",
                             "message": f"command {nm} declared in {len(where)} places: {', '.join(sorted(set(where)))}"})
    detail = {"contract_blocks": len(contracts), "distinct_commands": len({c for c in contracts if c}),
              "dialects": dialects, "mention_only": len(mention_only)}
    return findings, detail


def check_srcfile_drift(root: Path, files):
    """D. Does the source-contract catalog still describe the tree?"""
    dbf = root / SRCFILE_DBF
    if not dbf.is_file():
        return ([{"check": "SRCFILE_DRIFT", "code": "MISSING_TABLE", "severity": "WARN",
                  "message": f"{SRCFILE_DBF} not found"}], {})
    paths = {p.replace("\\", "/") for p in dbf_column(dbf, "RELPATH") if p}
    tree = set(files)
    scoped = {p for p in paths if p.split("/", 1)[0] in SRC_DIRS}
    added, removed = sorted(tree - scoped), sorted(scoped - tree)
    detail = {"catalog_rows": len(paths), "catalog_rows_in_scope": len(scoped),
              "tracked_source": len(tree), "uncollected": len(added), "phantom": len(removed)}
    out = []
    if added:
        out.append({"check": "SRCFILE_DRIFT", "code": "UNCOLLECTED", "severity": "WARN",
                    "message": f"{len(added)} tracked source file(s) absent from SRCFILE: "
                               + ", ".join(added[:6]) + (" ..." if len(added) > 6 else "")})
    if removed:
        out.append({"check": "SRCFILE_DRIFT", "code": "PHANTOM", "severity": "WARN",
                    "message": f"{len(removed)} SRCFILE row(s) no longer tracked (moved/renamed/deleted): "
                               + ", ".join(removed[:6]) + (" ..." if len(removed) > 6 else "")})
    return out, detail


def check_dotref_coverage(root: Path):
    """E. Measured against the LIVE table -- never a CSV."""
    hpp, dbf = root / DOTREF_HPP, root / LANES["SYSCMD"][0]
    if not hpp.is_file() or not dbf.is_file():
        return ([], {})
    sys.path.insert(0, str(root / "dottalkpp" / "tools" / "help"))
    try:
        import generate_dotref_from_metadata_v1 as g
        _, items, _ = g.parse_header(hpp.read_text(encoding="utf-8"))
        entries = [it.name.upper() for it in items]
    except Exception as exc:
        return ([{"check": "DOTREF_COV", "code": "PARSE_FAILED", "severity": "WARN",
                  "message": f"could not parse {DOTREF_HPP}: {exc}"}], {})
    live = {v.strip().upper() for v in dbf_column(dbf, "CAN_NAME") if v.strip()}
    covered = sum(1 for e in entries if e in live)
    pct = round(100.0 * covered / len(entries), 1) if entries else 0.0
    detail = {"dotref_entries": len(entries), "live_syscmd_rows": len(live),
              "metadata_backed": covered, "coverage_pct": pct,
              "uncovered": len(entries) - covered}
    out = []
    if covered < len(entries):
        out.append({"check": "DOTREF_COV", "code": "UNCOVERED_ENTRIES", "severity": "WARN",
                    "message": f"{len(entries) - covered} dotref entr(ies) have no live SYSCMD row "
                               f"(coverage {pct}% against the TABLE)"})
    return out, detail


def check_embedded_bom(root: Path, files):
    """F. Build-breaking. Non-negotiable FAIL."""
    bad = []
    for rel in files:
        try:
            blob = (root / rel).read_bytes()
        except Exception:
            continue
        if blob.find(UTF8_BOM) > 0:
            bad.append(rel)
    out = []
    if bad:
        out.append({"check": "EMBEDDED_BOM", "code": "BOM_AFTER_BYTE0", "severity": "FAIL",
                    "message": f"{len(bad)} source file(s) carry a UTF-8 BOM after byte 0 "
                               f"(breaks MSVC C3872/C2014): " + ", ".join(bad[:8])})
    return out, {"offenders": len(bad), "files": bad[:40]}


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def run_audit(root: Path):
    files = tracked_sources(root)
    findings, detail = [], {}
    for name, fn in (("csv_vs_table", lambda: check_csv_vs_table(root)),
                     ("banner_census", lambda: check_banner_census(root, files)),
                     ("contract_qa", lambda: check_contract_qa(root, files)),
                     ("srcfile_drift", lambda: check_srcfile_drift(root, files)),
                     ("dotref_coverage", lambda: check_dotref_coverage(root)),
                     ("embedded_bom", lambda: check_embedded_bom(root, files))):
        f, d = fn()
        findings.extend(f)
        detail[name] = d
    counts = {"FAIL": sum(1 for f in findings if f["severity"] == "FAIL"),
              "WARN": sum(1 for f in findings if f["severity"] == "WARN")}
    by_check = {}
    for f in findings:
        by_check[f["check"]] = by_check.get(f["check"], 0) + 1
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "root": str(root), "tracked_source_files": len(files),
            "counts": counts, "by_check": by_check,
            "detail": detail, "findings": findings}


def comparable(summary: dict) -> dict:
    """Baseline view -- excludes the timestamp and free-text messages."""
    return {"counts": summary["counts"], "by_check": summary["by_check"],
            "detail": summary["detail"], "tracked_source_files": summary["tracked_source_files"]}


def render_markdown(s: dict, baseline_delta) -> str:
    L = [f"# Stack audit v1\n",
         f"Generated: {s['generated_at']}  ",
         f"Root: `{s['root']}`  ",
         f"Tracked source files: {s['tracked_source_files']}\n",
         f"**FAIL: {s['counts']['FAIL']}  .  WARN: {s['counts']['WARN']}**\n"]
    if baseline_delta is not None:
        L.append("## Baseline comparison\n")
        if not baseline_delta:
            L.append("No change against the recorded baseline.\n")
        else:
            L.append("| metric | baseline | now |")
            L.append("|---|---:|---:|")
            for k, (b, n) in sorted(baseline_delta.items()):
                L.append(f"| {k} | {b} | {n} |")
            L.append("")
    L.append("## Detail\n")
    for name, d in s["detail"].items():
        L.append(f"### {name}\n")
        L.append("```json")
        L.append(json.dumps(d, indent=2, sort_keys=True))
        L.append("```\n")
    L.append("## Findings\n")
    if not s["findings"]:
        L.append("(none)\n")
    else:
        L.append("| severity | check | code | message |")
        L.append("|---|---|---|---|")
        for f in s["findings"]:
            msg = f["message"].replace("|", "\\|")
            L.append(f"| {f['severity']} | {f['check']} | {f['code']} | {msg} |")
        L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out-dir", default=None, help="write report.md + summary.json here")
    ap.add_argument("--baseline", default="docs/maintenance/lanes/full_stack_documentation/"
                                          "stack_audit_baseline_v1.json")
    ap.add_argument("--write-baseline", action="store_true",
                    help="record the current state as the baseline and exit 0")
    ap.add_argument("--json", action="store_true", help="print the JSON summary only")
    ap.add_argument("--strict", action="store_true",
                    help="treat any WARN as failure (exit 3 -> 1)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    s = run_audit(root)
    bpath = root / args.baseline

    if args.write_baseline:
        bpath.parent.mkdir(parents=True, exist_ok=True)
        bpath.write_text(json.dumps(comparable(s), indent=2, sort_keys=True), encoding="utf-8")
        print(f"stack-audit: baseline written -> {bpath}")
        print(f"  FAIL={s['counts']['FAIL']}  WARN={s['counts']['WARN']}")
        return 0

    delta = None
    regressed = False
    if bpath.is_file():
        try:
            base = json.loads(bpath.read_text(encoding="utf-8"))
        except Exception:
            base = None
        if base:
            delta = {}
            for k in ("FAIL", "WARN"):
                b, n = base["counts"].get(k, 0), s["counts"][k]
                if b != n:
                    delta[f"counts.{k}"] = (b, n)
                    if n > b:
                        regressed = True
            for chk in sorted(set(base.get("by_check", {})) | set(s["by_check"])):
                b, n = base.get("by_check", {}).get(chk, 0), s["by_check"].get(chk, 0)
                if b != n:
                    delta[f"by_check.{chk}"] = (b, n)

    if args.json:
        print(json.dumps(s, indent=2, sort_keys=True))
    else:
        print("=== stack audit v1 ===")
        print(f"  root                : {s['root']}")
        print(f"  tracked source      : {s['tracked_source_files']}")
        print(f"  FAIL / WARN         : {s['counts']['FAIL']} / {s['counts']['WARN']}")
        for chk, n in sorted(s["by_check"].items()):
            print(f"     {chk:16} {n}")
        if delta is not None:
            print(f"  baseline            : {'NO CHANGE' if not delta else 'CHANGED'}")
            for k, (b, n) in sorted(delta.items()):
                print(f"     {k:26} {b} -> {n}")
        elif bpath.is_file() is False:
            print(f"  baseline            : none recorded (--write-baseline to create)")
        print()
        for f in s["findings"]:
            print(f"  [{f['severity']}] {f['check']}/{f['code']}: {f['message']}")

    if args.out_dir:
        od = Path(args.out_dir)
        od.mkdir(parents=True, exist_ok=True)
        (od / "stack_audit_summary.json").write_text(
            json.dumps(s, indent=2, sort_keys=True), encoding="utf-8")
        (od / "stack_audit_report.md").write_text(
            render_markdown(s, delta), encoding="utf-8")
        print(f"\nstack-audit: evidence -> {od}")

    if s["counts"]["FAIL"]:
        return 1
    if regressed:
        print("\nstack-audit: REGRESSION against baseline (WARN count increased).", file=sys.stderr)
        return 1
    if s["counts"]["WARN"]:
        return 1 if args.strict else 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
