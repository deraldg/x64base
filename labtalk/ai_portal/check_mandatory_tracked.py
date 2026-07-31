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

# Documents the portal points at, inline: `docs/agents/CURRENT_TARGET.md`
DOC_RE = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.md)`")

# Scripts the portal instructs you to RUN. These matter more than the documents:
# a missing document can be worked around, a missing gate cannot. Found the hard
# way on 2026-07-31 -- `tools/staging/repository_role_guard.py` was untracked
# while `prepush_gate.py`, which invokes it, was tracked. A clone therefore got a
# pre-push gate whose first dependency did not exist. The first version of this
# checker looked only at backticked .md paths and missed it.
SCRIPT_RE = re.compile(
    r"(?:^|[\s`\"'(])((?:[A-Za-z0-9_.-]+[/\\])*[A-Za-z0-9_.-]+\.(?:py|ps1|sh))"
)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "AI_README.md").exists():
            return candidate
    print("check: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def declared(root: Path) -> tuple[set[str], set[str]]:
    """Return (documents, scripts) the entry documents declare, that exist on disk.

    Reported separately because they fail differently. A missing document can be
    worked around by reading something else; a missing gate silently does not run.
    """
    docs: set[str] = set(ENTRY_DOCS) | set(ALWAYS_READ)
    scripts: set[str] = set()

    for name in ENTRY_DOCS:
        path = root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for hit in DOC_RE.findall(text):
            docs.add(hit.lstrip("./"))
        for hit in SCRIPT_RE.findall(text):
            scripts.add(hit.lstrip("./").replace("\\", "/"))

    docs = {f for f in docs if (root / f).is_file()}
    scripts = {f for f in scripts if (root / f).is_file()}
    return docs, scripts


def tracked(root: Path) -> set[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if out.returncode != 0:
        print("check: git ls-files failed", file=sys.stderr)
        raise SystemExit(1)
    return set(out.stdout.split())


def main() -> int:
    root = repo_root()
    docs, scripts = declared(root)
    have = tracked(root)

    missing_docs = sorted(docs - have)
    missing_scripts = sorted(scripts - have)

    print(
        f"mandatory-tracked: {len(docs)} document(s) and {len(scripts)} script(s) checked"
    )
    if not missing_docs and not missing_scripts:
        print("mandatory-tracked: PASS -- every declared file is tracked")
        return 0

    print(
        "mandatory-tracked: FAIL -- "
        f"{len(missing_docs)} document(s) and {len(missing_scripts)} script(s) UNTRACKED"
    )
    for name in missing_scripts:
        print(f"  UNTRACKED SCRIPT  {name}   <-- a gate that will not run downstream")
    for name in missing_docs:
        print(f"  UNTRACKED DOC     {name}")
    print("")
    print("These are invisible to a clone. An agent onboarding from GitHub cannot")
    print("read the documents and cannot run the gates. Commit them, or stop")
    print("declaring them mandatory. An untracked script is the worse case: it")
    print("does not error, it silently does not exist.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
