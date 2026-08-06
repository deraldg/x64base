#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from pydottalk_nonmemo_common import copy_dbf_scratch, field_name, field_type, fields, get_field_by_name, open_area, repo_default_sandbox, safe_close, set_field_by_name, assert_true, row_dict

def choose_fixed_fields(area):
    out = []
    for fd in fields(area):
        nm = field_name(fd)
        typ = field_type(fd).upper()[:1]
        if nm and typ in {"C", "N", "F", "D", "L"}:
            out.append((nm, typ))
    return out

def value_for(name: str, typ: str) -> str:
    n = name.upper()
    if typ == "C":
        if n == "EMAIL": return "pydottalk.type@example.test"
        if n == "LNAME": return "PYDTYPE"
        if n == "FNAME": return "Matrix"
        if n == "GENDER": return "X"
        if n == "MAJOR": return "CSCI"
        return "PYDT"
    if typ in {"N", "F"}:
        return "3.77" if n == "GPA" else "7"
    if typ == "D": return "20000101"
    if typ == "L": return "T"
    return "X"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=None)
    ap.add_argument("--scratch-name", default="PYDT_FIXED_FIELD_TYPE_MATRIX.dbf")
    ns = ap.parse_args()
    src = Path(ns.source) if ns.source else repo_default_sandbox() / "STUDENTS.dbf"
    scratch = copy_dbf_scratch(src, ns.scratch_name)
    area = open_area(scratch)
    try:
        print("PYDOTTALK FIXED FIELD TYPE MATRIX")
        print(f"source: {src}")
        print(f"scratch: {scratch}")
        n0 = int(area.rec_count())
        assert_true(n0 > 0, "requires non-empty source table")
        chosen = choose_fixed_fields(area)
        assert_true(bool(chosen), "no fixed fields found")
        print(f"chosen_fields: {chosen}")
        area.top()
        print(f"before_row: {row_dict(area)}")
        for nm, typ in chosen:
            set_field_by_name(area, nm, value_for(nm, typ))
        area.write_current()
        print(f"after_write_row: {row_dict(area)}")
    finally:
        safe_close(area)
    area = open_area(scratch)
    try:
        assert_true(int(area.rec_count()) == n0, "record count changed during update")
        area.top()
        print(f"reopened_row: {row_dict(area)}")
        for nm, typ in choose_fixed_fields(area):
            got = get_field_by_name(area, nm).strip()
            expected = value_for(nm, typ)
            if typ == "L":
                assert_true(got.upper() in {"T", "TRUE", "1", "Y"}, f"{nm} expected truthy got {got!r}")
            elif typ in {"N", "F"}:
                assert_true(bool(got), f"{nm} numeric field came back empty")
            else:
                assert_true(bool(got), f"{nm} field came back empty")
        print("OK: fixed-field type matrix completed.")
        return 0
    finally:
        safe_close(area)

if __name__ == "__main__":
    raise SystemExit(main())
