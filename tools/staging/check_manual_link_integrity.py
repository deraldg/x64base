#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: staging
# layer: gate
# owns: the assertion that every page the accepted manual links to is tracked,
#       and that no untracked page sits unreferenced beside the accepted set
# project: project.x64base.runtime
# lane: full_stack_documentation
# owner: member.derald
# status: review-needed
"""check_manual_link_integrity.py -- the accepted manual must be IN THE REPOSITORY.

WHY THIS EXISTS
---------------
Measured 2026-09-02, from the commit output of `5c1a39f7f`: the accepted command
reference had NEVER BEEN TRACKED. All 165 pages landed as `create mode`, and the
175-file commit carried only 43 deletions. From the 2026-07-18 acceptance until
that moment, every Gate 4 apply wrote into files git could not see.

The reader `developer_manual_publication_v1.md` WAS tracked. The 164 pages it
links to were not. That is the shape worth naming: the index was in the
repository and its contents were not, so nothing looked wrong from either end.

WHAT IT COST, which is why this is a gate and not a note:

  - "accepted" meant "present on this disk". No other clone had the pages.
  - the acceptance ledgers, hashes and backups were the ONLY record of a change,
    so an apply could not be reviewed as a diff -- and this lane's entire
    defence against a bad apply is reviewing the diff. Four Gate 4 plans were
    built on 2026-09-02 and three were discarded on exactly that review; all
    three reported PASS_PLAN_ONLY findings=0.
  - it silently changed what the house-style gate meant. With the files
    untracked EVERY line is an added line, so pre-existing characters were
    correctly reported as new to history, and a check comparing against the
    on-disk backup instead of HEAD could not see why. That wrong conclusion was
    asserted twice before the commit output settled it.

TWO ASSERTIONS
--------------
  1. LINKED IMPLIES TRACKED. Every `(commands/NAME.md)` target in the accepted
     README must exist AND be tracked. A link to an untracked file resolves on
     the author's disk and nowhere else.
  2. NO UNTRACKED STRAYS. Any .md beside the accepted pages that is neither
     linked nor tracked is reported. Untracked-and-unreferenced is the one state
     that is wrong whichever way you resolve it -- 47 such pages were found on
     2026-09-02, dating from 2026-07-18 to 2026-08-25.

Assertion 1 hard-fails. Assertion 2 reports, because deciding whether a stray is
wanted is a human call and a gate that fails on somebody else's leftovers gets
bypassed -- and a bypassed gate is worse than none, because it looks like
protection. That reasoning is `check_house_style.py`'s, and it held up.

    exit 0   every linked page is tracked
    exit 1   the accepted manual is not where this expects it
    exit 2   at least one linked page is missing or untracked
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r"\(commands/([A-Za-z0-9_.-]+\.md)\)")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "AI_README.md").exists():
            return candidate
    print("manual-link-integrity: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def tracked(root: Path, rel: str) -> bool:
    """Ask git, not the filesystem. Presence on disk is what fooled everyone."""
    return subprocess.run(
        ["git", "--no-optional-locks", "ls-files", "--error-unmatch", rel],
        cwd=root, capture_output=True, timeout=30, check=False,
    ).returncode == 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manual-root", default=(
        "docs/manuals/developer/manualgen/published/"
        "developer_manual_publication_v1/command_reference_v1"))
    a = ap.parse_args(argv)

    root = repo_root()
    base = root / a.manual_root
    readme = base / "README.md"
    if not readme.is_file():
        print(f"manual-link-integrity: no README at {a.manual_root}")
        return 1

    links = sorted(set(LINK.findall(readme.read_text(encoding="utf-8", errors="replace"))))
    missing, untracked_linked = [], []
    for name in links:
        rel = f"{a.manual_root}/commands/{name}"
        if not (root / rel).is_file():
            missing.append(name)
        elif not tracked(root, rel):
            untracked_linked.append(name)

    on_disk = {p.name for p in (base / "commands").glob("*.md")}
    strays = sorted(
        n for n in on_disk - set(links)
        if not tracked(root, f"{a.manual_root}/commands/{n}")
    )

    print(f"manual-link-integrity: {len(links)} link target(s) in the accepted README")
    if strays:
        print(f"  ADVISORY -- {len(strays)} untracked page(s) beside the accepted set, "
              f"linked from nothing:")
        for n in strays[:10]:
            print(f"      {n}")
        if len(strays) > 10:
            print(f"      ... {len(strays) - 10} more")
        print("  Untracked AND unreferenced is wrong either way: track them or delete them.")

    if not missing and not untracked_linked:
        print("manual-link-integrity: PASS -- every linked page exists and is tracked")
        return 0

    for name in missing:
        print(f"  MISSING  {name} -- linked from the README, not on disk")
    for name in untracked_linked:
        print(f"  UNTRACKED {name} -- on disk, linked, and invisible to git")
    print("")
    print("A link to an untracked page resolves on the author's machine and NOWHERE ELSE.")
    print("The accepted manual is a deliverable; it belongs in the repository.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
