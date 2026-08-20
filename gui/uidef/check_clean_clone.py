#!/usr/bin/env python3
"""Every module gui/uidef imports must be tracked. AIF-120 R84.1.

A tool that imports an untracked sibling works for everyone who has run it once
and for nobody who clones. R87 found eleven of these at once -- an import of a
GITIGNORED file -- fixed them, and did not sweep for the same SHAPE. Two hours
later `manifest.py`, the checker every ruling in this lane quotes measurements
from, still failed on a clean clone because `resolve_workspace.py` was untracked.
Fixing a site instead of the rule; the fourth time this lane has done it.

PRIOR ART, and this file deliberately copies it rather than inventing:
`labtalk/ai_portal/check_mandatory_tracked.py` (AIF-082, finding C8) already
states the rule -- "an unreachable canonical copy is the same as no copy" -- and
its own history is this defect exactly: `tools/staging/repository_role_guard.py`
was untracked while `prepush_gate.py`, which invokes it, was tracked, so a clone
got a pre-push gate whose first dependency did not exist.

Why this is a separate file and not an edit to that one:
  * it belongs to another lane, and
  * it derives its set from BACKTICKED PATHS in two portal documents. This one
    derives from the IMPORT GRAPH. Same rule, different evidence, and the portal
    checker cannot see a Python import any more than this one can see a
    backticked path.

Usage (PowerShell 7, from D:\\code\\ccode):

    python gui\\uidef\\check_clean_clone.py

Exit codes: 0 all tracked, 1 repo root not found, 2 one or more untracked.
Run it host-side. `git ls-files` is read-only and does not take the index lock,
but the sandbox rule is absolute for a reason.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


def repo_root() -> Path:
    for candidate in [HERE, *HERE.parents]:
        if (candidate / ".git").exists() and (candidate / "include" / "xbase.hpp").exists():
            return candidate
    print("check-clean-clone: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def tracked(root: Path, rel: str) -> bool:
    r = subprocess.run(["git", "--no-optional-locks", "ls-files", "--error-unmatch", rel],
                       cwd=root, capture_output=True, text=True)
    return r.returncode == 0


def main() -> int:
    root = repo_root()
    wanted: dict[str, set[str]] = {}
    for src in sorted(HERE.glob("*.py")):
        for name in IMPORT_RE.findall(src.read_text(encoding="utf-8", errors="replace")):
            if (HERE / (name + ".py")).is_file():
                wanted.setdefault(name + ".py", set()).add(src.name)

    bad = []
    for mod in sorted(wanted):
        rel = str((HERE / mod).relative_to(root)).replace("\\", "/")
        if not tracked(root, rel):
            bad.append((rel, sorted(wanted[mod])))

    print("check-clean-clone: %d local module(s) imported by gui/uidef" % len(wanted))
    if not bad:
        print("check-clean-clone: PASS -- every imported module is tracked")
        return 0
    for rel, importers in bad:
        print("check-clean-clone: UNTRACKED %s" % rel)
        print("    imported by: %s" % ", ".join(importers))
        print("    a clone gets the importer and not the import.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
