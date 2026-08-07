from __future__ import annotations
import os
from pathlib import Path

PYCRUD_ROOT = Path(__file__).resolve().parents[3]

def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"

# Default to the local pycrud demo files, independent of the process cwd.
DB_URL = os.getenv("DB_URL", _sqlite_url(PYCRUD_ROOT / "data" / "demo.sqlite"))
SCHEMA_PATH = os.getenv("SCHEMA_PATH", str(PYCRUD_ROOT / "data" / "xbase_schema.json"))
FIXTURES_PATH = os.getenv("FIXTURES_PATH", str(PYCRUD_ROOT / "data" / "xbase_fixtures.json"))
