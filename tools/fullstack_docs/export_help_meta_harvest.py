#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: tools
# layer: helper
# owns:
# project: project.x64base.runtime
# lane: full_stack_documentation
# owner: member.derald
# status: supported
#
# INTERIM SCAFFOLDING. This is the producer-side HELP/META -> harvest CSV
# exporter that Phase 8 entry-check E5 requires. It exists because no producer
# existed (the harvest was a hand-made May snapshot; HELP_META_EXPORT_MANIFEST
# read PENDING_EXPORT with a blank method). The PERMANENT home is a native
# CMDHELP / HELP-META export verb (beside export_helpdata_v2_dbfs), not this
# Python tool and NOT the read-only MANUAL consumer command. See
# docs/maintenance/lanes/full_stack_documentation/FULL_STACK_DOCUMENTATION_PHASE8_PUBLICATION_ASCENT_PLAN_V1.md.
#
# Read-only over source DBFs; writes only into the given --out directory. Does
# NOT touch the canonical docs/manuals/developer/manualgen/harvested/ snapshot.
#
# MEMO LIMITATION (v32 vs v64/x64): the underlying dbfread is a v32-era reader
# that does not follow memo blocks, so x64 memo fields (COMMANDS.USAGE/VERBOSE,
# CMD_ARGS.USAGE/VERBOSE, HELP_ARTIFACTS.TEXT/DETAIL/EVIDENCE, SYSFUNC.NOTES) come
# out as bare pointers -- matching the legacy May harvest, which also did not
# resolve them. The manual's PROSE comes from HELP_LINE (no memo fields; fully
# resolved), so manual content is current regardless. Resolving memo TEXT is a
# native x64/v64 capability and belongs to the permanent CMDHELP verb, not here.
"""Export the 14 HELP/META tables to a manualgen harvest workspace (CSV).

Dumps each source DBF verbatim (DBF field names as the CSV header, undeleted
rows only) so the output matches the manualgen harvest input contract's 14 files.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbfread  # noqa: E402

# dbfread emits unresolved .dbt memo cells as "<memo:unresolved ptr='N'>".
# The legacy (May) harvest emitted the bare pointer integer N and the pipeline
# consumes the actual prose from HELP_LINE, not these pointers. Match the legacy
# representation for parity. Resolving memo TEXT is deferred to the permanent
# native CMDHELP verb.
_MEMO = re.compile(r"^<memo:unresolved ptr=.*>$")


def _cell(value: str) -> str:
    # x64 memo TEXT is not resolvable by the v32-era dbfread. Blank the pointer
    # placeholder rather than leak it: the manual's prose comes from HELP_LINE
    # (no memo fields), and the native CMDHELP verb (USE/memo logic in
    # cmd_use.cpp) resolves memo text properly. Interim = resolved-or-empty.
    return "" if _MEMO.match(value) else value

# target CSV -> source DBF (relative to the data roots)
HELP_TABLES = {
    "HELP_COMMANDS.csv": "COMMANDS.dbf",
    "HELP_CMD_ARGS.csv": "CMD_ARGS.dbf",
    "HELP_HELP_ARTIFACTS.csv": "HELP_ARTIFACTS.dbf",
    "HELP_HELP_LINE.csv": "HELP_LINE.dbf",
    "HELP_HELP_SECTION.csv": "HELP_SECTION.dbf",
    "HELP_HELP_TOPIC.csv": "HELP_TOPIC.dbf",
}
META_TABLES = {
    "META_SYSARGS.csv": "SYSARGS.dbf",
    "META_SYSCMD.csv": "SYSCMD.dbf",
    "META_SYSENTVAR.csv": "SYSENTVAR.dbf",
    "META_SYSFLDDIC.csv": "SYSFLDDIC.dbf",
    "META_SYSFUNC.csv": "SYSFUNC.dbf",
    "META_SYSHELP.csv": "SYSHELP.dbf",
    "META_SYSMSG.csv": "SYSMSG.dbf",
    "META_SYSSUBCMD.csv": "SYSSUBCMD.dbf",
}


def _dump(dbf_path: Path, csv_path: Path) -> tuple[int, str]:
    table = dbfread.read(dbf_path)
    header = [f.name for f in table.fields]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        for row in table.rows:
            writer.writerow({k: _cell(v) for k, v in row.items()})
    return len(table.rows), ",".join(header)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True,
                    help="candidate harvest workspace (NOT the canonical harvested/)")
    args = ap.parse_args()

    root = args.repo_root.resolve()
    help_root = root / "dottalkpp" / "data" / "help"
    meta_root = root / "dottalkpp" / "data" / "metadata"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    total = 0
    for csv_name, dbf in HELP_TABLES.items():
        rows, _ = _dump(help_root / dbf, out / csv_name)
        total += rows
        manifest_rows.append(("HELP", dbf[:-4], csv_name, "yes", "EXPORTED",
                              rows, "export_help_meta_harvest.py", ""))
        print(f"  {csv_name:<26} {rows:>6} rows  <- data/help/{dbf}")
    for csv_name, dbf in META_TABLES.items():
        rows, _ = _dump(meta_root / dbf, out / csv_name)
        total += rows
        manifest_rows.append(("META", dbf[:-4], csv_name, "yes", "EXPORTED",
                              rows, "export_help_meta_harvest.py", ""))
        print(f"  {csv_name:<26} {rows:>6} rows  <- data/metadata/{dbf}")

    manifest = out / "HELP_META_EXPORT_MANIFEST_v0.csv"
    with manifest.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["source", "table_name", "target_csv", "required",
                    "current_status", "row_count", "export_method", "notes"])
        w.writerows(manifest_rows)

    print(f"harvest: {len(manifest_rows)} tables, {total} rows -> {out}")
    print("manifest: current_status flipped PENDING_EXPORT -> EXPORTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
