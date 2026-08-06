# pydottalk_smoke_x64.py
# Read-only smoke against an explicit x64/x64base DBF candidate.
#
# Resolution order:
#   1. DOTTALK_X64_DBF = full path to a .dbf file
#   2. DOTTALK_X64_DBF_DIR = directory to scan for .dbf files
#   3. common project locations under dottalkpp/data/dbf

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, List


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def add_paths() -> None:
    root = repo_root()
    build_python = Path(os.environ.get("PYDOTTALK_BIN", root / "build-labtalk" / "python"))
    bindings_dir = root / "bindings"
    for path in (build_python, bindings_dir):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def project_dbf_root() -> Path:
    root = repo_root()
    candidates = [
        root / "dottalkpp" / "data" / "dbf",
        root / "data" / "dbf",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def candidate_files() -> List[Path]:
    explicit = os.environ.get("DOTTALK_X64_DBF")
    if explicit:
        return [Path(explicit)]

    root = project_dbf_root()
    out: List[Path] = []

    explicit_dir = os.environ.get("DOTTALK_X64_DBF_DIR")
    dirs: List[Path] = []
    if explicit_dir:
        dirs.append(Path(explicit_dir))

    dirs.extend([
        root / "x64",
        root / "x64" / "metadata",
        root / "sandbox",
        root,
    ])

    preferred_names = [
        "STUDENTS.dbf",
        "students.dbf",
        "students_x64.dbf",
        "X64SAMPLE.dbf",
        "SYSTEM_COMMANDS.dbf",
        "SYSCMD.dbf",
    ]

    seen = set()
    for d in dirs:
        if not d.exists() or not d.is_dir():
            continue
        for name in preferred_names:
            p = d / name
            key = str(p).lower()
            if p.exists() and key not in seen:
                out.append(p)
                seen.add(key)
        for p in sorted(d.glob("*.dbf")):
            key = str(p).lower()
            if key not in seen:
                out.append(p)
                seen.add(key)

    return out


def main() -> int:
    add_paths()

    import pydottalk
    from pydottalk_helpers import Table

    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("pydottalk:", pydottalk.version())
    print("module:", getattr(pydottalk, "__file__", None))

    candidates = candidate_files()
    print("candidate count:", len(candidates))
    for p in candidates[:12]:
        print(" -", p)

    if not candidates:
        print("FAIL: no x64 DBF candidates found. Set DOTTALK_X64_DBF or DOTTALK_X64_DBF_DIR.")
        return 2

    last_error = None
    for path in candidates:
        print()
        print("trying:", path)
        try:
            with Table(path) as table:
                desc = table.describe()
                print("OK: opened")
                print("logical_name:", desc["logical_name"])
                print("records     :", desc["rec_count"])
                print("rec_length  :", desc["rec_length"])
                print("field_count :", desc["field_count"])
                print("fields      :", ", ".join(table.field_names()[:12]))

                names = table.field_names()[:min(6, len(table.field_names()))]
                if desc["rec_count"] > 0 and names:
                    print("first row   :", table.row_dict(names=names))

            print()
            print("OK: x64 smoke completed using:", path)
            return 0
        except Exception as exc:
            last_error = exc
            print("skip: failed to open/read:", repr(exc))

    print()
    print("FAIL: no x64 candidate opened successfully.")
    if last_error is not None:
        print("last error:", repr(last_error))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
