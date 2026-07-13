#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from pydottalk_nonmemo_common import open_area, safe_close, repo_default_sandbox, assert_true, row_dict

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dbf", default=None)
    ns = ap.parse_args()
    path = Path(ns.dbf) if ns.dbf else repo_default_sandbox() / "STUDENTS.dbf"
    area = open_area(path)
    try:
        print("PYDOTTALK CURSOR MATRIX")
        print(f"path: {path}")
        print(f"logical_name: {area.logical_name()}")
        print(f"rec_count: {area.rec_count()}")
        print(f"field_count: {area.field_count()}")
        n = int(area.rec_count())
        assert_true(n > 0, "requires non-empty table")
        area.top()
        assert_true(area.recno() == 1, f"top recno expected 1 got {area.recno()}")
        print(f"top_row: {row_dict(area)}")
        if n >= 2:
            area.skip(1)
            assert_true(area.recno() == 2, f"skip(1) expected 2 got {area.recno()}")
            area.skip(-1)
            assert_true(area.recno() == 1, f"skip(-1) expected 1 got {area.recno()}")
        area.bottom()
        assert_true(area.recno() == n, f"bottom recno expected {n} got {area.recno()}")
        print(f"bottom_recno: {area.recno()}")
        mid = max(1, min(n, (n + 1) // 2))
        area.goto_rec(mid)
        assert_true(area.recno() == mid, f"goto_rec({mid}) expected {mid} got {area.recno()}")
        print(f"mid_row: {row_dict(area)}")
        for label, setup in [("after_last", lambda: (area.goto_rec(n), area.skip(1))), ("before_first", lambda: (area.goto_rec(1), area.skip(-1)))]:
            try:
                setup()
                print(f"{label}_recno: {area.recno()}")
                print(f"{label}_bof: {area.bof()}")
                print(f"{label}_eof: {area.eof()}")
            except Exception as exc:
                print(f"{label}_exception: {type(exc).__name__}: {exc}")
        print("OK: cursor matrix completed.")
        return 0
    finally:
        safe_close(area)

if __name__ == "__main__":
    raise SystemExit(main())
