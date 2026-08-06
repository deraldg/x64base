#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from pydottalk_nonmemo_common import copy_dbf_scratch, field_name, field_type, fields, open_area, repo_default_sandbox, safe_close, set_field_by_name, assert_true, row_dict

def fill_row(area, sid_value="99999001", suffix="APPEND"):
    for fd in fields(area):
        nm = field_name(fd).upper()
        typ = field_type(fd).upper()[:1]
        if typ == "M": continue
        if nm == "SID": set_field_by_name(area, nm, sid_value)
        elif nm == "LNAME": set_field_by_name(area, nm, "PYDLIFE")
        elif nm == "FNAME": set_field_by_name(area, nm, suffix)
        elif nm == "DOB": set_field_by_name(area, nm, "20000101")
        elif nm == "GENDER": set_field_by_name(area, nm, "X")
        elif nm == "MAJOR": set_field_by_name(area, nm, "CSCI")
        elif nm == "GPA": set_field_by_name(area, nm, "3.50")
        elif nm == "EMAIL": set_field_by_name(area, nm, f"pydottalk.{suffix.lower()}@example.test")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=None)
    ap.add_argument("--scratch-name", default="PYDT_APPEND_UPDATE_DELETE_LIFECYCLE.dbf")
    ns = ap.parse_args()
    src = Path(ns.source) if ns.source else repo_default_sandbox() / "STUDENTS.dbf"
    scratch = copy_dbf_scratch(src, ns.scratch_name)
    area = open_area(scratch)
    try:
        print("PYDOTTALK APPEND UPDATE DELETE LIFECYCLE")
        print(f"source: {src}")
        print(f"scratch: {scratch}")
        before = int(area.rec_count())
        print(f"before_rec_count: {before}")
        area.append_blank()
        assert_true(int(area.rec_count()) == before + 1, "append did not increment record count")
        target = int(area.rec_count())
        fill_row(area, "99999001", "APPEND")
        area.write_current()
        print(f"after_append_row: {row_dict(area)}")
        fill_row(area, "99999002", "UPDATED")
        area.write_current()
        print(f"after_update_row: {row_dict(area)}")
        area.delete_current()
        assert_true(area.is_deleted() is True, "delete_current did not mark row deleted")
        print(f"after_delete_is_deleted: {area.is_deleted()}")
    finally:
        safe_close(area)
    area = open_area(scratch)
    try:
        assert_true(int(area.rec_count()) == before + 1, "record count did not persist after reopen")
        area.goto_rec(before + 1)
        assert_true(area.is_deleted() is True, "delete flag did not persist after reopen")
        print(f"reopened_row: {row_dict(area)}")
        print("OK: append/update/delete lifecycle completed.")
        return 0
    finally:
        safe_close(area)

if __name__ == "__main__":
    raise SystemExit(main())
