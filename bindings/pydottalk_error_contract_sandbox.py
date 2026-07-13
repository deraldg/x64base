#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from pydottalk_nonmemo_common import import_pydottalk, open_area, repo_default_sandbox, safe_close

def record_case(label, fn):
    print(f"CASE {label}")
    try:
        print(f"  RESULT: {fn()!r}")
    except Exception as exc:
        print(f"  EXCEPTION: {type(exc).__name__}: {exc}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dbf", default=None)
    ns = ap.parse_args()
    pydottalk = import_pydottalk()
    path = Path(ns.dbf) if ns.dbf else repo_default_sandbox() / "STUDENTS.dbf"
    print("PYDOTTALK ERROR CONTRACT")
    print(f"path: {path}")
    closed = pydottalk.xbase.DbArea()
    record_case("closed_is_open", lambda: closed.is_open())
    record_case("closed_rec_count", lambda: closed.rec_count())
    record_case("closed_get_1", lambda: closed.get(1))
    record_case("missing_open", lambda: pydottalk.xbase.DbArea().open(str(path.with_name("__NO_SUCH_TABLE__.dbf"))))
    area = open_area(path)
    try:
        record_case("goto_rec_0", lambda: area.goto_rec(0))
        record_case("goto_rec_minus_1", lambda: area.goto_rec(-1))
        record_case("goto_rec_after_last", lambda: area.goto_rec(int(area.rec_count()) + 100))
        record_case("get_field_0", lambda: area.get(0))
        record_case("get_field_after_last", lambda: area.get(int(area.field_count()) + 1))
        record_case("set_field_after_last", lambda: area.set(int(area.field_count()) + 1, "X"))
    finally:
        safe_close(area)
    print("OK: error contract capture completed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
