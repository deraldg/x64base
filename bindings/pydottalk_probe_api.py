# pydottalk_probe_api.py
# Prints the live API exposed by the built pydottalk module.

from __future__ import annotations

import os
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def add_build_python_to_path() -> Path:
    root = repo_root()
    build_python = Path(os.environ.get("PYDOTTALK_BIN", root / "build-labtalk" / "python"))
    if str(build_python) not in sys.path:
        sys.path.insert(0, str(build_python))
    return build_python


def public_names(obj) -> list[str]:
    return [name for name in dir(obj) if not name.startswith("_")]


def main() -> int:
    build_python = add_build_python_to_path()
    print("PY:", sys.version)
    print("EXE:", sys.executable)
    print("PYDOTTALK_BIN:", build_python)

    import pydottalk

    print("pydottalk file:", getattr(pydottalk, "__file__", None))
    print("pydottalk version:", pydottalk.version() if hasattr(pydottalk, "version") else "(missing)")
    print("HAVE_XBASE:", getattr(pydottalk, "HAVE_XBASE", None))
    print()
    print("module public names:")
    for name in public_names(pydottalk):
        print(" -", name)

    if hasattr(pydottalk, "xbase") and hasattr(pydottalk.xbase, "DbArea"):
        print()
        print("xbase.DbArea public names:")
        for name in public_names(pydottalk.xbase.DbArea):
            print(" -", name)

    print()
    print("OK: API probe completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
