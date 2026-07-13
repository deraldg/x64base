# pydottalk_smoke_readonly.py
# Read-only pydottalk smoke against sandbox STUDENTS.dbf by default.

from __future__ import annotations

import os
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def add_paths() -> None:
    root = repo_root()
    build_python = Path(os.environ.get("PYDOTTALK_BIN", root / "build-labtalk" / "python"))
    bindings_dir = root / "bindings"
    for path in (build_python, bindings_dir):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def default_sandbox_dir() -> Path:
    root = repo_root()
    candidates = [
        root / "dottalkpp" / "data" / "dbf" / "sandbox",
        root / "data" / "dbf" / "sandbox",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def resolve_students_path() -> Path:
    explicit = os.environ.get("DOTTALK_DBF")
    if explicit:
        return Path(explicit)

    dbf_dir = Path(os.environ.get("DOTTALK_DBF_DIR", default_sandbox_dir()))
    for name in ("STUDENTS.dbf", "students.dbf", "STUDENTS.DBF"):
        candidate = dbf_dir / name
        if candidate.exists():
            return candidate
    return dbf_dir / "STUDENTS.dbf"


def main() -> int:
    add_paths()

    import pydottalk
    from pydottalk_helpers import Table

    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("pydottalk:", pydottalk.version())
    print("module:", getattr(pydottalk, "__file__", None))

    path = resolve_students_path()
    print("opening:", path)
    if not path.exists():
        print("FAIL: DBF not found. Set DOTTALK_DBF or DOTTALK_DBF_DIR.")
        return 2

    dbfs = pydottalk.list_dbf(str(path.parent)) if hasattr(pydottalk, "list_dbf") else []
    print("list_dbf count:", len(dbfs))

    with Table(path) as table:
        desc = table.describe()
        print("logical_name:", desc["logical_name"])
        print("records     :", desc["rec_count"])
        print("rec_length  :", desc["rec_length"])
        print("field_count :", desc["field_count"])
        print("fields      :", ", ".join(table.field_names()))

        interesting = [name for name in ("SID", "LNAME", "FNAME", "DOB", "GENDER", "MAJOR") if name in table.field_names()]
        if not interesting:
            interesting = table.field_names()[:6]

        print()
        print("first 5 rows:")
        for row in table.rows(limit=5, names=interesting):
            print(row)

    print()
    print("OK: read-only smoke completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
