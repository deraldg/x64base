#!/usr/bin/env python3
"""
AIF-067 M2 -- generate SYSSUBCMD from @dottalk.subusage contracts.

THE POINT OF THIS FILE
    SYSSUBCMD stops being typed. Source contracts are the authority; this
    emits the CSV and the seeding .dts. If a row is wrong, the contract is
    wrong, and the fix goes next to the code it describes.

WHAT WAS THERE BEFORE (measured 2026-07-27)
    dottalkpp/data/metadata/SYSSUBCMD.dbf -- 12 rows: 3 blank, plus the same
    three rows three times (SET PATH, SET ORDER, REL ENUM), one batch ACTIVE=F.
    Shape-test scratch, never a seed.

    dottalkpp/data/scripts/metadata/SYSSUBCMD_SEED_CANDIDATES_v1.csv -- 37 rows
    in a 10-field schema (SUBCMD_ID,PARENT_CMD,CAN_NAME,TOKEN,...) against the
    table's 20-field schema. Different names, different arity. It could never
    have loaded. Nothing ever tried, so nothing ever said so.

FIELDS THIS TOOL REFUSES TO INVENT
    The 20-field schema is defined NOWHERE in the repo -- no .dtx body, no
    CREATE script, no spec. Its meaning had to be recovered by reading the
    three surviving scratch rows. That recovery produced one genuine surprise:

        OWNER is a SUBSYSTEM ('runtime_paths', 'order_state', 'tuple_engine'),
        not a member id. Writing 'member.derald' there -- the obvious guess --
        would have been wrong in all 31 rows.

    So: populate what the contract states or what is mechanically derivable
    from it. Leave the rest EMPTY and report it, rather than filling a column
    with a confident guess. An empty column is a visible question; a wrong
    column is an invisible answer. Unresolved, listed by --report:
        OWNER      subsystem owner   -- not derivable from the contract
        LIFE_PH    lifecycle phase   -- 'session' vs 'command_execution',
                                        no rule recoverable from 3 rows
        PUB_SURF / DISP_REACH / OUT_ROUTE / MSG_CAT
                   four logicals that are 'F' in every surviving row, i.e.
                   they have never carried information

VOCABULARY NOTE
    VIS_TIER in the scratch rows is 'core'. The contracts use public|developer,
    mirroring the split SetUsageText already draws ("Public options" vs
    "Developer / transitional"). Three values now exist in one column and the
    enum is unratified; flagged rather than silently reconciled.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

SCAN_DIRS = ("src", "include", "bindings")
EXTS = {".cpp", ".hpp", ".h", ".c", ".inl", ".ipp"}

BLOCK_RE = re.compile(r"// @dottalk\.subusage v1\n(?:\s*//[^\n]*\n)+")

# Live 20-field schema, exact order, read from the DBF header.
COLUMNS = [
    "SUB_ID", "PARENT", "SUB_NAME", "QUAL_NAME", "DISP_STYL", "IMPL_STAT",
    "VIS_TIER", "OWNER", "REG_RING", "LIFE_PH", "SRC_AUTH", "SRC_FILE",
    "HANDLER", "PUB_SURF", "DISP_REACH", "OUT_ROUTE", "MSG_CAT", "ACTIVE",
    "VER_AT", "NOTES",
]

CREATE = (
    "CREATE X64 SYSSUBCMD ( SUB_ID C(32), PARENT C(80), SUB_NAME C(80), "
    "QUAL_NAME C(140), DISP_STYL C(32), IMPL_STAT C(32), VIS_TIER C(32), "
    "OWNER C(64), REG_RING C(64), LIFE_PH C(48), SRC_AUTH C(64), "
    "SRC_FILE C(180), HANDLER C(96), PUB_SURF L, DISP_REACH L, OUT_ROUTE L, "
    "MSG_CAT L, ACTIVE L, VER_AT C(24), NOTES M )"
)

# PROPOSED mapping, category -> REG_RING. The three REG_RING values below are
# the ones actually present in the scratch rows; everything else lands in
# core_settings. Declared here so it is reviewable, not buried in a branch.
REG_RING = {
    "index": "index_order",
    "relations": "relations",
}
REG_RING_DEFAULT = "core_settings"

UNPOPULATED = ("OWNER", "LIFE_PH", "PUB_SURF", "DISP_REACH", "OUT_ROUTE", "MSG_CAT")


def tracked(root: Path) -> list[Path]:
    """Membership is git, not the filesystem (settled 2026-07-26, member.derald)."""
    out = subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(root), "ls-files", *SCAN_DIRS],
        text=True,
    )
    return [root / p for p in out.split("\n")
            if p and Path(p).suffix.lower() in EXTS]


def parse_block(block: str) -> dict:
    """
    Parse one @dottalk.subusage block. Multi-line values continue under a bare
    `key:` line as further-indented `//   text` lines, matching the convention
    source_census.parse_usage_fields already uses for @dottalk.usage.
    """
    fields: dict[str, object] = {}
    key = None
    for raw in block.split("\n"):
        line = raw.strip()
        if not line.startswith("//"):
            continue
        body = line[2:].rstrip()
        if "@dottalk.subusage" in body:
            continue
        # A BLANK COMMENT LINE TERMINATES THE CURRENT LIST.
        #
        # This previously did `continue` without clearing `key`, so prose that
        # followed a blank line INSIDE the block kept appending to whatever list
        # was open. SYSSUBCMD's RELATIONS row shipped with
        #     syntax=SET RELATIONS <args...> | CORRECTED 2026-07-27. This
        #     contract previously read
        # -- an explanatory sentence advertised as a command syntax form.
        #
        # A contract block is a machine-read region. Commentary belongs above it,
        # and the parser now enforces the boundary rather than trusting authors
        # to remember (the author who forgot wrote this parser).
        if not body.strip():
            key = None
            continue
        m = re.match(r"^ (\S[^:]*):\s*(.*)$", body)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            if val:
                fields[key] = val
                key = None
            else:
                fields[key] = []
        elif key is not None and isinstance(fields.get(key), list):
            fields[key].append(body.strip())
    return fields


def harvest(root: Path) -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    for path in tracked(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            problems.append(f"{path}: {e}")
            continue
        if "@dottalk.subusage" not in text:
            continue
        rel = path.relative_to(root).as_posix()
        for block in BLOCK_RE.findall(text):
            f = parse_block(block)
            parent, sub = f.get("parent", ""), f.get("sub", "")
            if not parent or not sub:
                problems.append(f"{rel}: block missing parent: or sub:")
                continue
            qual = f"{parent} {sub}"
            notes = []
            if isinstance(f.get("summary"), list):
                notes.append("summary=" + " ".join(f["summary"]))
            if isinstance(f.get("usage"), list):
                notes.append("syntax=" + " | ".join(f["usage"]))
            if f.get("aliases"):
                notes.append(f"aliases={f['aliases']}")
            if f.get("build-gate"):
                notes.append(f"build-gate={f['build-gate']}")
            rows.append({
                "SUB_ID": "SUB_" + re.sub(r"\W+", "_", qual).upper(),
                "PARENT": parent,
                "SUB_NAME": sub,
                "QUAL_NAME": qual,
                "DISP_STYL": f.get("disp-style", ""),
                "IMPL_STAT": "implemented" if f.get("status") == "supported" else f.get("status", ""),
                "VIS_TIER": f.get("tier", ""),
                "OWNER": "",
                "REG_RING": REG_RING.get(f.get("category", ""), REG_RING_DEFAULT),
                "LIFE_PH": "",
                "SRC_AUTH": "subusage_contract",
                "SRC_FILE": Path(rel).name,
                "HANDLER": f.get("handler", ""),
                "PUB_SURF": "F", "DISP_REACH": "F", "OUT_ROUTE": "F", "MSG_CAT": "F",
                "ACTIVE": "T",
                "VER_AT": f.get("ver-at", ""),
                "NOTES": " ; ".join(notes),
            })
    rows.sort(key=lambda r: (r["PARENT"], r["SUB_NAME"]))

    seen: dict[str, str] = {}
    for r in rows:
        if r["QUAL_NAME"] in seen:
            problems.append(f"duplicate contract for {r['QUAL_NAME']}")
        seen[r["QUAL_NAME"]] = r["SRC_FILE"]
    return rows, problems


def write_dts(path: Path, csv_rel: str, count: int) -> None:
    path.write_text(
        f"""&& SYSSUBCMD_SEED_v1.dts
