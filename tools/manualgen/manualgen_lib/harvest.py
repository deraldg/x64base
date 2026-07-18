from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .paths import ManualgenPaths
from .util import relpath, relpath_posix, sha256_file


REQUIRED_HARVEST_FILES = (
    "HELP_CMD_ARGS.csv",
    "HELP_COMMANDS.csv",
    "HELP_HELP_ARTIFACTS.csv",
    "HELP_HELP_LINE.csv",
    "HELP_HELP_SECTION.csv",
    "HELP_HELP_TOPIC.csv",
    "META_SYSARGS.csv",
    "META_SYSCMD.csv",
    "META_SYSENTVAR.csv",
    "META_SYSFLDDIC.csv",
    "META_SYSFUNC.csv",
    "META_SYSHELP.csv",
    "META_SYSMSG.csv",
    "META_SYSSUBCMD.csv",
)


def _resolve_requested_harvest(paths: ManualgenPaths, requested: str) -> Path:
    raw = Path(requested)
    return raw.resolve() if raw.is_absolute() else (paths.repo_root / raw).resolve()


def select_harvest_workspace(paths: ManualgenPaths) -> tuple[Path | None, str, bool]:
    """Select HELP/META evidence without copying or promoting it."""
    if paths.harvest_workspace:
        requested = _resolve_requested_harvest(paths, paths.harvest_workspace)
        return (requested, "explicit", True) if requested.is_dir() else (None, "explicit_invalid", False)

    legacy = paths.manualgen_root / "harvested"
    if legacy.is_dir():
        return legacy.resolve(), "legacy_default", True
    return None, "none", False


def _csv_shape(path: Path) -> tuple[list[str], int, str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            rows = sum(1 for _ in reader)
        return header, rows, "PASS" if header else "FAIL"
    except (OSError, UnicodeError, csv.Error):
        return [], -1, "FAIL"


def inventory_harvest(paths: ManualgenPaths) -> dict[str, Any]:
    root, selection_mode, selection_valid = select_harvest_workspace(paths)
    rows: list[dict[str, Any]] = []
    for name in REQUIRED_HARVEST_FILES:
        candidate = root / name if root else None
        exists = bool(candidate and candidate.is_file())
        header, row_count, readable = _csv_shape(candidate) if candidate and exists else ([], -1, "FAIL")
        rows.append({
            "file_name": name,
            "family": "HELP" if name.startswith("HELP_") else "META",
            "required": 1,
            "exists": 1 if exists else 0,
            "csv_readable": readable,
            "row_count": row_count,
            "column_count": len(header),
            "header": "|".join(header),
            "sha256": sha256_file(candidate) if candidate and exists else "",
            "relative_path": relpath(candidate, paths.repo_root) if candidate else "",
            "relative_path_posix": relpath_posix(candidate, paths.repo_root) if candidate else "",
        })

    return {
        "workspace": relpath(root, paths.repo_root) if root else "",
        "workspace_posix": relpath_posix(root, paths.repo_root) if root else "",
        "selection_requested": paths.harvest_workspace or "",
        "selection_mode": selection_mode,
        "selection_valid": 1 if selection_valid else 0,
        "required_file_count": len(REQUIRED_HARVEST_FILES),
        "present_file_count": sum(row["exists"] for row in rows),
        "readable_file_count": sum(row["csv_readable"] == "PASS" for row in rows),
        "files": rows,
    }
