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
  G. COUNT_KINDS    Every identity count beside the discriminator that splits it:
                    COMMANDS.dbf holds function-bridge entries, SYSFUNC holds
                    alias rows, @dottalk.file is not @dottalk.usage. Emits NO
                    findings -- it reports, so the naive number never appears
                    alone. Added after three counts went wrong the same way in
                    one session (2026-08-25).
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
#
# NOT ALL FOUR LANES ARE THE SAME KIND OF THING. Settled 2026-07-27, member.derald.
#
# SYSCMD / SYSARGS / SYSFUNC are metacollect-generated catalogs. Their CSV is
# regenerated from source (--syscmd-import-out / --sysargs-import-out /
# --sysfunc-import-out) and then imported. For those, "table rows == csv rows"
# is the right question and EMPTY_TABLE means genuinely unseeded.
#
# SYSTEM_MESSAGES is NOT metacollect-generated. It is the messaging lane's own
# table, populated and maintained by MSGMGR SEED PRIORITY{A,B,C} APPLY, and it
# lives under data/messaging rather than data/metadata. It is listed here so the
# guard watches the table that is actually authoritative -- but note metacollect
# has no --sysmsg-import-out, and that absence is deliberate, not an oversight.
#
# SYSMSG (data/metadata/SYSMSG.dbf) IS RETIRED -- deliberately not listed.
#   Measured 2026-07-27: SYSTEM_MESSAGES held 1006 records; SYSMSG held 0; and
#   SYSMSG_IMPORT_v1.csv held the SAME 1006 messages -- SYMBOL overlap 1006/1006,
#   zero on either side only. Both cite src/help/helpdata_messages.cpp. SYSMSG was
#   an empty parallel schema (17 fields, CSV 23 cols) for data that was already
#   seeded, indexed and maintained elsewhere.
#
#   Seeding it would have produced a second copy under a third schema with no
#   generator, no maintenance command and no sync rule. The guard reported
#   "EMPTY_TABLE: lane is unseeded" only because this map assumed all four lanes
#   were peers. A guard cannot distinguish "not yet done" from "should never be
#   done" -- that distinction has to be encoded here.
LANES = {
    "SYSCMD":  ("dottalkpp/data/metadata/SYSCMD.dbf",
                "dottalkpp/data/scripts/metadata/SYSCMD_IMPORT_v1.csv"),
    "SYSARGS": ("dottalkpp/data/metadata/SYSARGS.dbf",
                "dottalkpp/data/scripts/metadata/SYSARGS_IMPORT_v1.csv"),
    "SYSFUNC": ("dottalkpp/data/metadata/SYSFUNC.dbf",
                "dottalkpp/data/scripts/metadata/SYSFUNC_IMPORT_v1.csv"),
    "SYSTEM_MESSAGES": ("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf",
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
def tracked_paths(root: Path) -> set:
    """Everything git knows about, as repo-relative posix strings.

    Used to check THIS GUARD'S OWN INPUTS. See check_csv_vs_table.
    """
    try:
        out = subprocess.check_output(
            ["git", "--no-optional-locks", "-C", str(root), "ls-files"], text=True)
        return set(out.splitlines())
    except Exception:
        return set()


def check_csv_vs_table(root: Path):
    """A. The stale-snapshot trap. A number is only canonical if its input is.

    UNTRACKED_INPUT added 2026-07-26 -- this guard was not applying its own rule
    to itself.

    Discovered at the close of run COWORK-20260726-001: every lane CSV this
    check reads was being compared against a canonical table WITHOUT verifying
    the CSV exists in the repository. Measured at the time:

        SYSCMD_IMPORT_v1.csv   untracked until 32747e423
        SYSCMD_IMPORT_v2.csv   untracked until 492ac73f0
        SYSMSG_IMPORT_v1.csv   untracked, 1,006 rows

    So the guard was reporting agreement or drift between a canonical table and
    a file that no clone has. On another machine the same run means something
    different, or nothing.

    That is precisely the AIF-062 failure -- evidence invisible outside one
    working tree -- for which the registry validator (proofs must cite COMMITTED
    artifacts) was built. It was never pointed at this guard's own inputs.

    Severity is WARN, not FAIL, because an untracked CSV is a real state during
    seeding work; the point is that it can never again be silent. A guard that
    reads untracked evidence can pass on one machine and mean nothing on
    another, which is the exact failure it exists to prevent.
    """
    findings, detail = [], {}
    tracked = tracked_paths(root)
    for lane, (dbf_rel, csv_rel) in LANES.items():
        dbf, csvp = root / dbf_rel, root / csv_rel

        if tracked and csvp.is_file() and csv_rel not in tracked:
            findings.append({"check": "CSV_VS_TABLE", "lane": lane,
                             "code": "UNTRACKED_INPUT", "severity": "WARN",
                             "message": f"{lane}: {csv_rel} is NOT tracked by git -- this "
                                        f"guard is comparing a canonical table against a "
                                        f"file no clone has. Commit it or stop citing it."})

        rec = dbf_header(dbf)[0] if dbf.is_file() else None
        rows = len(csv_rows(csvp)) if csvp.is_file() else None
        detail[lane] = {"table_rows": rec, "csv_rows": rows,
                        "csv_tracked": (csv_rel in tracked) if tracked else None}
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
            # CAPTURE THE WHOLE NAME, NOT THE FIRST TOKEN.
            #
            # This was `(\S+)`, which read `command: SET CASE` as `SET`. Every
            # multi-word command identity collapsed to its first word, so the
            # eleven files correctly declaring SET CASE, SET CDX, SET CNX,
            # SET FILTER, SET INDEX, SET LMDB, SET NEAR, SET ORDER, SET PATH,
            # SET RELATION and SET UNIQUE were folded together with cmd_set.cpp
            # and reported as "command SET declared in 12 places".
            #
            # That single false finding was the largest item in CONTRACT_QA and
            # was cited repeatedly, by this session included, as evidence of a
            # documentation problem. The contracts were right. The guard was
            # reading them one word at a time.
            #
            # Note the multi-word identity is exactly what AIF-067 formalised as
            # QUAL_NAME (parent + sub). A checker for contract identity must be
            # able to express the identities the contract system supports.
            m = (re.search(r"(?m)^\s*(?://)?\s*command:\s*(.+?)\s*$", blk)
                 or re.search(r"(?m)^\s*(?://)?\s*surface:\s*(.+?)\s*$", blk))
            nm = re.sub(r"\s+", " ", m.group(1)).strip().upper() if m else ""
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


def command_resolution_paths(root: Path):
    """Every way a name can become reachable at the prompt.

    Adjudicating 43 dotref entries on 2026-07-27 found FIVE registration paths.
    A check that knows only registry().add() reports the other four as
    "uncovered", which is how 14 legitimately-reachable names were nearly
    written off -- and how two genuinely broken ones nearly hid among them.

      core       registry().add("NAME", ...)                 -- shell_commands.cpp
      shortcut   { "ALIAS", "TARGET" } pairs                 -- shortcut_resolver.hpp
      extension  dli::register_extension_command("NAME", ..) -- src/ext/cmd/
      alias      add(ALIAS, TARGET, "alias", ...)            -- reference_collection.cpp
      function   fn_NAME / BuiltinFnSpec                     -- NOT a command at all

    The last one matters: STU_REPEAT and STU_UPPER are student programming
    STUBS registered as FUNCTIONS (fn_STU_*). They will never have a SYSCMD row
    and should never be counted against command coverage.
    """
    src = subprocess.run(["git", "--no-optional-locks", "-C", str(root), "ls-files",
                          "src", "include"], capture_output=True, text=True).stdout.split()
    blob = []
    for rel in src:
        if rel.endswith((".cpp", ".hpp", ".h")):
            try:
                blob.append((root / rel).read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass
    text = "\n".join(blob)
    return {
        "core":      {m.upper() for m in re.findall(r'registry\(\)\.add\(\s*"([^"]+)"', text)},
        "shortcut":  {m.upper() for m in re.findall(r'\{\s*"([A-Z0-9_ ]+)"\s*,\s*"[A-Z0-9_ ]+"\s*\}', text)},
        "extension": {m.upper() for m in re.findall(r'register_extension_command\(\s*"([^"]+)"', text)},
        "alias":     {m.upper() for m in re.findall(r'add\(\s*"([A-Z0-9_ ]+)"\s*,\s*"[A-Z0-9_ ]+"\s*,\s*"alias"', text)},
        "function":  {m.upper() for m in re.findall(r'\bfn_([A-Z][A-Z0-9_]*)\b', text)},
    }


def fold_command_name(name: str) -> str:
    """Fold a command name to a spelling-insensitive key.

    dotref.hpp and SYSCMD spell the same command two ways, because they are
    generated from different things: dotref carries HANDLER-SYMBOL spellings
    (SETCASE, APPEND BLANK, ERROR CLEAR) while SYSCMD carries CANONICAL ones
    (SET CASE, APPEND_BLANK, ERROR_CLEAR). Neither is wrong; they are different
    conventions for one identity.

    Measured 2026-07-27: of 55 dotref entries reported UNCOVERED, TWELVE were
    pure spelling -- SETCASE/SET CASE, SETCDX/SET CDX, SETCNX, SETFILTER,
    SETINDEX, SETNEAR, SETORDER, SET PATH/SETPATH, APPEND BLANK/APPEND_BLANK,
    ERROR CLEAR/STATUS/TEST. Reporting those as missing coverage invites the
    obvious "fix": adding rows that already exist under another spelling, which
    would create duplicates in the canonical table.

    Fold rule: uppercase, then drop spaces and underscores. Deliberately narrow.
    It does NOT strip punctuation or attempt stemming -- SIMPLEBROWSER vs
    SIMPLEBROWSE is a real difference in identity and must stay visible.
    """
    return re.sub(r"[ _]", "", name.strip().upper())


def check_dotref_coverage(root: Path):
    """E. Measured against the LIVE table -- never a CSV.

    Coverage is measured on FOLDED names (2026-07-27, AIF-066 follow-on).

    "Coverage 78.4%" was conflating aliasing with absence, and pointed at the
    wrong remedy for a fifth of its own findings. dotref.hpp INTENTIONALLY
    registers both spellings of a command so both parse at the prompt -- its own
    text says so:

        {"SET CASE", "SET CASE ON|OFF",
         "Control case-sensitivity using the spaced compatibility form.", true},
        {"SETCASE",  "SETCASE ON|OFF",
         "Control case-sensitivity / collation mode for comparisons.", true},

    SYSCMD, being a canonical catalog, holds exactly ONE of each pair. So the
    alias form was scored as "no live SYSCMD row" -- true literally, misleading
    completely, and it invited the fix of adding a duplicate canonical row.

    Twelve such pairs exist. Eleven resolve; the twelfth (SET LMDB / SETLMDB)
    resolves to nothing and is a genuine gap, already counted as uncovered.

    NOTE, worth a separate decision: SYSCMD is not consistent about WHICH form
    it treats as canonical -- spaced for SET CASE, underscored for ERROR_CLEAR.
    Folding makes coverage correct either way, but the inconsistency is real and
    will surface anywhere the canonical name is used as a key.
    """
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
    live_folded = {fold_command_name(v) for v in live}

    exact = [e for e in entries if e in live]
    rest = [e for e in entries if e not in live]
    spelling = [e for e in rest if fold_command_name(e) in live_folded]
    uncovered = [e for e in rest if fold_command_name(e) not in live_folded]

    # Guard the fold: if two different dotref names collapse to one key, the
    # rule is over-folding and would hide a real distinction.
    folds = {}
    for e in entries:
        folds.setdefault(fold_command_name(e), []).append(e)
    collisions = {k: v for k, v in folds.items() if len(v) > 1}

    matched = len(exact) + len(spelling)
    pct_raw = round(100.0 * len(exact) / len(entries), 1) if entries else 0.0
    pct_norm = round(100.0 * matched / len(entries), 1) if entries else 0.0

    detail = {"dotref_entries": len(entries), "live_syscmd_rows": len(live),
              "exact_match": len(exact), "spelling_variant": len(spelling),
              "uncovered": len(uncovered), "fold_collisions": len(collisions),
              "coverage_pct_raw": pct_raw, "coverage_pct_normalized": pct_norm,
              "spelling_variants": sorted(spelling),
              "uncovered_names": sorted(uncovered)}
    # An alias pair whose members BOTH fold onto a live canonical row is the
    # system working, not a finding. Only a pair that resolves to nothing is
    # interesting, and those members are already in `uncovered`.
    unresolved_pairs = {k: v for k, v in collisions.items() if k not in live_folded}
    detail["alias_pairs_resolved"] = len(collisions) - len(unresolved_pairs)
    detail["alias_pairs_unresolved"] = sorted("/".join(v) for v in unresolved_pairs.values())

    # Split `uncovered` by HOW the name is reachable. Only a name registered as
    # a command and missing a SYSCMD row is a catalog gap; a shortcut, an alias,
    # an extension command or a function is reachable by design and will never
    # have its own canonical row.
    paths = command_resolution_paths(root)
    folded = {k: {fold_command_name(n) for n in v} for k, v in paths.items()}
    gaps, elsewhere, subcmds, unresolvable = [], {}, [], []
    for e in uncovered:
        f = fold_command_name(e)
        if f in folded["core"]:
            gaps.append(e)
            continue
        for kind in ("shortcut", "alias", "extension", "function"):
            if f in folded[kind]:
                elsewhere.setdefault(kind, []).append(e)
                break
        else:
            # A multi-word name whose FIRST token is a registered command is a
            # SUBCOMMAND: typeable (the parent's dispatcher parses it) but never
            # independently registered, so no registry lookup and no catalog row.
            # This is the same structural gap that left DOT|SET LANGUAGE and
            # DOT|SET LOCALE as orphaned HELP locale topics (AIF-066) --
            # DotTalk++ has no convention for declaring a subcommand identity.
            head = e.split()[0].upper() if " " in e else ""
            if head and fold_command_name(head) in folded["core"]:
                subcmds.append(e)
            else:
                unresolvable.append(e)
    detail["registered_no_syscmd_row"] = sorted(gaps)
    detail["reachable_elsewhere"] = {k: sorted(v) for k, v in elsewhere.items()}
    detail["subcommand_only"] = sorted(subcmds)
    detail["unresolvable"] = sorted(unresolvable)

    out = []
    if gaps:
        out.append({"check": "DOTREF_COV", "code": "UNCOVERED_ENTRIES", "severity": "WARN",
                    "message": f"{len(gaps)} command(s) are registered via registry().add() but "
                               f"have no live SYSCMD row -- a real catalog gap "
                               f"(coverage {pct_norm}% normalized, {pct_raw}% raw; "
                               f"{len(spelling)} alias spelling(s) folded, "
                               f"{sum(len(v) for v in elsewhere.values())} reachable via "
                               f"shortcut/alias/extension/function)"})
    if subcmds:
        out.append({"check": "DOTREF_COV", "code": "SUBCOMMAND_ONLY", "severity": "WARN",
                    "message": f"{len(subcmds)} dotref entr(ies) are subcommands of a registered "
                               f"parent -- typeable, but never independently registered, so no "
                               f"contract, no SYSCMD row and no HELP topic. Same gap that orphaned "
                               f"the SET LANGUAGE / SET LOCALE locale topics: "
                               f"{', '.join(sorted(subcmds))}"})
    if unresolvable:
        out.append({"check": "DOTREF_COV", "code": "UNRESOLVABLE_ENTRY", "severity": "WARN",
                    "message": f"{len(unresolvable)} dotref entr(ies) resolve through NO path and "
                               f"are not a subcommand of any registered parent -- dotref documents "
                               f"a command that CANNOT be typed: "
                               f"{', '.join(sorted(unresolvable))}"})
    return out, detail


def check_subcmd_coverage(root: Path):
    """G. AIF-067. THREE representations of the SET subcommand surface, compared.

    Until this check existed, the surface was described in three places that
    never met:

        1. the LADDER   -- `if (opt == "X")` arms in src/cli/cmd_set.cpp,
                           the only one that actually dispatches anything
        2. the USAGE TEXT -- MessageId::SetUsageText, a hand-typed ~40-line
                           string literal in src/help/helpdata_messages.cpp
        3. the TABLE    -- dottalkpp/data/metadata/SYSSUBCMD.dbf

    Measured when this check was written: the ladder had 33 option tokens, the
    usage text listed 30. ERRORSTOP and INDEXTXN dispatch correctly and are
    undiscoverable from the product itself. The table held 12 scratch rows.

    ACCEPTANCE TEST FOR THIS CHECK (AIF-067 sec 7): run against the tree as it
    stood on 2026-07-27 it MUST report ERRORSTOP and INDEXTXN under
    USAGE_TEXT_DRIFT. A check that passes on the broken tree has proved nothing,
    so do not "fix" that finding by relaxing the check -- it clears when
    SET USAGE is rendered from SYSSUBCMD (M4) and not before.

    Note SETCASE and SETNEAR are deliberately NOT reported: they are alias
    spellings of CASE and NEAR, both of which the usage text does list. Folding
    them is the same normalization DOTREF_COV learned to apply.
    """
    findings, detail = [], {}

    ladder_src = root / "src" / "cli" / "cmd_set.cpp"
    msg_src = root / "src" / "help" / "helpdata_messages.cpp"
    if not ladder_src.is_file():
        return findings, {"skipped": "cmd_set.cpp not found"}

    text = ladder_src.read_text(encoding="utf-8", errors="replace")

    # 1. ladder arms
    ladder = {m.upper() for m in re.findall(r'opt\s*==\s*"([A-Z0-9_]+)"', text)}
    # Do NOT strip USAGE/HELP here. An earlier draft did, on the reasoning that
    # they are "meta" rather than real options -- which then reported the
    # `sub: USAGE` contract as a CONTRACT_ORPHAN describing something untypeable.
    # It is typeable: `if (opt == "USAGE" || opt == "HELP" || opt == "?")` is an
    # arm like any other. The exclusion invented the very defect it claimed to
    # find. HELP and ? are carried as that contract's aliases and fold normally.

    # 2. contracts (parent SET), plus their alias spellings
    contracts, aliases = set(), set()
    for block in re.findall(r"// @dottalk\.subusage v1\n(?:\s*//[^\n]*\n)+", text):
        sub = re.search(r"//\s*sub:\s*(\S+)", block)
        if not sub:
            continue
        contracts.add(sub.group(1).upper())
        al = re.search(r"//\s*aliases:\s*(.+)", block)
        if al:
            aliases |= {a.strip().upper() for a in al.group(1).split(";") if a.strip()}
    contracts_all = contracts | aliases

    # 3. live table
    table = set()
    dbf = root / "dottalkpp" / "data" / "metadata" / "SYSSUBCMD.dbf"
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import dbfread  # sibling module; refuses on a layout it cannot reconcile
        for r in dbfread.read(dbf).rows:
            if r.get("PARENT", "").upper() == "SET" and r.get("SUB_NAME"):
                table.add(r["SUB_NAME"].upper())
    except Exception as e:                                  # noqa: BLE001
        detail["table_error"] = str(e)

    # 4. the SetUsageText copies.
    #
    # This was ONE hand-typed single-line literal; it is now TWO generated
    # regions of #if-guarded adjacent string literals (AIF-067 M4). The old
    # parser matched `\n  SET X` inside one long line and would return an EMPTY
    # set against the new shape -- making every option look undiscoverable and
    # turning this check into noise nobody trusts.
    #
    # Both regions are parsed and INTERSECTED: an option must appear in the
    # descriptor default AND the en-US locale row to count as listed. The
    # descriptor copy is the one that was found stale (it still lacked
    # ERRORSTOP, INDEXTXN and DEVDIAG after the locale row was generated), so
    # accepting either alone would hide precisely that failure.
    listed = set()
    if msg_src.is_file():
        mt = msg_src.read_text(encoding="utf-8", errors="replace")
        regions = []
        for begin, end in (("@generated:set-usage-text BEGIN",
                            "@generated:set-usage-text END"),
                           ("@generated:set-usage-descriptor BEGIN",
                            "@generated:set-usage-descriptor END")):
            s = mt.find(begin)
            e = mt.find(end, s + 1) if s >= 0 else -1
            if s >= 0 and e > s:
                regions.append({m.upper() for m in
                                re.findall(r'"\s*SET ([A-Z0-9_]+)', mt[s:e])})
        if regions:
            listed = set.intersection(*regions)
        else:
            # pre-migration single-line form, kept so this check still means
            # something on an older tree instead of reporting a false gap
            for line in mt.splitlines():
                if 'SetUsageText, "en-US"' in line:
                    listed = {m.upper() for m in
                              re.findall(r"\\n\s+SET ([A-Z0-9_]+)", line)}
                    break
        detail["usage_text_regions"] = len(regions)
        detail["usage_text_listed"] = len(listed)

    uncontracted = sorted(ladder - contracts_all)
    orphaned = sorted(contracts - ladder)
    undiscoverable = sorted(ladder - listed - contracts_all.intersection(aliases) - aliases)
    table_missing = sorted(contracts - table) if table or "table_error" not in detail else []

    if uncontracted:
        findings.append({"check": "SUBCMD_COV", "code": "LADDER_UNCONTRACTED",
                         "severity": "WARN",
                         "message": f"{len(uncontracted)} SET ladder arm(s) dispatch with no "
                                    f"@dottalk.subusage contract, so they have no identity for "
                                    f"SYSSUBCMD or HELP: " + ", ".join(uncontracted)})
    if orphaned:
        findings.append({"check": "SUBCMD_COV", "code": "CONTRACT_ORPHAN",
                         "severity": "WARN",
                         "message": f"{len(orphaned)} @dottalk.subusage contract(s) describe a "
                                    f"subcommand the ladder does not dispatch -- the contract "
                                    f"documents something untypeable: " + ", ".join(orphaned)})
    if undiscoverable:
        findings.append({"check": "SUBCMD_COV", "code": "USAGE_TEXT_DRIFT",
                         "severity": "WARN",
                         "message": f"{len(undiscoverable)} SET option(s) dispatch but are absent "
                                    f"from MessageId::SetUsageText, so they work and cannot be "
                                    f"discovered from the product: " + ", ".join(undiscoverable)
                                    + ". NOTE the localization cost is PROSPECTIVE, not incurred: "
                                      "SetUsageText currently exists in en-US only (de/es/fr/it "
                                      "carry 290 messages each and this is not among them), so the "
                                      "gap exists once. It multiplies the first time this string "
                                      "is translated, which is an argument for generating it "
                                      "BEFORE the locale spine reaches it, not after."})
    if table_missing:
        findings.append({"check": "SUBCMD_COV", "code": "TABLE_DRIFT",
                         "severity": "WARN",
                         "message": f"{len(table_missing)} contracted subcommand(s) have no live "
                                    f"SYSSUBCMD row -- the table has not been reseeded from the "
                                    f"contracts (tools/fullstack_docs/generate_syssubcmd.py): "
                                    + ", ".join(table_missing[:12])})

    detail.update({"ladder_arms": len(ladder), "contracts": len(contracts),
                   "aliases": len(aliases), "usage_text_listed": len(listed),
                   "table_rows_set": len(table),
                   "uncontracted": uncontracted, "orphaned": orphaned,
                   "undiscoverable": undiscoverable,
                   "table_missing": table_missing[:20]})
    return findings, detail


def check_registration_policy(root: Path):
    """H. src/cli/shell_commands.cpp states a policy that nothing enforces.

    Its header says, verbatim:

        "Built-in CLI commands are registered here. Do not self-register built-in
         commands elsewhere; otherwise startup order, duplicate names,
         help/reflection, and command-audit tooling become harder to reason about."

    Measured when this check was written: ten other translation units call
    registry().add() for eleven names, NINE of which shell_commands.cpp also
    registers -- BBS, CASE, CODASYL, DELETE, ERASE, EXPORTFUNCTIONS, NET,
    RECALL, SQLHELP.

    WHY THIS IS NOT MERELY UNTIDY
        CommandRegistry::add_with_origin does `map_[key] = std::move(h)`
        unconditionally for Core origin; the protection check only rejects
        Extension and Function. So Core-vs-Core is a SILENT overwrite with no
        diagnostic, and the duplicates are NOT equivalent:

            cmd_delete.cpp   registry().add("DELETE", &cmd_DELETE)
            shell_commands   registry().add("DELETE", ... cmd_DELETE(A,S);
                                            relations_api::refresh_if_enabled(); )

        One version performs relation maintenance after a mutation and the other
        does not. Self-registration runs at static init; register_shell_commands
        is called later from shell.cpp:535, so the wrapped version wins TODAY --
        by construction order, not by rule. Nothing pins that order, and
        cmd_foxpro.cpp:568 calls register_shell_commands a second time, so
        registration is not even once-only.

    SEVERITY IS WARN, DELIBERATELY
        This is a development repository whose working tree is expected to run
        slightly ahead of its documentation. The point is not to block; it is
        that a name silently bound twice, to handlers that differ in whether
        they maintain relations, can never again be invisible.

    Extension registrations (register_extension_command) are EXCLUDED: the same
    header explicitly permits custom/student commands to self-register.
    """
    findings, detail = [], {}
    hub_rel = "src/cli/shell_commands.cpp"
    hub = root / hub_rel
    if not hub.is_file():
        return findings, {"skipped": "shell_commands.cpp not found"}

    add_re = re.compile(r'registry\(\)\.add\(\s*"([^"]+)"')
    sites: dict[str, list[tuple[str, int, str]]] = {}

    for rel in tracked_sources(root):
        if not rel.endswith(".cpp"):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "registry().add(" not in text:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            m = add_re.search(line)
            if m:
                sites.setdefault(m.group(1).upper(), []).append((rel, n, line.strip()))

    dup_in_hub, split, asymmetric = [], [], []
    for name, occ in sorted(sites.items()):
        in_hub = [o for o in occ if o[0].replace("\\", "/") == hub_rel]
        elsewhere = [o for o in occ if o[0].replace("\\", "/") != hub_rel]
        if len(in_hub) > 1:
            dup_in_hub.append(f"{name} ({', '.join(str(o[1]) for o in in_hub)})")
        if in_hub and elsewhere:
            other = elsewhere[0]
            split.append(f"{name} (also {other[0]}:{other[1]})")
            hub_wrapped = any("refresh_if_enabled" in o[2] for o in in_hub)
            oth_wrapped = any("refresh_if_enabled" in o[2] for o in elsewhere)
            if hub_wrapped != oth_wrapped:
                asymmetric.append(
                    f"{name}: {'hub' if hub_wrapped else other[0]} refreshes relations, "
                    f"{other[0] if hub_wrapped else 'hub'} does not")

    if asymmetric:
        findings.append({"check": "REG_POLICY", "code": "WRAPPER_ASYMMETRY",
                         "severity": "WARN",
                         "message": f"{len(asymmetric)} command(s) are registered TWICE with "
                                    f"handlers that DIFFER in whether they call "
                                    f"relations_api::refresh_if_enabled(). Core-vs-Core "
                                    f"registration is a silent overwrite, so which one is live "
                                    f"depends on static-init vs shell-bootstrap ORDER, not on "
                                    f"any rule: " + "; ".join(asymmetric)})
    if split:
        findings.append({"check": "REG_POLICY", "code": "SPLIT_REGISTRATION",
                         "severity": "WARN",
                         "message": f"{len(split)} built-in command(s) are registered both in "
                                    f"{hub_rel} and in their own translation unit, against that "
                                    f"file's own stated policy ('Do not self-register built-in "
                                    f"commands elsewhere'). Last writer wins with no diagnostic: "
                                    + ", ".join(split)})
    if dup_in_hub:
        findings.append({"check": "REG_POLICY", "code": "DUPLICATE_IN_HUB",
                         "severity": "WARN",
                         "message": f"{len(dup_in_hub)} command(s) are registered more than once "
                                    f"within {hub_rel} itself -- the duplicate the file's own "
                                    f"policy warns about, in the file that states it: "
                                    + ", ".join(dup_in_hub)})

    detail.update({"distinct_names": len(sites),
                   "hub_registrations": sum(
                       1 for occ in sites.values()
                       for o in occ if o[0].replace("\\", "/") == hub_rel),
                   "self_registering_files": sorted(
                       {o[0] for occ in sites.values() for o in occ
                        if o[0].replace("\\", "/") != hub_rel}),
                   "split": split, "duplicate_in_hub": dup_in_hub,
                   "wrapper_asymmetry": asymmetric})
    return findings, detail


def check_dead_registration(root: Path):
    """J. Registered names the dispatcher can never produce.

    shell_dispatch (src/cli/shell_api.cpp) keys the registry on the FIRST TOKEN
    of the line:

        std::istringstream tok(line); std::string cmd; tok >> cmd;
        registry().run(area, textio::up(cmd), tok);

    Two consequences nobody was checking:

    1. MULTI-WORD KEYS ARE UNREACHABLE. A key containing a space cannot be the
       first token, so `registry().add("SET RELATION", ...)` never fires.
       Eight such keys exist. They look like working registrations, they appear
       in command inventories, and they are dead.

       This is not cosmetic. `"SET RELATION"` is bound to cmd_SET_RELATIONS --
       the house-SQL handler -- while the SET ladder routes the singular
       spelling to cmd_SET_RELATION, the VFP-compatibility front-end. The dead
       entry, if ever revived, would INVERT the intended layering.

    2. NAMES REWRITTEN BEFORE DISPATCH ARE UNREACHABLE. preprocess_for_dispatch
       (src/cli/shell_api_extras.cpp) rewrites the line before the registry is
       consulted -- today `SET RELATIONS ...` and `RELATIONS ...` both become
       `REL ...`. So the registration of "RELATIONS" is dead too, and so is the
       `opt == "RELATIONS"` arm inside cmd_SET.

    The rewrite rules are PARSED from that source rather than hardcoded, so a
    new rule cannot silently invalidate this check the way it invalidated the
    registrations.

    WARN: a dead registration harms nothing at runtime. It misleads every
    reader and every inventory that treats the registry as the command surface,
    which this run has been doing all day.
    """
    findings, detail = [], {}
    hub = root / "src" / "cli" / "shell_commands.cpp"
    pre = root / "src" / "cli" / "shell_api_extras.cpp"
    if not hub.is_file():
        return findings, {"skipped": "shell_commands.cpp not found"}

    names: dict[str, list[str]] = {}
    for rel in tracked_sources(root):
        if not rel.endswith(".cpp"):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r'registry\(\)\.add\(\s*"([^"]+)"', text):
            names.setdefault(m.group(1).upper(), []).append(rel)

    rewritten: set[str] = set()
    if pre.is_file():
        pt = pre.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'starts_with_tokens_ci\([^,]+,\s*"([^"]+)"\s*,\s*"([^"]+)"', pt):
            rewritten.add(f"{m.group(1)} {m.group(2)}".upper())
        for m in re.finditer(r'starts_with_token_ci\([^,]+,\s*"([^"]+)"', pt):
            rewritten.add(m.group(1).upper())

    multiword = sorted(n for n in names if " " in n)
    shadowed = sorted(n for n in names if n in rewritten and " " not in n)

    if multiword:
        findings.append({"check": "DEAD_REG", "code": "MULTIWORD_KEY",
                         "severity": "WARN",
                         "message": f"{len(multiword)} registry key(s) contain a space and can "
                                    f"never be dispatched -- shell_dispatch keys on the FIRST "
                                    f"TOKEN only. They read as working registrations and are "
                                    f"dead: " + ", ".join(multiword)})
    if shadowed:
        findings.append({"check": "DEAD_REG", "code": "REWRITTEN_BEFORE_DISPATCH",
                         "severity": "WARN",
                         "message": f"{len(shadowed)} registry key(s) are rewritten by "
                                    f"preprocess_for_dispatch before the registry is consulted, "
                                    f"so the registration never fires: " + ", ".join(shadowed)
                                    + f" (rules parsed from shell_api_extras.cpp: "
                                    + ", ".join(sorted(rewritten)) + ")"})

    detail.update({"registered_names": len(names), "multiword": multiword,
                   "rewrite_rules": sorted(rewritten), "shadowed": shadowed})
    return findings, detail


CANONICAL_TABLE_DIRS = ("metadata", "messaging", "help", "locale", "comments")


def check_table_parse(root: Path):
    """I. Every canonical table must parse end to end.

    WHY THIS EXISTS
        CSV_VS_TABLE reads only the DBF header for a row count. A table can be
        structurally unreadable by the documentation toolchain and still pass
        every check in this file -- which is not hypothetical:

            SYSFUNC.dbf     unreadable for the life of tools/fullstack_docs
                            (a phantom descriptor named 0x45 = 'E' was admitted
                            as a 10-byte field, shifting all 21 real fields)
            MEMO_LINES.dbf  unreadable (LINECONT is C(1024); the classic width
                            byte clamps at 255, leaving 769 bytes of every
                            record undescribed)

        Both were found by hand, on the same afternoon, only because someone
        asked what flavour of DBF these were. Nothing was watching.

    WHAT A FAILURE MEANS -- TWO POSSIBILITIES, DELIBERATELY NOT CONFLATED
        A table this check cannot read is NOT necessarily corrupt. The engine
        reads SYSFUNC and MEMO_LINES perfectly well; it was the PYTHON READER
        that could not express an X64 construct. So a finding here means "the
        documentation toolchain cannot audit this table", which is either a
        data defect or a reader gap, and the message says so rather than
        asserting the alarming one.

        WARN, not FAIL, for the same reason plus the house rule: this is a dev
        repository whose tree runs ahead of its documentation.
    """
    findings, detail = [], {}
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import dbfread
    except Exception as e:                                   # noqa: BLE001
        return findings, {"skipped": f"dbfread unavailable: {e}"}

    checked, failures = 0, []
    for sub in CANONICAL_TABLE_DIRS:
        d = root / "dottalkpp" / "data" / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.dbf")):
            checked += 1
            try:
                t = dbfread.read(f)
                if t.live != t.header_rows - t.deleted:
                    failures.append(f"{sub}/{f.name}: row accounting mismatch")
            except Exception as e:                           # noqa: BLE001
                msg = str(e).split(": ", 1)[-1].split(" Refusing")[0].strip()
                failures.append(f"{sub}/{f.name}: {msg[:120]}")

    if failures:
        findings.append({"check": "TABLE_PARSE", "code": "UNPARSEABLE",
                         "severity": "WARN",
                         "message": f"{len(failures)} of {checked} canonical table(s) cannot be "
                                    f"read end to end by the documentation toolchain. This is "
                                    f"EITHER a data defect OR a gap in tools/fullstack_docs/"
                                    f"dbfread.py -- the engine may read a table this cannot. "
                                    f"Determine which before acting: "
                                    + "; ".join(failures[:6])})

    detail.update({"checked": checked, "failures": failures,
                   "dirs": list(CANONICAL_TABLE_DIRS)})
    return findings, detail


def check_count_kinds(root: Path):
    """G. COUNT_KINDS -- every identity count, beside the discriminator that splits it.

    WHY THIS EXISTS. On 2026-08-25 three counts went wrong in one session, all
    the same way: a number taken from an authority that holds more than one KIND
    of thing, with no discriminator applied.

        578 "contract-bearing .cpp"   was @dottalk.file, the FILE HEADER on 578
                                      files. Usage contracts: 231.
        320 "commands"                is 288 commands + 32 function-bridge
                                      entries that are really SYSFUNC functions.
         75 "functions"               is 73 names HELP FUNCTIONS prints, plus
                                      STRCAT and TRIM -- alias names carried in
                                      a FunctionDoc alias field
                                      (STRCAT->CONCAT, TRIM->RTRIM).

    None was a guess. Each was a correct sum over the wrong set.

    AND THE FIRST RUN OF THIS CHECK CORRECTED ITS OWN AUTHOR. The session that
    wrote it had concluded "SRC_AUTH separates canonical functions from alias
    rows" and committed that. SRC_AUTH splits SYSFUNC 68/7, not 73/2: the seven
    builtin_registry rows are PADC PADL PADR PROPER STRCAT STUFF TRIM, and FIVE
    OF THEM ARE PRINTED by HELP FUNCTIONS. SRC_AUTH is harvest provenance, not
    alias status. The real alias discriminator lives in a FunctionDoc alias
    field in function_catalog.cpp and is in NO table at all -- which is exactly
    why a count taken from a table cannot be trusted to know what it holds.

    WHY A CHECK AND NOT A DOCUMENT. An errata list records facts true when
    written -- COMMANDS.dbf moved twice in the week those numbers were taken, so
    "320 is really 288" is wrong the day a command lands and nothing says so. A
    heads-up has to be read at the right moment by someone who does not yet know
    they need it; that session read five governing documents and still got three
    counts wrong. THE REGISTERS EXISTED; CONSULTING THEM IS THE STEP THAT FAILED.

    This emits NO findings. It is not a defect detector -- it reports, so that
    the naive number never appears on a page alone and nobody has to re-derive
    the split. That is also why it cannot move the baseline ratchet.

    READS THROUGH dbfread, NOT THE LOCAL dbf_column. Two of these tables are
    x64, and this module's own dbf_fields() scans for the 0x0D descriptor
    terminator from offset 32 -- inside the x64 phantom block -- which is
    AIF-127. It is not firing today (SYSCMD's row count is 212, low byte 0xd4)
    and both readers agree exactly on SYSCMD as of this writing. It WOULD fire
    silently at 269 rows, 57 away. Fixing dbf_column is a separate change and is
    deliberately not made here; this check simply does not depend on it.
    """
    detail = {}

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dbfread  # noqa: E402  -- the shared x64-correct reader

    # --- functions: SRC_AUTH separates catalog entries from alias rows --------
    fn_names, fn_by_auth = set(), {}
    fnp = root / "dottalkpp/data/metadata/SYSFUNC.dbf"
    if fnp.is_file():
        try:
            t = dbfread.read(fnp)
            for r in t.rows:
                name = r.get("CAN_NAME", "").strip().upper()
                if not name:
                    continue
                fn_names.add(name)
                auth = r.get("SRC_AUTH", "").strip() or "(blank)"
                fn_by_auth[auth] = fn_by_auth.get(auth, 0) + 1
            detail["sysfunc"] = {"rows": len(t.rows), "distinct_names": len(fn_names),
                                 "by_SRC_AUTH": fn_by_auth,
                                 "note": "SRC_AUTH is HARVEST PROVENANCE, not "
                                         "alias status. builtin_registry rows "
                                         "are PADC PADL PADR PROPER STRCAT "
                                         "STUFF TRIM -- five of those seven ARE "
                                         "printed by HELP FUNCTIONS. The two "
                                         "that are not (STRCAT, TRIM) are alias "
                                         "names living in a FunctionDoc alias "
                                         "field, which is visible ONLY in "
                                         "function_catalog.cpp and in no table. "
                                         "HELP FUNCTIONS prints 73 of these 75."}
        except Exception as e:
            detail["sysfunc"] = {"error": f"{type(e).__name__}: {e}"}
    else:
        detail["sysfunc"] = {"error": "SYSFUNC.dbf not found"}

    # --- commands: a name also in SYSFUNC is a FUNCTION on the bridge ---------
    cmdp = root / "dottalkpp/data/help/COMMANDS.dbf"
    if cmdp.is_file():
        try:
            t = dbfread.read(cmdp)
            names = {r.get("COMMAND", "").strip().upper() for r in t.rows}
            names.discard("")
            bridge = sorted(n for n in names if n in fn_names)
            by_cat = {}
            for r in t.rows:
                c = r.get("CATALOG", "").strip() or "(blank)"
                by_cat[c] = by_cat.get(c, 0) + 1
            detail["commands_dbf"] = {
                "rows": len(t.rows), "distinct_names": len(names),
                "commands": len(names) - len(bridge),
                "function_bridge_entries": len(bridge),
                "function_bridge_names": bridge,
                "rows_by_CATALOG": by_cat,
                "note": "a distinct name also present in SYSFUNC is a FUNCTION "
                        "reached through the function command-line bridge, "
                        "not a command"}
        except Exception as e:
            detail["commands_dbf"] = {"error": f"{type(e).__name__}: {e}"}
    else:
        detail["commands_dbf"] = {"error": "COMMANDS.dbf not found"}

    # --- contracts: NOT recounted here, on purpose ---------------------------
    # The @dottalk.usage / @dottalk.file distinction was the third of the three
    # wrong counts, and it is tempting to add it. It is NOT added, for two
    # reasons. Check C (CONTRACT_QA) already owns the contract estate and
    # already names this failure -- "mention-only false positives that inflate
    # command counts". And counting it here means a THIRD full read of every
    # tracked source, after BANNER_CENSUS and CONTRACT_QA have each already made
    # one; this check reads three small tables and should stay cheap enough that
    # nobody is tempted to skip the audit.
    detail["dottalk_markers"] = {
        "counted_here": False,
        "owner": "check C -- CONTRACT_QA",
        "note": "@dottalk.usage is the CONTRACT. @dottalk.file is a provenance "
                "header and is NOT a contract -- counting it inflates the "
                "contract estate roughly 2.5x (231 vs 578 files, 2026-08-25). "
                "See CONTRACT_QA detail for the live contract numbers."}

    # --- help topics: one table, five catalogs --------------------------------
    tp = root / "dottalkpp/data/help/HELP_TOPIC.dbf"
    if tp.is_file():
        try:
            t = dbfread.read(tp)
            by_cat = {}
            for r in t.rows:
                c = r.get("CATALOG", "").strip() or "(blank)"
                by_cat[c] = by_cat.get(c, 0) + 1
            detail["help_topics"] = {"rows": len(t.rows), "by_CATALOG": by_cat}
        except Exception as e:
            detail["help_topics"] = {"error": f"{type(e).__name__}: {e}"}

    return [], detail


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
                     ("subcmd_coverage", lambda: check_subcmd_coverage(root)),
                     ("registration_policy", lambda: check_registration_policy(root)),
                     ("table_parse", lambda: check_table_parse(root)),
                     ("dead_registration", lambda: check_dead_registration(root)),
                     ("embedded_bom", lambda: check_embedded_bom(root, files)),
                     ("count_kinds", lambda: check_count_kinds(root))):
        f, d = fn()
        findings.extend(f)
        detail[name] = d

    findings, expected, stale = apply_expectations(findings)

    counts = {"FAIL": sum(1 for f in findings if f["severity"] == "FAIL"),
              "WARN": sum(1 for f in findings if f["severity"] == "WARN")}
    by_check = {}
    for f in findings:
        by_check[f["check"]] = by_check.get(f["check"], 0) + 1
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "root": str(root), "tracked_source_files": len(files),
            "counts": counts, "by_check": by_check,
            "detail": detail, "findings": findings,
            "expected": expected, "stale_expectations": len(stale)}