&&
&& GENERATED by tools/fullstack_docs/generate_syssubcmd.py (AIF-067 M2).
&& Do not hand-edit: fix the @dottalk.subusage contract in source and re-run.
&&
&& Seeds SYSSUBCMD from the subcommand contracts. Replaces 12 scratch rows
&& (3 blank + the same 3 rows three times) with {count} generated ones.
&&
&& ORDER is the canonical one, proven across eight tables:
&&     CREATE -> USE -> CDX CREATE -> CDX ADDTAG -> IMPORT -> BUILDLMDB
&& Index LAST, over populated data. Building it before IMPORT indexes an
&& empty table and never sees the rows.
&&
&& PATHS are explicit. A precondition in prose is not a precondition.
&&
&& NO ERASE: CREATE X64 already replaces the table.
&&
&& EXPECTED AFTER RUN: {count} records.
&&
&& Run:  ./datarun.ps1 -CommandLines 'DOTSCRIPT <abs path to this file>'

SET TALK OFF

; ===== SYSSUBCMD SEED START =====

SETPATH DBF metadata
SETPATH INDEXES INDEXES/metadata
SETPATH LMDB LMDB/metadata

WORKSPACE CLOSE
SELECT 0

{CREATE}

USE SYSSUBCMD
STRUCT

