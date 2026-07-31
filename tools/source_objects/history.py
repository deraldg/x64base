from __future__ import annotations

import subprocess
from pathlib import Path


def git_history(repo: Path, relpath: str) -> dict[str, str]:
    """Return first/last committed attribution while following recorded renames."""
    result = subprocess.run(
        [
            "git", "-C", str(repo), "log", "--follow",
            "--format=%an%x1f%ad", "--date=short", "--", relpath,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return {}
    records = []
    for line in result.stdout.splitlines():
        if "\x1f" not in line:
            continue
        author, date = line.split("\x1f", 1)
        records.append((author.strip(), date.strip()))
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "--", relpath],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    working_tree_state = "modified" if status.stdout.strip() else "clean"
    if not records:
        return {"working_tree_state": working_tree_state}
    latest_author, latest_date = records[0]
    first_author, first_date = records[-1]
    return {
        "author": first_author,
        "created_date": first_date,
        "last_modified_by": latest_author,
        "last_modified_date": latest_date,
        "working_tree_state": working_tree_state,
    }