# --------------------------------------------------------------------------- #
# EXPECTED findings (AIF-067 M6)
# --------------------------------------------------------------------------- #
#
# A deliberate open finding and a neglected one look IDENTICAL in a count-based
# ratchet. Before this registry existed, the only thing distinguishing the two
# was a paragraph in a lane document -- which the next session may not read, and
# which cannot notify anyone of anything.
#
# WHAT MAKES THIS A REGISTRY AND NOT A SUPPRESSION LIST
#     Every entry MUST stop matching eventually, and when it does, its own
#     staleness is reported as a finding (STALE_EXPECTATION). Without that rule
#     this is just a way to hide things -- which is precisely the defect class
#     this run keeps uncovering (a value written and never read; a list typed
#     twice and never compared). An expectation nobody re-checks is one more
#     thing that never compares itself.
#
# Fields:
#     check/code  the finding this expects
#     token       a substring that must appear in the finding's message; this is
#                 what keeps an expectation NARROW. Expecting a whole check would
#                 blind the guard to unrelated instances of the same code.
#     reason      why it is open on purpose
#     expires     the observable condition that should retire it, in plain words
#     owner/lane  who decided, and under what lane number
#
EXPECTED = [
    {
        "check": "SRCFILE_DRIFT",
        "code": "UNCOLLECTED",
        "token": "src/cli/cmd_area51.cpp",
        "reason": "Planted fixture. cmd_area51.cpp is a real, tracked, "
                  "contract-bearing source file deliberately left out of the SRC* "
                  "catalog so the next first-class full-stack pass has one piece of "
                  "unplanted evidence to be tested against. Seeding the catalog "
                  "first would destroy the only honest test available.",
        "expires": "The new full-stack pass reports this file as tree-present and "
                   "catalog-absent from its own traversal, WITHOUT being told where "
                   "to look. On that event: harvest the file, delete this entry, and "
                   "record the catch as evidence.",
        "owner": "member.derald",
        "lane": "AIF-067",
        "recorded": "2026-07-27",
        "doc": "docs/maintenance/SUBCOMMAND_IDENTITY_CONTRACT_LANE_V1.md sec 9a",
    },
]


