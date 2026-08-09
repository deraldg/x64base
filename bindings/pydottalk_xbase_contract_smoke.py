"""Disposable physical-order CRUD smoke for the pydottalk xbase binding.

The authoritative fixture is read and hashed but never opened for mutation.
All writes happen to a DBF-only copy under the system temporary directory, so
no memo or index sidecar can be attached accidentally.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def add_paths() -> None:
    root = repo_root()
    build_python = Path(
        os.environ.get("PYDOTTALK_BIN", root / "build-labtalk" / "python")
    )
    bindings_dir = root / "bindings"
    for path in (build_python, bindings_dir):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def source_fixture() -> Path:
    explicit = os.environ.get("DOTTALK_DBF")
    if explicit:
        return Path(explicit)
    return repo_root() / "dottalkpp" / "data" / "dbf" / "sandbox" / "STUDENTS.dbf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    add_paths()

    import pydottalk
    from pydottalk_helpers import Table

    source = source_fixture().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"DBF fixture not found: {source}")

    source_hash_before = sha256(source)
    marker_sid = "99999997"

    print("module       :", pydottalk.__file__)
    print("version      :", pydottalk.version())
    print("source       :", source)
    print("source sha256:", source_hash_before)

    with tempfile.TemporaryDirectory(prefix="pydottalk-xbase-contract-") as tmp:
        scratch = Path(tmp) / "STUDENTS.dbf"
        shutil.copy2(source, scratch)

        # Copy only the DBF. With no neighboring index sidecar, DbArea remains
        # in physical order even though the current binary links xindex.
        require(list(scratch.parent.iterdir()) == [scratch], "temporary fixture is not DBF-only")

        with Table(scratch) as table:
            area = table.area
            fields = table.field_names()
            require(area.is_open(), "temporary DBF did not open")
            require("SID" in fields and "LNAME" in fields, "expected fixture fields are missing")

            count_before = area.rec_count()
            require(count_before > 0, "fixture unexpectedly contains no records")

            area.goto_rec(1)
            first_sid = table.get("SID")
            require(bool(str(first_sid).strip()), "first record SID is blank")

            table.set("LNAME", "COREPROOF")
            table.set("FNAME", "Physical")
            table.write_current()
            require(area.rec_count() == count_before, "record update changed record count")

            area.append_blank()
            appended_recno = area.recno()
            table.set("SID", marker_sid)
            table.set("LNAME", "COREPROOF")
            table.set("FNAME", "Append")
            table.set("DOB", "20000103")
            table.set("GENDER", "X")
            table.set("MAJOR", "CSCI")
            table.set("GPA", "3.50")
            table.set("EMAIL", "coreproof@example.test")
            table.write_current()

            require(
                area.rec_count() == count_before + 1,
                "append did not increase record count by one",
            )

            area.goto_rec(appended_recno)
            require(table.get("SID") == marker_sid, "appended marker was not written")
            area.delete_current()
            require(area.is_deleted(), "delete did not mark appended record")

        with Table(scratch) as table:
            area = table.area
            require(
                area.rec_count() == count_before + 1,
                "reopen did not preserve appended record count",
            )

            area.goto_rec(1)
            require(table.get("LNAME") == "COREPROOF", "updated value did not persist")
            require(table.get("FNAME") == "Physical", "second updated value did not persist")

            area.goto_rec(appended_recno)
            require(table.get("SID") == marker_sid, "appended value did not persist")
            require(area.is_deleted(), "deleted flag did not persist")

        remaining = sorted(path.name for path in scratch.parent.iterdir())
        require(remaining == [scratch.name], f"unexpected sidecars created: {remaining}")

        print("temporary DBF:", scratch)
        print("records      :", count_before, "->", count_before + 1)
        print("sidecars     : none")

    source_hash_after = sha256(source)
    require(source_hash_after == source_hash_before, "authoritative fixture changed")

    print("source unchanged: yes")
    print("PASS: pydottalk xbase physical-order CRUD contract smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
