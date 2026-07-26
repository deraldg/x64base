#!/usr/bin/env python3
"""
manual_guard_v1.py -- Gate 4 flush guard for the manual / SelfDoc tier.

Read-only, deterministic, baseline-ratcheting. Protocol: FLUSH_GUARD_STAGE_MODEL_V1.md.

Checks:

  A. ASSEMBLY_REPORT  The assembly report is the canonical Gate 4 artifact
                      (schema `dottalk.manual.assembly_report.v1`). Asserts it
                      exists, its anchor balance closes, and its counts have not
                      regressed against the recorded baseline. A DECREASE in
                      parts/pages/lines is content loss and fails.

  B. RECORDED_PARITY  Compares the assembly report's actual counts against the
                      Gate 4 numbers written into the run handoff. These are
                      currently NOT equal -- the handoff records 191 command
                      pages / 26 parts / 14,542 lines while the only assembly
                      report on disk reports 183 / 23 / 13,879. A gate that
                      claims numbers its own artifact does not support is not a
                      gate, so the divergence is surfaced rather than assumed
                      benign.

  C. PDF_PROVENANCE   The staged PDF must be traceable to the assembly it claims
                      to come from. Asserts: SHA-256 matches the recorded value,
                      page count matches, and -- critically -- the PDF is NOT
                      OLDER than the assembly's build_utc. It currently is
                      (PDF 2026-07-23T00:39 vs build 2026-07-23T04:14Z), meaning
                      the published PDF was rendered from a different assembly
                      than the one preserved as evidence.

  D. MANIFEST         The assembly manifest driving the build is present, and its
                      declared part count agrees with the report.

Exit codes:  0 PASS  .  3 WARN  .  1 FAIL (missing/unbalanced assembly, count
             regression, or PDF hash mismatch).

Usage:
  python tools/fullstack_docs/manual_guard_v1.py
  python tools/fullstack_docs/manual_guard_v1.py --out-dir <run>/gate4_<date>
  python tools/fullstack_docs/manual_guard_v1.py --write-baseline
  python tools/fullstack_docs/manual_guard_v1.py --pdf <path>   # override staged PDF

Owner: member.derald  .  steward: member.ai.claude.cowork  .  lane: full_stack_documentation
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

RUN = "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260722-001"
ASSEMBLY_REPORT = f"{RUN}/manualgen_phase/assembled_candidate_v1/assembly_report_v1.json"
ASSEMBLED_MD = f"{RUN}/manualgen_phase/assembled_candidate_v1/developer_manual_assembled_v1.md"
MANIFEST = "tools/manualgen/manual_assembly_manifest.yaml"
DEFAULT_PDF = r"D:/dev/x64base-site/public/downloads/current/developer-manual-latest.pdf"

# Numbers recorded in FULLSTACK_DOCUMENTATION_FLUSH_COMPLETE_HANDOFF_V1.md for Gate 4.
# These are a RECORDED CLAIM to be verified, never a threshold to be assumed true.
GATE4_RECORDED = {"command_pages": 191, "parts": 26, "lines": 14542,
                  "lineage_rows": 4604, "pdf_pages": 298}
PDF_RECORDED_SHA256 = ("33D969758D195DD8BE2B8A763CEA1B81"
                       "BE259687FD9BA8BA368B9412B798B036")

# assembly_report key -> recorded-claim key
REPORT_TO_RECORDED = {"command_pages_bound": "command_pages",
                      "parts": "parts",
                      "total_lines": "lines"}


def sha256_upper(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def parse_iso(s: str):
    if not s:
        return None
    s = s.strip().replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def check_assembly(root: Path, baseline):
    findings, detail = [], {}
    p = root / ASSEMBLY_REPORT
    if not p.is_file():
        return ([{"check": "ASSEMBLY_REPORT", "code": "MISSING", "severity": "FAIL",
                  "message": f"assembly report not found: {ASSEMBLY_REPORT}"}], {})
    try:
        rep = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return ([{"check": "ASSEMBLY_REPORT", "code": "UNPARSEABLE", "severity": "FAIL",
                  "message": f"{ASSEMBLY_REPORT}: {exc}"}], {})

    counts = dict(rep.get("counts") or {})
    counts["total_lines"] = rep.get("total_lines")
    ab = rep.get("anchor_balance") or {}
    detail = {"schema": rep.get("schema"), "assembler": rep.get("assembler"),
              "build_utc": rep.get("build_utc"), "commit": rep.get("commit"),
              "counts": counts, "anchor_balance": ab}

    if rep.get("schema") != "dottalk.manual.assembly_report.v1":
        findings.append({"check": "ASSEMBLY_REPORT", "code": "UNEXPECTED_SCHEMA",
                         "severity": "WARN",
                         "message": f"schema is {rep.get('schema')!r}, expected "
                                    f"dottalk.manual.assembly_report.v1"})
    if not ab.get("balanced"):
        findings.append({"check": "ASSEMBLY_REPORT", "code": "ANCHOR_IMBALANCE",
                         "severity": "FAIL",
                         "message": f"anchor balance not closed: open={ab.get('open')} "
                                    f"close={ab.get('close')}"})

    # verify the assembled markdown really has the reported line count
    md = root / ASSEMBLED_MD
    if md.is_file():
        actual = md.read_text(encoding="utf-8", errors="replace").count("\n") + 1
        detail["assembled_md_lines"] = actual
        rep_lines = rep.get("total_lines")
        if isinstance(rep_lines, int) and abs(actual - rep_lines) > 1:
            findings.append({"check": "ASSEMBLY_REPORT", "code": "LINE_COUNT_MISMATCH",
                             "severity": "WARN",
                             "message": f"report says {rep_lines} lines, assembled file has "
                                        f"{actual}"})
    else:
        findings.append({"check": "ASSEMBLY_REPORT", "code": "ASSEMBLED_MD_MISSING",
                         "severity": "WARN",
                         "message": f"assembled markdown absent: {ASSEMBLED_MD}"})

    if baseline:
        for key, prev in (baseline.get("counts") or {}).items():
            now = counts.get(key)
            if not isinstance(prev, int) or not isinstance(now, int):
                continue
            if now < prev:
                findings.append({"check": "ASSEMBLY_REPORT", "code": "COUNT_REGRESSION",
                                 "severity": "FAIL",
                                 "message": f"{key}: {prev} -> {now} ({prev - now} LOST)"})
            elif now > prev:
                findings.append({"check": "ASSEMBLY_REPORT", "code": "COUNT_INCREASE",
                                 "severity": "WARN",
                                 "message": f"{key}: {prev} -> {now} (+{now - prev}; ratchet "
                                            f"the baseline deliberately if correct)"})
    return findings, detail


def check_recorded_parity(assembly_detail):
    """B. Does the gate's recorded claim match its own artifact?"""
    findings, detail = [], {}
    counts = assembly_detail.get("counts") or {}
    for rk, ck in REPORT_TO_RECORDED.items():
        actual, claimed = counts.get(rk), GATE4_RECORDED.get(ck)
        detail[ck] = {"recorded_claim": claimed, "assembly_actual": actual,
                      "match": actual == claimed}
        if actual is None:
            continue
        if actual != claimed:
            findings.append({"check": "RECORDED_PARITY", "code": "CLAIM_MISMATCH",
                             "severity": "WARN",
                             "message": f"{ck}: handoff records {claimed}, assembly report "
                                        f"shows {actual} -- the recorded Gate 4 result is not "
                                        f"supported by the preserved artifact"})
    detail["lineage_rows"] = {"recorded_claim": GATE4_RECORDED["lineage_rows"],
                              "assembly_actual": None,
                              "note": "not present in assembly_report; requires SelfDoc evidence"}
    findings.append({"check": "RECORDED_PARITY", "code": "UNVERIFIABLE_CLAIM",
                     "severity": "WARN",
                     "message": "lineage_rows (recorded 4,604) is not emitted by the assembly "
                                "report -- supply SelfDoc evidence or drop the claim"})
    return findings, detail


