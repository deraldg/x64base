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

A THIRD CATEGORY, ADDED 2026-10-20: AGENT ASSETS -- everything under
`.claude/skills/` and `.claude/plugins/`. These are agent BEHAVIOUR, the same
class of thing as the entry documents, and a clone that does not get them runs
an agent with different instructions. Owner instruction the same day: the skills
and plugins we build for DotTalk++ belong in GitHub too.

This category is walked from DISK, not read out of the entry documents, and that
is deliberate twice over. First, a skill nobody thought to mention in the portal
is exactly the one that goes missing. Second, DOC_RE cannot see these paths at
all: its first character class excludes a dot, so a backticked
`.claude/skills/<name>/SKILL.md` never MATCHES rather than matching and being
mangled -- the same shape as the backslash hole recorded below, and widening the
pattern would move the document count in the same commit, which this file
refuses on principle.

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

# Agent behaviour that ships with the tree. Walked from disk; see the head of
# this file for why these are not derived from the entry documents.
AGENT_ASSET_ROOTS = (".claude/skills", ".claude/plugins")

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
            # DOC_RE's character class has no backslash, so a Windows-spelled
            # .md path is never MATCHED here rather than being matched and then
            # mangled. Narrower hole, different shape, deliberately not widened
            # in the same change: doing so would move the document count too,
            # and one measured fix per commit.
            docs.add(hit.lstrip("./"))
        for hit in SCRIPT_RE.findall(text):
            # NORMALIZE SEPARATORS FIRST, THEN STRIP. The reverse order was
            # silently discarding every Windows-spelled path in the portal, and
            # AI_README.md spells its scripts that way (`.\\run-erp.ps1`, line
            # 560). Worked through:
            #
            #   .\\run-erp.ps1  -lstrip("./")->  \\run-erp.ps1  -replace->  /run-erp.ps1
            #
            # -- a leading slash that matches nothing, so the is_file() filter
            # below dropped it without a word. 27 hits in the entry documents,
            # 10 survived. FOUR SCRIPTS THE PORTAL TELLS YOU TO RUN WERE
            # UNTRACKED WHILE THIS GATE REPORTED PASS: launch_portal.ps1,
            # run-cli.ps1, run-erp.ps1, run-pycrud.ps1.
            #
            # That is the 2026-07-31 defect described at the head of this file,
            # recurring inside the checker written to catch it. A guard whose
            # own input normalization drops the cases it exists for reports
            # PASS over a smaller set every time and never says the set shrank.
            scripts.add(hit.replace("\\", "/").lstrip("./"))

    docs = {f for f in docs if (root / f).is_file()}
    scripts = {f for f in scripts if (root / f).is_file()}
    return docs, scripts


def agent_assets(root: Path) -> list[str]:
    """Every file under the agent-asset roots, repo-relative, sorted.

    Returns [] when no root exists, and main() says so rather than printing a
    green. A zero that is not distinguished from a pass is how this repo's
    instruments have lied all autumn: seven greens in one week meant "I did not
    look".
    """
    found: list[str] = []
    for rel in AGENT_ASSET_ROOTS:
        base = root / rel
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                found.append(path.relative_to(root).as_posix())
    return found


def ignored(root: Path, paths: list[str]) -> set[str]:
    """Of `paths`, those git deliberately excludes.

    A gitignored asset is a DECISION, not a defect -- a personal settings file
    belongs to one clone. It is reported and never failed on. `check-ignore`
    EXITS 1 when nothing matches, which is the ordinary case, so only a code
    above 1 is an error.
    """
    if not paths:
        return set()
    out = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=root,
        input="\n".join(paths),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if out.returncode > 1:
        print("check: git check-ignore failed", file=sys.stderr)
        raise SystemExit(1)
    return {line.strip().replace("\\", "/") for line in out.stdout.splitlines() if line.strip()}


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
    assets = agent_assets(root)
    have = tracked(root)
    excluded = ignored(root, assets)

    missing_docs = sorted(docs - have)
    missing_scripts = sorted(scripts - have)
    missing_assets = sorted(a for a in assets if a not in have and a not in excluded)

    print(
        f"mandatory-tracked: {len(docs)} document(s), {len(scripts)} script(s) "
        f"and {len(assets)} agent asset(s) checked"
    )
    # SAY WHICH ROOTS WERE WALKED AND WHICH WERE NOT THERE. Zero assets from a
    # root that does not exist is a different fact from zero untracked ones.
    for rel in AGENT_ASSET_ROOTS:
        if (root / rel).is_dir():
            n = sum(1 for a in assets if a.startswith(rel + "/"))
            print(f"  agent assets: {rel}/ -- {n} file(s)")
        else:
            print(f"  agent assets: {rel}/ -- not present in this tree")
    for name in sorted(excluded):
        print(f"  agent assets: GITIGNORED (a decision, not a defect) {name}")

    if not missing_docs and not missing_scripts and not missing_assets:
        print("mandatory-tracked: PASS -- every declared file is tracked")
        return 0

    print(
        "mandatory-tracked: FAIL -- "
        f"{len(missing_docs)} document(s), {len(missing_scripts)} script(s) "
        f"and {len(missing_assets)} agent asset(s) UNTRACKED"
    )
    for name in missing_scripts:
        print(f"  UNTRACKED SCRIPT  {name}   <-- a gate that will not run downstream")
    for name in missing_docs:
        print(f"  UNTRACKED DOC     {name}")
    for name in missing_assets:
        print(f"  UNTRACKED ASSET   {name}   <-- agent behaviour a clone will not get")
    print("")
    print("These are invisible to a clone. An agent onboarding from GitHub cannot")
    print("read the documents and cannot run the gates. Commit them, or stop")
    print("declaring them mandatory. An untracked script is the worse case: it")
    print("does not error, it silently does not exist.")
    if missing_assets:
        print("")
        print("AN UNTRACKED SKILL OR PLUGIN IS THE SAME DEFECT WEARING A DIFFERENT")
        print("HAT. The tree's agent reads it, a clone's agent does not, and nothing")
        print("else in the toolchain notices: 100a43170 shipped a skill whose content")
        print("was 41 lines stale and every gate passed. Commit it, or gitignore it")
        print("on purpose so this check reports it as a decision.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
