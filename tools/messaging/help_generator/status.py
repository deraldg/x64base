"""Status, hashing, and savepoint helpers for generated HELP maintenance."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


def utc_stamp() -> str:
    """Return timezone-aware UTC timestamp with a stable Z suffix."""
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def append_savepoint(journal: Path, label: str, status: str, detail: str = "") -> None:
    journal.parent.mkdir(parents=True, exist_ok=True)
    line = f"- {utc_stamp()} {label}: {status}"
    if detail:
        line += f"; {detail}"
    with journal.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