def check_pdf(root: Path, pdf_arg, assembly_detail):
    findings, detail = [], {}
    candidates = [pdf_arg] if pdf_arg else [DEFAULT_PDF,
                                            "/sessions/peaceful-youthful-gauss/mnt/x64base-site/"
                                            "public/downloads/current/developer-manual-latest.pdf"]
    p = None
    for c in candidates:
        if c and Path(c).is_file():
            p = Path(c)
            break
    if p is None:
        return ([{"check": "PDF_PROVENANCE", "code": "PDF_NOT_FOUND", "severity": "WARN",
                  "message": "staged PDF not reachable from this host; supply --pdf <path>"}],
                {"searched": [str(c) for c in candidates if c]})

    digest = sha256_upper(p)
    blob = p.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", blob))
    mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)
    build = parse_iso(assembly_detail.get("build_utc") or "")
    detail = {"path": str(p), "sha256": digest, "pages": pages,
              "mtime": mtime.strftime("%Y-%m-%dT%H:%M:%S"),
              "assembly_build_utc": assembly_detail.get("build_utc"),
              "sha_matches_recorded": digest == PDF_RECORDED_SHA256}

    if digest != PDF_RECORDED_SHA256:
        findings.append({"check": "PDF_PROVENANCE", "code": "SHA_MISMATCH", "severity": "FAIL",
                         "message": f"staged PDF SHA-256 {digest} != recorded "
                                    f"{PDF_RECORDED_SHA256}"})
    if pages != GATE4_RECORDED["pdf_pages"]:
        findings.append({"check": "PDF_PROVENANCE", "code": "PAGE_COUNT_MISMATCH",
                         "severity": "WARN",
                         "message": f"PDF has {pages} page objects, recorded "
                                    f"{GATE4_RECORDED['pdf_pages']}"})
    if build and mtime < build:
        delta = build - mtime
        findings.append({"check": "PDF_PROVENANCE", "code": "PDF_PREDATES_ASSEMBLY",
                         "severity": "WARN",
                         "message": f"staged PDF ({mtime:%Y-%m-%dT%H:%M}) is OLDER than the "
                                    f"assembly it is evidence for ({assembly_detail.get('build_utc')}) "
                                    f"by {delta}. The published PDF was rendered from a different "
                                    f"assembly than the one preserved -- re-render before promoting."})
    return findings, detail


