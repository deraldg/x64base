#!/usr/bin/env python3
"""Read the portal tracking DBF tables via pydottalk -- the DERIVE source.

The tracking tables (SYSLANE / SYSRUN / SYSRUNLANE / SYSPROOF) were seeded into
dottalkpp/data/metadata/portal/ by load_tracking_tables.dts. This module reads them
back through pydottalk -- the same engine that owns them -- so reports can DERIVE
from the DBF store instead of parsing authored YAML/Markdown. This is the read half
of the dogfood: work -> a row in the engine -> a derived view. Because a landed lane
IS a row, it cannot be missing from a view that queries the table (the AIF-087
drift dies here).

It reuses the PROVEN read helpers in bindings/ (open_area, row_dict, safe_close) --
same ones the pydottalk proof scripts use -- rather than reinventing the API.

WINDOWS / pydottalk step: needs the built pydottalk .pyd (build-labtalk/python or
$PYDOTTALK_BIN). The steward's Linux sandbox cannot import the win_amd64 .pyd, so
this is authored + maintainer-run.

Usage:
  python tools/tracking/read_tracking.py            # counts + a sample row per table
  from read_tracking import read_all                # {table: [row_dict, ...]}
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PORTAL_DIR = REPO / "dottalkpp" / "data" / "metadata" / "portal"
TABLES = ["SYSLANE", "SYSRUN", "SYSRUNLANE", "SYSPROOF"]


def _wire_paths() -> None:
    """Put the pydottalk .pyd and the bindings helpers on sys.path."""
    build_py = Path(os.environ.get("PYDOTTALK_BIN", REPO / "build-labtalk" / "python"))
    if str(build_py) not in sys.path:
        sys.path.insert(0, str(build_py))
    bindings = REPO / "bindings"
    if str(bindings) not in sys.path:
        sys.path.insert(0, str(bindings))


def read_table(name: str, portal_dir: Path | None = None) -> list[dict]:
    """All rows of one tracking table as a list of {FIELD: str} dicts."""
    _wire_paths()
    from pydottalk_nonmemo_common import open_area, row_dict, safe_close  # type: ignore

    path = (portal_dir or PORTAL_DIR) / f"{name}.dbf"
    area = open_area(path)
    try:
        rows: list[dict] = []
        n = int(area.rec_count())
        if n > 0:
            area.top()
            for _ in range(n):
                rows.append(row_dict(area))
                area.skip(1)
        return rows
    finally:
        safe_close(area)


def read_all(portal_dir: Path | None = None) -> dict:
    """{table_name: [row_dict, ...]} for every tracking table."""
    return {t: read_table(t, portal_dir) for t in TABLES}


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Read the portal tracking DBF tables via pydottalk.")
    ap.add_argument("--portal-dir", default=str(PORTAL_DIR))
    args = ap.parse_args(argv)
    portal = Path(args.portal_dir)

    total = 0
    for t in TABLES:
        rows = read_table(t, portal)
        total += len(rows)
        print(f"{t}: {len(rows)} rows")
        if rows:
            sample = {k: (v[:38] + "..." if len(v) > 38 else v) for k, v in list(rows[0].items())[:6]}
            print(f"  sample: {sample}")
    print(f"TOTAL: {total} rows read from {portal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
