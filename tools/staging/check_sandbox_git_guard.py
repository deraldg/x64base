#!/usr/bin/env python3
"""Refuse git from a non-host root, and detect a stale index.lock.

AIF-082, 6.5f. `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:36-42` warns
in specific terms that running git through an unreliable mount leaves a stale
`.git/index.lock` and wedges the maintainer's commits. On 2026-07-31 this
steward read that warning during onboarding, cited it approvingly in its own lane
charter as an example of the corpus working, and then wedged the index with
exactly that mistake inside the hour. The rule was correct, dated, specific and
already read. It had no mechanism.

This is the mechanism, and it is the reason 6.6 lets the prose demote: once a
gate hard-fails, the gate is the memory.

TWO CHECKS, deliberately separate:

  1. ROOT     -- am I running from a declared host root? A sandbox mount is not.
                 `repository_role_guard.py` already answers this for its own
                 purposes; this reuses the same signal for a different decision.
  2. LOCK     -- is a stale `.git/index.lock` present? Zero bytes with no live
                 git process is the known-stale signature, and it is what a
                 killed or timed-out git leaves behind.

The lock check is the one that pays for itself. Any session, host or sandbox, can
run it in a second and know whether the repository is wedged before wasting an
afternoon on it.

Usage (PowerShell 7, from D:\\code\\ccode):

    python tools\\staging\\check_sandbox_git_guard.py            # both checks
    python tools\\staging\\check_sandbox_git_guard.py --lock-only

Exit codes: 0 clear, 2 stale lock present, 3 non-host root (advisory).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# The declared host roots, from the repository-role contract. Matching is done on
# a normalized lowercase string because Windows paths arrive in both slash forms.
HOST_ROOTS = ("d:/code/ccode", "c:/x64base")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "AI_README.md").exists():
            return candidate
    print("git-guard: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def on_host_root(root: Path) -> bool:
    norm = str(root.resolve()).replace("\\", "/").lower().rstrip("/")
    return any(norm == r or norm.startswith(r + "/") for r in HOST_ROOTS)


def check_lock(root: Path) -> int:
    lock = root / ".git" / "index.lock"
    if not lock.exists():
        print("git-guard: no index.lock -- repository is not wedged")
        return 0

    size = lock.stat().st_size
    mtime = lock.stat().st_mtime
    import datetime

    when = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    print(f"git-guard: index.lock PRESENT  {size} bytes  written {when}")
    if size == 0:
        print("")
        print("Zero bytes is the known-stale signature: git created the lock and was")
        print("killed before writing the index. Every subsequent commit will fail with")
        print("'Unable to create .git/index.lock: File exists'.")
        print("")
        print("If no git process is running, remove it:")
        print("    Get-Process git -ErrorAction SilentlyContinue")
        print("    Remove-Item .git\\index.lock")
    else:
        print("")
        print("NON-EMPTY lock. That is not the known-stale signature -- a git process")
        print("may genuinely be mid-operation. Do not delete it blindly; check for a")
        print("running git first and inspect the file.")
    return 2


def check_root(root: Path) -> int:
    if on_host_root(root):
        print(f"git-guard: host root OK -- {root}")
        return 0

    print(f"git-guard: NON-HOST ROOT -- {root}")
    print("")
    print("This is a mounted copy, not a declared host root. Per")
    print("LOCAL_ACCESS_AGENT_CHECKLIST_V1.md:36-42, run NO git commands from here,")
    print("including read-only ones: git takes .git/index.lock and cannot reliably")
    print("unlink it across a mount. A killed git then leaves a zero-byte lock that")
    print("blocks the maintainer's commits. This happened on 2026-07-31.")
    print("")
    print("Read and write files freely. Prepare git as commands and hand them over.")
    print("Note that claim-aif shells out to git grep, so it is host-side too.")
    return 3


def main() -> int:
    parser = argparse.ArgumentParser(description="Guard against git-over-a-mount and stale locks.")
    parser.add_argument("--lock-only", action="store_true", help="skip the root check")
    args = parser.parse_args()

    root = repo_root()
    lock_status = check_lock(root)
    if args.lock_only:
        return lock_status

    print("")
    root_status = check_root(root)

    # A stale lock is the more urgent condition and wins the exit code.
    return lock_status or root_status


if __name__ == "__main__":
    raise SystemExit(main())
