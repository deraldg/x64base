#!/usr/bin/env python3
"""Verify that every file the portal declares mandatory is tracked by git.

AIF-082, finding C8. An unreachable canonical copy is the same as no copy. On
2026-07-31 two files were found untracked and therefore invisible to a clone:

  * `AGENTS.md`                                  -- the always-read shim for
                                                    Codex-family agents
  * `labtalk/ai_portal/SCOPE_CALIBRATION_SEED_V1.md`
                                                 -- step 5 of the Mandatory Start

Both were discovered by accident, from `create mode` lines in unrelated commits.
This check finds them on purpose.

The mandatory set is derived, not hand-listed, so it cannot drift away from what
the portal actually says: every repo-relative `.md` path backticked inside
`AI_README.md` and `AI_PORTAL.md`, plus the two vendor shims and the two entry
documents themselves.

Usage (PowerShell 7, from D:\\code\\ccode):

    python labtalk\\ai_portal\\check_mandatory_tracked.py

Exit codes: 0 all tracked, 1 repo root not found, 2 one or more untracked.
Run it host-side. It shells out to `git ls-files`, which is read-only and does
not touch the index, but the sandbox rule is absolute for a reason.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ENTRY_DOCS = ("AI_README.md", "AI_PORTAL.md")
ALWAYS_READ = ("CLAUDE.md", "AGENTS.md")
PATH_RE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.md)`")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "AI_README.md").exists():
            return candidate
    print("check: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def declared(root: Path) -> set[str]:
    """Every existing repo-relative .md path the entry documents point at."""
    found: set[str] = set(ENTRY_DOCS) | set(ALWAYS_READ)
    for name in ENTRY_DOCS:
        path = root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for hit in PATH_RE.findall(text):
            hit = hit.lstrip("./")
            if (root / hit).is_file():
                found.add(hit)
    return {f for f in found if (root / f).is_file()}


def tracked(root: Path) -> set[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if out.returncode != 0:
        print("check: git ls-files failed", file=sys.stderr)
        raise SystemExit(1)
    return set(out.stdout.split())


def main() -> int:
    root = repo_root()
    want = declared(root)
    have = tracked(root)
    missing = sorted(want - have)

    print(f"mandatory-tracked: {len(want)} declared file(s) checked")
    if not missing:
        print("mandatory-tracked: PASS -- every declared file is tracked")
        return 0

    print(f"mandatory-tracked: FAIL -- {len(missing)} declared file(s) UNTRACKED")
    for name in missing:
        print(f"  UNTRACKED  {name}")
    print("")
    print("These are invisible to a clone. An agent onboarding from GitHub")
    print("cannot read them. Commit them, or stop declaring them mandatory.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
