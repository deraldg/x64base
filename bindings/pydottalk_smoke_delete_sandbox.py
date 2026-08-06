import os
import shutil
import sys
from pathlib import Path

import pydottalk
from pydottalk_helpers import Table
from pydottalk_nonmemo_common import repo_default_sandbox


def compact_row(row):
    return {
        "SID": row.get("SID"),
        "LNAME": row.get("LNAME"),
        "FNAME": row.get("FNAME"),
        "DOB": row.get("DOB"),
        "GENDER": row.get("GENDER"),
        "MAJOR": row.get("MAJOR"),
        "GPA": row.get("GPA"),
        "EMAIL": row.get("EMAIL"),
    }


def main() -> int:
    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("pydottalk:", pydottalk.version())
    print("module:", pydottalk.__file__)

    sandbox_dir = repo_default_sandbox()

    src = sandbox_dir / "STUDENTS.dbf"
    scratch = sandbox_dir / "PYDT_DELETE_SMOKE_STUDENTS.dbf"

    if not src.exists():
        raise FileNotFoundError(f"source table not found: {src}")

    if scratch.exists():
        scratch.unlink()

    shutil.copy2(src, scratch)

    print("source :", src)
    print("scratch:", scratch)
    print("NOTE   : delete smoke uses copied sandbox scratch table only")

    marker_sid = "99999998"

    with Table(scratch) as t:
        area = t.area

        before_count = area.rec_count()
        print("before rec_count:", before_count)

        sid_i = t.field_index("SID")
        lname_i = t.field_index("LNAME")
        fname_i = t.field_index("FNAME")
        dob_i = t.field_index("DOB")
        gender_i = t.field_index("GENDER")
        major_i = t.field_index("MAJOR")
        gpa_i = t.field_index("GPA")
        email_i = t.field_index("EMAIL")

        # Create a disposable marker record, then delete that same marker.
        area.append_blank()
        target_recno = area.recno()

        area.set(sid_i, marker_sid)
        area.set(lname_i, "DELETE")
        area.set(fname_i, "Smoke")
        area.set(dob_i, "20000102")
        area.set(gender_i, "X")
        area.set(major_i, "CSCI")
        area.set(gpa_i, "2.50")
        area.set(email_i, "pydottalk.delete@example.test")
        area.write_current()

        after_append_count = area.rec_count()
        print("after append rec_count:", after_append_count)
        print("target recno:", target_recno)

        if after_append_count != before_count + 1:
            raise RuntimeError(
                f"append did not increase record count by 1: "
                f"{before_count} -> {after_append_count}"
            )

        area.goto_rec(target_recno)
        before_delete_row = t.row_dict()

        print("before delete is_deleted:", area.is_deleted())
        print("before delete row:", compact_row(before_delete_row))

        if before_delete_row.get("SID") != marker_sid:
            raise RuntimeError(
                f"target recno does not contain marker SID {marker_sid}: "
                f"{before_delete_row.get('SID')}"
            )

        area.delete_current()

        print("after delete is_deleted:", area.is_deleted())
        print("after delete rec_count:", area.rec_count())

        if not area.is_deleted():
            raise RuntimeError("delete_current() did not mark current record deleted")

        if area.rec_count() != after_append_count:
            raise RuntimeError(
                f"delete changed record count unexpectedly: "
                f"{after_append_count} -> {area.rec_count()}"
            )

    # Reopen to prove delete flag persistence.
    with Table(scratch) as t:
        area = t.area

        reopened_count = area.rec_count()
        area.goto_rec(target_recno)
        row = t.row_dict()

        print("reopened rec_count:", reopened_count)
        print("reopened recno:", area.recno())
        print("reopened is_deleted:", area.is_deleted())
        print("reopened row:", compact_row(row))

        assert reopened_count == after_append_count
        assert row.get("SID") == marker_sid
        assert area.is_deleted() is True

    print()
    print("OK: sandbox delete smoke completed.")
    print("scratch table preserved for inspection:", scratch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
