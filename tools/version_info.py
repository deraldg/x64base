from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

# AIF-120. The version has ONE authority: `project(DotTalkpp VERSION x)` in the
# root CMakeLists.txt. This module used to carry a hardcoded `fallback_version` as a
# default argument in THREE signatures -- three more hand-kept copies of a number
# that only one place is entitled to state, none of which any gate compared.
# It reads the authority instead. Nothing here restates a version.
_PROJECT_VERSION_RE = re.compile(
    r"project\s*\([^)]*?\bVERSION\s+([0-9][0-9A-Za-z.\-+]*)", re.IGNORECASE | re.DOTALL)

# What a caller gets when the authority cannot be read at all. Deliberately not a
# plausible version, for the same reason include/dottalk/version.hpp's fallback
# is not: a number that looks real is a lie a consumer will act on.
UNRESOLVED_VERSION = "0.0-unresolved"


def declared_version(root: Path | None = None) -> str:
    """The version declared by the root CMakeLists.txt project() call."""
    repo_root = find_repo_root(root)
    cmakelists = repo_root / "CMakeLists.txt"
    try:
        text = cmakelists.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return UNRESOLVED_VERSION
    match = _PROJECT_VERSION_RE.search(text)
    return match.group(1) if match else UNRESOLVED_VERSION


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


def version_info(root: Path | None = None, fallback_version: str | None = None) -> dict[str, object]:
    repo_root = find_repo_root(root)
    version = fallback_version if fallback_version is not None else declared_version(repo_root)
    sha = _git(repo_root, "rev-parse", "--short=8", "HEAD") or "nogit"
    date = _git(repo_root, "log", "-1", "--format=%cs") or datetime.now().strftime("%Y-%m-%d")
    dirty = bool(_git(repo_root, "status", "--porcelain"))
    return {
        "version": version,
        "date": date,
        "sha": sha,
        "dirty": dirty,
        "root": repo_root,
    }


def display_version(root: Path | None = None, fallback_version: str | None = None) -> str:
    info = version_info(root, fallback_version)
    version = str(info["version"])
    date = str(info["date"])
    sha = str(info["sha"])
    dirty = " dirty" if info["dirty"] else ""
    if sha and sha != "nogit":
        return f"v{version} ({date}, {sha}{dirty})"
    return f"v{version} ({date})"


def title_with_version(name: str, root: Path | None = None,
                       fallback_version: str | None = None) -> str:
    return f"{name} {display_version(root, fallback_version)}"