CDX CREATE
CDX ADDTAG SUB_ID
CDX ADDTAG PARENT
CDX ADDTAG SUB_NAME
CDX ADDTAG QUAL_NAME
CDX ADDTAG DISP_STYL
CDX ADDTAG VIS_TIER
CDX ADDTAG REG_RING
CDX ADDTAG SRC_AUTH

IMPORT {csv_rel}

BUILDLMDB CLEAN YES

; ===== READBACK =====
USE SYSSUBCMD
COUNT
STRUCT
LIST

; ===== SYSSUBCMD SEED END =====
QUIT
""",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out-csv",
                    default="dottalkpp/data/scripts/metadata/SYSSUBCMD_IMPORT_v1.csv")
    ap.add_argument("--out-dts",
                    default="dottalkpp/data/scripts/metadata/SYSSUBCMD_SEED_v1.dts")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    rows, problems = harvest(root)

    parents: dict[str, int] = {}
    for r in rows:
        parents[r["PARENT"]] = parents.get(r["PARENT"], 0) + 1
    print(f"contracts harvested: {len(rows)}")
    for p, n in sorted(parents.items()):
        print(f"  {p:10} {n}")
    for p in problems:
        print(f"  PROBLEM: {p}")

    if a.report:
        print("\ncolumns left EMPTY by design (no spec recoverable, not guessed):")
        for c in UNPOPULATED:
            print(f"  {c}")
        print("\nVIS_TIER values emitted:",
              sorted({r['VIS_TIER'] for r in rows}),
              "-- scratch rows used 'core'; enum unratified")
        gated = [r["QUAL_NAME"] for r in rows if "build-gate=" in r["NOTES"]]
        print(f"\nbuild-gated subcommands: {len(gated)}")
        for q in gated:
            print(f"  {q}")

    if problems:
        print("\nREFUSING to write while problems are outstanding.")
        return 2

    if not a.write:
        print("\ndry run -- pass --write to emit")
        return 0

    csv_path = root / a.out_csv
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {csv_path}  ({len(rows)} rows)")

    dts_path = root / a.out_dts
    write_dts(dts_path, "scripts/metadata/" + Path(a.out_csv).name, len(rows))
    print(f"wrote {dts_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
