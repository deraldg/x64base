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
    scratch = sandbox_dir / "PYDT_UPDATE_SMOKE_STUDENTS.dbf"

    if not src.exists():
        raise FileNotFoundError(f"source table not found: {src}")

    if scratch.exists():
        scratch.unlink()

    shutil.copy2(src, scratch)

    print("source :", src)
    print("scratch:", scratch)
    print("NOTE   : update smoke uses copied sandbox scratch table only")

    target_recno = int(os.environ.get("PYDOTTALK_UPDATE_RECNO", "1"))

    with Table(scratch) as t:
        area = t.area

        before_count = area.rec_count()
        print("before rec_count:", before_count)

        if before_count < target_recno:
            raise RuntimeError(
                f"target recno {target_recno} is beyond record count {before_count}"
            )

        area.goto_rec(target_recno)
        before_row = t.row_dict()

        print("target recno:", area.recno())
        print("before row:", {
            "SID": before_row.get("SID"),
            "LNAME": before_row.get("LNAME"),
            "FNAME": before_row.get("FNAME"),
            "DOB": before_row.get("DOB"),
            "GENDER": before_row.get("GENDER"),
            "MAJOR": before_row.get("MAJOR"),
            "GPA": before_row.get("GPA"),
            "EMAIL": before_row.get("EMAIL"),
        })

        lname_i = t.field_index("LNAME")
        fname_i = t.field_index("FNAME")
        gender_i = t.field_index("GENDER")
        major_i = t.field_index("MAJOR")
        gpa_i = t.field_index("GPA")
        email_i = t.field_index("EMAIL")

        area.set(lname_i, "UPDATED")
        area.set(fname_i, "Python")
        area.set(gender_i, "X")
        area.set(major_i, "CSCI")
        area.set(gpa_i, "3.99")
        area.set(email_i, "pydottalk.update@example.test")
        area.write_current()

        after_write_count = area.rec_count()
        print("after write rec_count:", after_write_count)

        if after_write_count != before_count:
            raise RuntimeError(
                f"update changed record count unexpectedly: "
                f"{before_count} -> {after_write_count}"
            )

        print("updated scratch record")

    # Reopen to prove persistence.
    with Table(scratch) as t:
        area = t.area

        reopened_count = area.rec_count()
        area.goto_rec(target_recno)
        row = t.row_dict()

        print("reopened rec_count:", reopened_count)
        print("after row:", {
            "SID": row.get("SID"),
            "LNAME": row.get("LNAME"),
            "FNAME": row.get("FNAME"),
            "DOB": row.get("DOB"),
            "GENDER": row.get("GENDER"),
            "MAJOR": row.get("MAJOR"),
            "GPA": row.get("GPA"),
            "EMAIL": row.get("EMAIL"),
        })

        assert reopened_count == before_count
        assert row.get("LNAME") == "UPDATED"
        assert row.get("FNAME") == "Python"
        assert row.get("GENDER") == "X"
        assert row.get("MAJOR") == "CSCI"
        assert row.get("GPA") == "3.99"
        assert row.get("EMAIL") == "pydottalk.update@example.test"

    print()
    print("OK: sandbox update smoke completed.")
    print("scratch table preserved for inspection:", scratch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