def apply_expectations(findings: list) -> tuple[list, list, list]:
    """
    Split findings into (active, expected_hits) and raise STALE_EXPECTATION for
    any registry entry that matched nothing.

    Matching is check + code + message substring. Deliberately narrow: an
    expectation for one file must not silence the same code for another.
    """
    active, expected_hits, stale = [], [], []
    matched = {id(e): 0 for e in EXPECTED}

    for f in findings:
        hit = None
        for e in EXPECTED:
            if (f["check"] == e["check"] and f["code"] == e["code"]
                    and e["token"] in f["message"]):
                hit = e
                break
        if hit is not None:
            matched[id(hit)] += 1
            expected_hits.append({**f, "expected_reason": hit["reason"],
                                  "expected_lane": hit["lane"]})
        else:
            active.append(f)

    for e in EXPECTED:
        if matched[id(e)] == 0:
            stale.append({
                "check": "EXPECTATION", "code": "STALE_EXPECTATION",
                "severity": "WARN",
                "message": f"{e['lane']} expected {e['check']}/{e['code']} matching "
                           f"'{e['token']}' and it no longer occurs. Either the "
                           f"condition was resolved -- in which case DELETE the entry "
                           f"from EXPECTED, and if it was the planted fixture, record "
                           f"the catch -- or the check stopped looking. An expectation "
                           f"that silently stops matching is how a suppression list "
                           f"turns into a blind spot. Recorded {e['recorded']} by "
                           f"{e['owner']}; see {e['doc']}.",
            })
    return active + stale, expected_hits, stale


def comparable(summary: dict) -> dict:
    """Baseline view -- excludes the timestamp and free-text messages.

    Note this ratchets on ACTIVE findings only. Expected findings are reported
    but never counted, so a deliberate open item cannot masquerade as a
    regression, and equally cannot be quietly absorbed into a raised baseline.
    """
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
        if s.get("expected"):
            print(f"  expected (not counted): {len(s['expected'])}")
        print()
        for f in s["findings"]:
            print(f"  [{f['severity']}] {f['check']}/{f['code']}: {f['message']}")
        for f in s.get("expected", []):
            print(f"  [EXPECTED {f['expected_lane']}] {f['check']}/{f['code']}: "
                  f"{f['message']}")

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
