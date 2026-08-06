import os
import shutil
import sys
from pathlib import Path

import pydottalk
from pydottalk_helpers import Table
from pydottalk_nonmemo_common import repo_default_sandbox


def main() -> int:
    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("pydottalk:", pydottalk.version())
    print("module:", pydottalk.__file__)

    sandbox_dir = repo_default_sandbox()

    src = sandbox_dir / "STUDENTS.dbf"
    scratch = sandbox_dir / "PYDT_WRITE_SMOKE_STUDENTS.dbf"

    if not src.exists():
        raise FileNotFoundError(f"source table not found: {src}")

    if scratch.exists():
        scratch.unlink()

    shutil.copy2(src, scratch)

    print("source :", src)
    print("scratch:", scratch)
    print("NOTE   : write smoke uses copied sandbox scratch table only")

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

        area.append_blank()
        after_append_count = area.rec_count()
        print("after append rec_count:", after_append_count)

        if after_append_count != before_count + 1:
            raise RuntimeError(
                f"append did not increase record count by 1: "
                f"{before_count} -> {after_append_count}"
            )

        area.set(sid_i, "99999999")
        area.set(lname_i, "PYDOTTALK")
        area.set(fname_i, "Smoke")
        area.set(dob_i, "20000101")
        area.set(gender_i, "X")
        area.set(major_i, "CSCI")
        area.set(gpa_i, "4.00")
        area.set(email_i, "pydottalk.smoke@example.test")
        area.write_current()

        print("wrote scratch record")

    # Reopen to prove persistence.
    with Table(scratch) as t:
        area = t.area
        area.goto_rec(area.rec_count())
        row = t.row_dict()

        print("reopened rec_count:", area.rec_count())
        print("last row:", {
            "SID": row.get("SID"),
            "LNAME": row.get("LNAME"),
            "FNAME": row.get("FNAME"),
            "DOB": row.get("DOB"),
            "GENDER": row.get("GENDER"),
            "MAJOR": row.get("MAJOR"),
            "GPA": row.get("GPA"),
            "EMAIL": row.get("EMAIL"),
        })

        assert row.get("SID") == "99999999"
        assert row.get("LNAME") == "PYDOTTALK"
        assert row.get("FNAME") == "Smoke"
        assert row.get("DOB") == "20000101"
        assert row.get("GENDER") == "X"
        assert row.get("MAJOR") == "CSCI"

    print()
    print("OK: sandbox write smoke completed.")
    print("scratch table preserved for inspection:", scratch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