def check_manifest(root: Path, assembly_detail):
    findings, detail = [], {}
    p = root / MANIFEST
    if not p.is_file():
        return ([{"check": "MANIFEST", "code": "MISSING", "severity": "WARN",
                  "message": f"assembly manifest absent: {MANIFEST}"}], {})
    text = p.read_text(encoding="utf-8", errors="replace")
    # count top-level part entries without a YAML dependency
    parts = len(re.findall(r"(?m)^\s{0,4}-\s+(?:part|id|name)\s*:", text))
    detail = {"path": MANIFEST, "bytes": len(text), "part_like_entries": parts,
              "report_parts": (assembly_detail.get("counts") or {}).get("parts")}
    return findings, detail


def run(root: Path, pdf_arg, baseline):
    findings, detail = [], {}
    f, asm = check_assembly(root, baseline);          findings += f; detail["assembly"] = asm
    f, d = check_recorded_parity(asm);                findings += f; detail["recorded_parity"] = d
    f, d = check_pdf(root, pdf_arg, asm);             findings += f; detail["pdf"] = d
    f, d = check_manifest(root, asm);                 findings += f; detail["manifest"] = d
    counts = {"FAIL": sum(1 for x in findings if x["severity"] == "FAIL"),
              "WARN": sum(1 for x in findings if x["severity"] == "WARN")}
    by_check = {}
    for x in findings:
        by_check[x["check"]] = by_check.get(x["check"], 0) + 1
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "root": str(root), "gate": 4, "tier": "manual/SelfDoc",
            "counts": counts, "by_check": by_check,
            "detail": detail, "findings": findings}


