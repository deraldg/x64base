#!/usr/bin/env python3
"""
AIF-067 -- generate SYSCMD from @dottalk.usage contracts.

SYSCMD stops being typed. Source contracts are the authority; this emits the CSV
and the seeding .dts, exactly as generate_syssubcmd.py does for SYSSUBCMD.

WHY THIS MATTERS MORE THAN TIDINESS
    SYSCMD held 203 rows while 223 commands carried contracts. The 24 missing
    ones were not merely undocumented -- they were INVISIBLE. On 2026-07-27 an AI
    partner working in this repository concluded that composed/teamwork agency
    was unmodelled and began writing a design for it, when `USER` -- the command
    implementing the entire identity/RBAC model -- had been sitting in source
    with a full contract and a HELP topic the whole time.

    It was absent from SYSCMD. The catalog is the surface you consult to ask
    "does this exist", so an incomplete catalog does not merely under-report:
    ABSENCE READS AS NON-EXISTENCE, and the system misinforms its own readers.

    That is the argument for deriving this table rather than maintaining it.

WHAT IS DERIVED AND WHAT IS DECLARED (see ENTITY_LIFECYCLE_AND_THE_BRIDGE_V1
section 2c -- declare only what cannot be derived)
    DERIVED   CMD_ID, CAN_NAME, HANDLER, ACTIVE, and whether a command exists
    DECLARED  TYPE for the 13 control-flow keywords, because it is not
              recoverable from any contract field. `category:` does not carry it:
              IF/SCAN/WHILE are `script`, but CONTINUE is `navigation` and CASE
              is `education-reference`. The set is small, closed and reviewable,
              so it lives HERE -- one declared list -- rather than as a new field
              on a thousand files.

CONTRACTS ARE THE AUTHORITY, THE REGISTRY IS THE CROSS-CHECK
    A contract naming a command the registry cannot dispatch is an IDENTITY
    ERROR, not a catalog gap, and this tool refuses to emit a row for it. Ten
    such cases exist today (CATALOGCANARY names its handler rather than its
    command; POLLING is a SET subcommand; and others). Emitting them would
    "close" the finding while burying ten real defects underneath it.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbfread  # noqa: E402

SCAN_DIRS = ("src", "include", "bindings")
EXTS = {".cpp", ".hpp", ".h", ".c", ".inl", ".ipp"}

USAGE_MARK = re.compile(r"^\s*//\s*@dottalk\.usage v1\s*$")


def usage_blocks(text: str) -> list[str]:
    """
    Split a file into @dottalk.usage blocks.

    NOT a regex, deliberately. The obvious pattern --
        //\\s*@dottalk\\.usage v1\\n(?://[^\\n]*\\n)+
    -- is GREEDY over consecutive comment lines, so when one file declares
    several commands in a single contiguous comment run, block 1 swallows
    blocks 2 and 3 and only the FIRST `command:` is ever seen.

    src/tv/cmd_recordview.cpp declares RECORDVIEW, RECORD and BROWSETV back to
    back. The regex reported one command; RECORD then appeared as "in the live
    table but not generated", which reads as a stale catalog rather than a blind
    harvester. Any multi-contract file was under-reported the same way.

    Same failure as the SetUsageText contamination earlier in this run: a match
    that does not stop at the boundary it is supposed to respect. A block ends at
    the next marker or at the first non-comment line, whichever comes first.
    """
    out, cur = [], None
    for line in text.splitlines():
        if USAGE_MARK.match(line):
            if cur is not None:
                out.append("\n".join(cur))
            cur = [line]
            continue
        if cur is None:
            continue
        if line.lstrip().startswith("//"):
            cur.append(line)
        else:
            out.append("\n".join(cur))
            cur = None
    if cur is not None:
        out.append("\n".join(cur))
    return out
CMD_RE = re.compile(r"(?m)^\s*(?://)?\s*command:\s*(.+?)\s*$")
# BOTH registration spellings. `registry().add(...)` is the core path; extensions
# use the free function `dli::register_extension_command(...)`. Matching only the
# first reported STUDENTECHO and STUDENTHELLO as "in the live table but not
# generated", which would have looked like the catalog was stale when in fact the
# harvester was blind to a registration path the system documents.
ADD_RE = re.compile(
    r'(?:registry\(\)\.add(?:_extension)?|register_extension_command)\('
    r'\s*"([^"]+)"\s*,?\s*(?:&\s*)?([A-Za-z_][A-Za-z0-9_]*)?')

COLUMNS = ["CMD_ID", "CAN_NAME", "TYPE", "VIS", "HANDLER", "ACTIVE"]

CREATE = ("CREATE X64 SYSCMD ( CMD_ID C(32), CAN_NAME C(80), TYPE C(20), "
          "VIS C(20), HANDLER C(96), ACTIVE L )")

# DECLARED, because it is not derivable. DotScript control-flow keywords: these
# are parsed as syntax rather than invoked as ordinary commands.
#
# CASE is deliberately NOT in this set. The live table classifies it as
# syntax-command, but its handler is edu_CASESTUDY and its category is
# education-reference -- it is the education case-study command, not a
# switch/case keyword. The existing row looks like a name collision that was
# never questioned. Flagged by --report rather than silently preserved.
CONTROL_FLOW = {
    "IF", "ELSE", "ENDIF",
    "SCAN", "ENDSCAN",
    "LOOP", "ENDLOOP",
    "UNTIL", "ENDUNTIL",
    "WHILE", "ENDWHILE",
    "CONTINUE",
}


def tracked(root: Path) -> list[str]:
    out = subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(root), "ls-files", *SCAN_DIRS],
        text=True)
    return [p for p in out.split("\n") if p and Path(p).suffix.lower() in EXTS]


def registry_map(root: Path) -> dict[str, str]:
    """name -> handler, from every registry().add site in the tree."""
    out: dict[str, str] = {}
    for rel in tracked(root):
        if not rel.endswith(".cpp"):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Cheap pre-filter -- but it must name EVERY registration spelling, or it
        # silently excludes files the regex below would have matched. It listed
        # only "registry().add" at first, so the student extension commands were
        # skipped before the widened pattern ever saw them, and the widening
        # appeared to have no effect. A fast path that filters on a narrower
        # condition than the slow path is a filter that hides the slow path.
        if ("registry().add" not in text
                and "register_extension_command" not in text):
            continue
        for line in text.splitlines():
            m = ADD_RE.search(line)
            if not m:
                continue
            name = m.group(1).upper()
            # the lambda body usually names the real handler
            h = re.search(r"\b((?:cmd|edu|fn)_[A-Za-z0-9_]+)\s*\(", line)
            out.setdefault(name, h.group(1) if h else (m.group(2) or ""))
    return out


def harvest(root: Path) -> tuple[dict[str, str], list[str]]:
    """command name -> declaring file."""
    names: dict[str, str] = {}
    dups: list[str] = []
    for rel in tracked(root):
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "@dottalk.usage" not in text:
            continue
        for blk in usage_blocks(text):
            m = CMD_RE.search(blk)
            if not m:
                continue
            nm = re.sub(r"\s+", " ", m.group(1)).strip().upper()
            if not nm or nm == "NONE" or "/" in nm:
                continue
            if nm in names and names[nm] != rel:
                dups.append(f"{nm} ({names[nm]}, {rel})")
            names.setdefault(nm, rel)
    return names, dups


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out-csv",
                    default="dottalkpp/data/scripts/metadata/SYSCMD_IMPORT_v3.csv")
    ap.add_argument("--out-dts",
                    default="dottalkpp/data/scripts/metadata/SYSCMD_SEED_v1.dts")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    contracts, dups = harvest(root)
    reg = registry_map(root)

    rows, unregistered, subcommands = [], [], []
    for nm in sorted(contracts):
        # MULTI-WORD NAMES ARE SUBCOMMANDS, NOT IDENTITY ERRORS.
        #
        # cmd_setcase.cpp and its siblings declare `command: SET CASE` using the
        # @dottalk.usage dialect, because they predate @dottalk.subusage. They
        # are correct contracts for the wrong table: their home is SYSSUBCMD,
        # which cmd_set.cpp's ladder now populates via parent:/sub:.
        #
        # So the SET family is currently described TWICE, in two vocabularies,
        # feeding two tables -- and seven of them (SET CASE, CDX, CNX, FILTER,
        # INDEX, NEAR, ORDER) sit in the live SYSCMD as though they were
        # top-level commands. Reported, not silently dropped.
        if " " in nm:
            subcommands.append(f"{nm}  ({contracts[nm]})")
            continue
        if nm not in reg:
            unregistered.append(f"{nm}  ({contracts[nm]})")
            continue
        rows.append({
            "CMD_ID": "CMD_" + re.sub(r"\W+", "_", nm).upper(),
            "CAN_NAME": nm,
            "TYPE": "syntax-command" if nm in CONTROL_FLOW else "command",
            "VIS": "public",
            "HANDLER": reg.get(nm, ""),
            "ACTIVE": "T",
        })

    uncontracted = sorted(n for n in reg if n not in contracts and " " not in n)

    live = dbfread.read(root / "dottalkpp/data/metadata/SYSCMD.dbf")
    live_names = {r["CAN_NAME"].upper() for r in live.rows}
    live_cols = [f.name for f in live.fields]

    print(f"contracts {len(contracts)}   registered {len(reg)}   emitting {len(rows)}")
    print(f"live SYSCMD {live.live} rows   ->  generated {len(rows)}")
    print(f"column order matches live header: {COLUMNS == live_cols}")
    if COLUMNS != live_cols:
        print(f"  live: {live_cols}\n  csv : {COLUMNS}")
        print("REFUSING to write: the CSV could not load into this table.")
        return 2

    new = sorted({r['CAN_NAME'] for r in rows} - live_names)
    gone = sorted(live_names - {r['CAN_NAME'] for r in rows})
    print(f"\nNEW rows (contracted+registered, absent from the live table): {len(new)}")
    for n in new:
        print(f"    + {n}")
    if gone:
        print(f"\nIN LIVE TABLE BUT NOT GENERATED: {len(gone)}")
        for n in gone:
            print(f"    - {n}")

    if a.report:
        print(f"\nSUBCOMMAND CONTRACTS IN THE @dottalk.usage DIALECT ({len(subcommands)}) "
              f"-- correct contracts, wrong table. Their home is SYSSUBCMD; several "
              f"currently sit in the live SYSCMD as if they were top-level commands:")
        for s in subcommands:
            print(f"    {s}")
        print(f"\nIDENTITY ERRORS -- contracted but NOT registered under that name "
              f"({len(unregistered)}). No row emitted; the contract names something "
              f"the dispatcher does not have:")
        for u in unregistered:
            print(f"    {u}")
        print(f"\nREGISTERED BUT UNCONTRACTED ({len(uncontracted)}) -- a command with "
              f"no usage contract cannot be catalogued from source:")
        for u in uncontracted[:20]:
            print(f"    {u}")
        if dups:
            print(f"\nDUPLICATE DECLARATIONS ({len(dups)}):")
            for d in dups:
                print(f"    {d}")
        if "CASE" in live_names:
            print("\nNOTE: the live table types CASE as syntax-command, but its "
                  "handler is edu_CASESTUDY and its category is education-reference "
                  "-- the education case-study command, not a control-flow keyword. "
                  "Generated as `command`; confirm before seeding.")

    if not a.write:
        print("\ndry run -- pass --write to emit")
        return 0

    csv_path = root / a.out_csv
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {csv_path}  ({len(rows)} rows)")

    dts = root / a.out_dts
    dts.write_text(f"""&& SYSCMD_SEED_v1.dts
