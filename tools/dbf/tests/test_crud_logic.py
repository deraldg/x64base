#!/usr/bin/env python3
"""Runnable CRUD-logic tests using FakeArea -- no pydottalk .pyd required.

Covers every close-policy family and the posture-A guards. Runs green in the
steward sandbox, so the tool is TESTED, not merely written (AIF-085).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import schema_registry as reg          # noqa: E402
import crud                            # noqa: E402
from fake_area import FakeArea         # noqa: E402

PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")


def factory_for(area):
    return lambda spec: area


# 1. create assigns pk + rowver, validates unknown field ------------------------
def test_create_assigns_id_and_rowver():
    spec = reg.get("SYSLANE")
    area = FakeArea(spec).seed([{"ID": "1", "LKEY": "AIF-001"},
                                {"ID": "2", "LKEY": "AIF-002"}])
    res = crud.op_create(area, spec, {"LKEY": "AIF-003", "TITLE": "third"})
    check(res["ID"] == "3", f"next id should be 3, got {res.get('ID')}")
    check(res["ROWVER"] == "1", "rowver should default to 1")
    live = area.live_rows()
    check(len(live) == 3, "should have 3 live rows after create")


def test_create_rejects_unknown_field():
    spec = reg.get("SYSLANE")
    area = FakeArea(spec)
    try:
        crud.op_create(area, spec, {"NOPE": "x"})
        check(False, "unknown field should raise")
    except crud.CrudError:
        check(True, "")


def test_create_validates_c_width():
    spec = reg.get("SYSLANE")
    area = FakeArea(spec)
    try:
        crud.op_create(area, spec, {"LKEY": "X" * 99})  # LKEY is C(16)
        check(False, "over-width C field should raise")
    except crud.CrudError:
        check(True, "")


# 2. read: where filter + deleted skipping --------------------------------------
def test_read_where_and_deleted():
    spec = reg.get("SYSLANE")
    area = FakeArea(spec).seed([
        {"ID": "1", "LKEY": "A", "STATUS": "1"},
        {"ID": "2", "LKEY": "B", "STATUS": "4"},
        {"ID": "3", "LKEY": "C", "STATUS": "1"},
    ])
    area.goto_rec(3)
    area.delete_current()
    rows = crud.op_read(area, spec, {"STATUS": "1"}, include_deleted=False, limit=None)
    check(len(rows) == 1 and rows[0]["LKEY"] == "A",
          f"only live STATUS=1 row A expected, got {[r['LKEY'] for r in rows]}")
    rows_all = crud.op_read(area, spec, {"STATUS": "1"}, include_deleted=True, limit=None)
    check(len(rows_all) == 2, "include-deleted should see A and C")


# 3. update: in place + rowver bump; append-only refusal ------------------------
def test_update_bumps_rowver():
    spec = reg.get("SYSLANE")
    area = FakeArea(spec).seed([{"ID": "1", "LKEY": "A", "STATUS": "0", "ROWVER": "1"}])
    crud.op_update(area, spec, "A", {}, {"STATUS": "1"})
    check(area.live_rows()[0]["STATUS"] == "1", "status should update")
    check(area.live_rows()[0]["ROWVER"] == "2", "rowver should bump to 2")


def test_update_append_only_refused():
    spec = reg.get("SYSRUN")
    area = FakeArea(spec).seed([{"ID": "1", "RKEY": "run-1", "STATUS": "0"}])
    try:
        crud.op_update(area, spec, "run-1", {}, {"STATUS": "1"})
        check(False, "append-only update should refuse")
    except crud.CrudError:
        check(True, "")


# 4. soft-close families --------------------------------------------------------
def test_softclose_bitemporal():
    spec = reg.get("SYSMEMBER")
    area = FakeArea(spec).seed([{"ID": "1", "MKEY": "member.x", "VTHRU": "0",
                                 "ROWVER": "1"}])
    crud.op_soft_close(area, spec, "member.x", {})
    row = area.live_rows()[0]
    check(int(row["VTHRU"]) > 0, "VTHRU should be stamped")
    check(row["ROWVER"] == "2", "ROWVER should bump")


def test_softclose_status_with_epoch():
    spec = reg.get("SYSTASK")
    area = FakeArea(spec).seed([{"ID": "1", "TKEY": "t1", "STATUS": "0", "DONEAT": "0",
                                 "ROWVER": "1"}])
    crud.op_soft_close(area, spec, "t1", {})
    row = area.live_rows()[0]
    check(row["STATUS"] == "2", "task terminal status should be 2 (done)")
    check(int(row["DONEAT"]) > 0, "DONEAT epoch should be stamped")


def test_softclose_status_string():
    spec = reg.get("SYSPROOF")
    area = FakeArea(spec).seed([{"ID": "1", "PKEY": "p1", "STATE": "validated"}])
    crud.op_soft_close(area, spec, "p1", {})
    check(area.live_rows()[0]["STATE"] == "retired", "proof STATE -> retired")


def test_softclose_appendonly_appends_terminal():
    spec = reg.get("SYSRULING")
    area = FakeArea(spec).seed([{"ID": "1", "RULEID": "6.5a", "STATUS": "1",
                                 "DECIDEDAT": "100", "ROWVER": "1"}])
    crud.op_soft_close(area, spec, "6.5a", {})
    rows = area.live_rows()
    check(len(rows) == 2, "append-only close should add a row, not mutate")
    newest = rows[-1]
    check(newest["STATUS"] == "4", "new terminal row STATUS should be 4 (withdrawn)")
    check(newest["ID"] == "2", "new terminal row gets next id")
    check(int(newest["DECIDEDAT"]) > 100, "new row gets a later DECIDEDAT")


def test_softclose_crosswalk_refused():
    spec = reg.get("SYSRUNLANE")
    area = FakeArea(spec).seed([{"RUNKEY": "r1", "LANEKEY": "AIF-1"}])
    try:
        crud.op_soft_close(area, spec, None, {"RUNKEY": "r1", "LANEKEY": "AIF-1"})
        check(False, "crosswalk soft-close should refuse")
    except crud.CrudError:
        check(True, "")


# 5. purge tombstone + crosswalk removal ----------------------------------------
def test_purge_tombstones():
    spec = reg.get("SYSRUNLANE")
    area = FakeArea(spec).seed([{"RUNKEY": "r1", "LANEKEY": "AIF-1"},
                                {"RUNKEY": "r1", "LANEKEY": "AIF-2"}])
    crud.op_purge(area, spec, None, {"RUNKEY": "r1", "LANEKEY": "AIF-1"})
    live = area.live_rows()
    check(len(live) == 1 and live[0]["LANEKEY"] == "AIF-2",
          "purge should tombstone exactly the matched link")


# 6. posture-A write guard on bbs -----------------------------------------------
def test_bbs_write_refused():
    spec = reg.get("SYSBOARD")
    area = FakeArea(spec)
    for fn in (lambda: crud.op_create(area, spec, {"BKEY": "b"}),
               lambda: crud.op_soft_close(area, spec, "b", {})):
        try:
            fn()
            check(False, "bbs write should be refused (posture A)")
        except crud.CrudError:
            check(True, "")


# 7. alias / prefix resolver ----------------------------------------------------
def test_alias_resolution():
    check(crud.resolve_cmd("r") == "read", "r -> read")
    check(crud.resolve_cmd("rm") == "delete", "rm -> delete")
    check(crud.resolve_cmd("cr") == "create", "unambiguous prefix cr -> create")
    check(crud.resolve_cmd("up") == "update", "prefix up -> update")
    check(crud.resolve_cmd("q") == "quit", "q -> quit")


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print(f"\ntest_crud_logic: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