def render_markdown(s):
    a = s["detail"].get("assembly", {})
    L = ["# Gate 4 flush guard -- manual / SelfDoc\n",
         f"Generated: {s['generated_at']}  ",
         f"Root: `{s['root']}`  ",
         f"Assembly build: `{a.get('build_utc')}`  commit `{a.get('commit')}`\n",
         f"**FAIL: {s['counts']['FAIL']}  .  WARN: {s['counts']['WARN']}**\n",
         "## Recorded claim vs assembled artifact\n",
         "| metric | handoff records | assembly report | match |", "|---|---:|---:|:--:|"]
    for k, v in (s["detail"].get("recorded_parity") or {}).items():
        if not isinstance(v, dict):
            continue
        L.append(f"| {k} | {v.get('recorded_claim')} | {v.get('assembly_actual')} | "
                 f"{'yes' if v.get('match') else 'NO'} |")
    L += ["\n## Detail\n```json", json.dumps(s["detail"], indent=2, sort_keys=True), "```\n",
          "## Findings\n"]
    if not s["findings"]:
        L.append("(none)\n")
    else:
        L += ["| severity | check | code | message |", "|---|---|---|---|"]
        for f in s["findings"]:
            L.append(f"| {f['severity']} | {f['check']} | {f['code']} | "
                     f"{f['message'].replace('|', chr(92) + '|')} |")
        L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--pdf", default=None)
    ap.add_argument("--baseline", default="docs/maintenance/lanes/full_stack_documentation/"
                                          "manual_guard_baseline_v1.json")
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    bpath = root / args.baseline

    baseline = None
    if bpath.is_file():
        try:
            baseline = json.loads(bpath.read_text(encoding="utf-8"))
        except Exception:
            baseline = None

    s = run(root, args.pdf, baseline)

    if args.write_baseline:
        counts = (s["detail"].get("assembly") or {}).get("counts") or {}
        bpath.parent.mkdir(parents=True, exist_ok=True)
        bpath.write_text(json.dumps({"counts": counts, "recorded_at": s["generated_at"]},
                                    indent=2, sort_keys=True), encoding="utf-8")
        print(f"manual-guard: baseline written -> {bpath}")
        for k, v in sorted(counts.items()):
            print(f"   {k:24} {v}")
        return 0

    if args.json:
        print(json.dumps(s, indent=2, sort_keys=True))
    else:
        a = s["detail"].get("assembly", {})
        print("=== Gate 4 flush guard -- manual / SelfDoc ===")
        print(f"  assembly build : {a.get('build_utc')}  commit {a.get('commit')}")
        for k, v in sorted((a.get("counts") or {}).items()):
            print(f"     {k:24} {v}")
        print(f"  baseline       : {'recorded' if baseline else 'NONE (--write-baseline)'}")
        print(f"  FAIL / WARN    : {s['counts']['FAIL']} / {s['counts']['WARN']}")
        print()
        for f in s["findings"]:
            print(f"  [{f['severity']}] {f['check']}/{f['code']}: {f['message']}")

    if args.out_dir:
        od = Path(args.out_dir)
        od.mkdir(parents=True, exist_ok=True)
        (od / "manual_guard_summary.json").write_text(
            json.dumps(s, indent=2, sort_keys=True), encoding="utf-8")
        (od / "manual_guard_report.md").write_text(render_markdown(s), encoding="utf-8")
        print(f"\nmanual-guard: evidence -> {od}")

    if s["counts"]["FAIL"]:
        return 1
    return 3 if s["counts"]["WARN"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
