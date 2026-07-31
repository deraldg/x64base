from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    path = (start or Path.cwd()).resolve()
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return path


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def version_info(root: Path | None = None, fallback_version: str = "0.6") -> dict[str, object]:
    repo_root = find_repo_root(root)
    sha = _git(repo_root, "rev-parse", "--short=8", "HEAD") or "nogit"
    date = _git(repo_root, "log", "-1", "--format=%cs") or datetime.now().strftime("%Y-%m-%d")
    dirty = bool(_git(repo_root, "status", "--porcelain"))
    return {
        "version": fallback_version,
        "date": date,
        "sha": sha,
        "dirty": dirty,
        "root": repo_root,
    }


def display_version(root: Path | None = None, fallback_version: str = "0.6") -> str:
    info = version_info(root, fallback_version)
    version = str(info["version"])
    date = str(info["date"])
    sha = str(info["sha"])
    dirty = " dirty" if info["dirty"] else ""
    if sha and sha != "nogit":
        return f"v{version} ({date}, {sha}{dirty})"
    return f"v{version} ({date})"


def title_with_version(name: str, root: Path | None = None, fallback_version: str = "0.6") -> str:
    return f"{name} {display_version(root, fallback_version)}"