&&
&& GENERATED by tools/fullstack_docs/generate_syscmd.py (AIF-067).
&& Do not hand-edit: fix the @dottalk.usage contract in source and re-run.
&&
&& Canonical order, proven across eight tables:
&&     CREATE -> USE -> CDX CREATE -> CDX ADDTAG -> IMPORT -> BUILDLMDB
&& Index LAST, over populated data.
&&
&& EXPECTED AFTER RUN: {len(rows)} records.
&&
&& Run:  ./datarun.ps1 -CommandLines 'DOTSCRIPT <abs path to this file>'

SET TALK OFF

; ===== SYSCMD SEED START =====

SETPATH DBF metadata
SETPATH INDEXES INDEXES/metadata
SETPATH LMDB LMDB/metadata

WORKSPACE CLOSE
SELECT 0

{CREATE}

USE SYSCMD
STRUCT

CDX CREATE
CDX ADDTAG CMD_ID
CDX ADDTAG CAN_NAME
CDX ADDTAG TYPE
CDX ADDTAG VIS
CDX ADDTAG HANDLER

IMPORT scripts/metadata/{Path(a.out_csv).name}

BUILDLMDB CLEAN SMALL YES

; ===== READBACK =====
USE SYSCMD
COUNT
STRUCT

; ===== SYSCMD SEED END =====
QUIT
""", encoding="utf-8")
    print(f"wrote {dts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
