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

R138. A LOCK THAT CLEARS ON ITS OWN WAS NEVER WEDGING ANYTHING. This check
answers "is the repository wedged", and a wedged repository's lock does not go
away while you look at it. Between 2026-09-01 15:14 and 15:16 this guard
hard-failed the prepush gate twice on a 668857-byte lock that was gone seconds
later both times, byte-identical across runs, with `.git/index` untouched --
a live git mid-operation, not wreckage. So the lock is now SAMPLED, not
stat'd once: a lock that survives the settle window is real, and one that does
not is reported and passed over. The stale ZERO-BYTE case still hard-fails on
the first sight of it, because that is the signature that cost an afternoon on
2026-07-31 and it never clears by itself.

A NON-EMPTY LOCK IS NOT A STALE LOCK AND MUST NOT BE REPORTED AS ONE. The
prose below already said so -- "not the known-stale signature", "do not delete
it blindly" -- while returning the same exit code as the stale case, which the
caller then summarized as "a stale index.lock is present. Remove it." The check
proved NOT STALE and the summary asserted STALE. That is the condensed
restatement losing the qualifier, and here it inverted it into an instruction
to delete a live git's lock. A persistent non-empty lock now returns its own
code so the caller cannot flatten the two.

The lock check is the one that pays for itself. Any session, host or sandbox, can
run it in a second and know whether the repository is wedged before wasting an
afternoon on it.

Usage (PowerShell 7, from D:\\code\\ccode):

    python tools\\staging\\check_sandbox_git_guard.py            # both checks
    python tools\\staging\\check_sandbox_git_guard.py --lock-only

Exit codes: 0 clear, 2 STALE lock (zero bytes) present, 3 non-host root
(advisory), 5 a non-empty lock that outlived the settle window -- a git may
be genuinely mid-operation, which is a WAIT, not a REMOVE.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
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


# How long to watch a lock before believing it. Three samples over two seconds
# is enough to outlast a `git diff` index refresh and short enough that nobody
# stops running the check. It is a WINDOW, not a proof of absence: a git that
# takes longer than this is reported as persistent, which is the safe way to be
# wrong here -- the guard says WAIT, and waiting costs seconds.
SETTLE_SAMPLES = 3
SETTLE_SECONDS = 1.0


def _lock_stat(lock: Path):
    """(size, mtime) or None. Never raises: the file we are watching for is the
    file most likely to vanish between exists() and stat()."""
    try:
        st = lock.stat()
        return st.st_size, st.st_mtime
    except (FileNotFoundError, OSError):
        return None


def check_lock(root: Path) -> int:
    lock = root / ".git" / "index.lock"
    first = _lock_stat(lock)
    if first is None:
        print("git-guard: no index.lock -- repository is not wedged")
        return 0

    import datetime

    size, mtime = first
    when = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"git-guard: index.lock PRESENT  {size} bytes  written {when}")

    # ZERO BYTES IS DECIDED ON SIGHT. It is the killed-git signature, it does
    # not clear on its own, and every commit downstream fails on it with a
    # message that does not say why. Waiting two seconds to confirm a condition
    # that is already unambiguous only makes the gate slower.
    if size == 0:
        print("")
        print("Zero bytes is the known-stale signature: git created the lock and was")
        print("killed before writing the index. Every subsequent commit will fail with")
        print("'Unable to create .git/index.lock: File exists'.")
        print("")
        print("If no git process is running, remove it:")
        print("    Get-Process git -ErrorAction SilentlyContinue")
        print("    Remove-Item .git\\index.lock")
        return 2

    # NON-EMPTY: sample it. A live git writes the refreshed index into the lock
    # and renames it away; what we are looking at may already be gone.
    for _ in range(SETTLE_SAMPLES):
        time.sleep(SETTLE_SECONDS)
        again = _lock_stat(lock)
        if again is None:
            print("")
            print(f"CLEARED. The lock was gone within "
                  f"{SETTLE_SAMPLES * SETTLE_SECONDS:.0f}s -- a git process was "
                  f"mid-operation")
            print("and finished. Nothing is wedged and nothing needs removing.")
            return 0

    size2, mtime2 = again
    print("")
    print(f"PERSISTENT after {SETTLE_SAMPLES * SETTLE_SECONDS:.0f}s "
          f"({size2} bytes). NOT the known-stale signature -- a git")
    print("process may genuinely be mid-operation, or may have died holding a")
    print("written lock. DO NOT DELETE IT BLINDLY. Check for a running git first:")
    print("")
    print("    Get-Process git -ErrorAction SilentlyContinue")
    print("")
    print("If one is running, WAIT -- that is the whole remedy. If none is, compare")
    print("the lock against .git/index before deciding; a lock LARGER than the")
    print("index is a refresh that never landed and is safe to remove, and one")
    print("that differs by more than that is worth a human look.")
    return 5


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
