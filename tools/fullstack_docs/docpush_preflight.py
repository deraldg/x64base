#!/usr/bin/env python3
"""docpush_preflight.py -- one-shot Phase 0/0.5 gate before a full-stack doc push.

The last few doc-push iterations learned to run the cheap, deterministic checks
FIRST, so contract/catalog gaps surface immediately instead of at commit time.
This runs them in one command:

  1. source_census.py            -- @dottalk.file coverage must be 100% (0 uncovered)  [HARD]
  2. command_catalog_sync check  -- website catalog matches the registry (no drift)    [HARD]
  3. house-style ASCII scan      -- no non-ASCII (em-dash etc.) in this plan doc        [advisory]
  4. help_build_order_check.py   -- catalogs -> exe -> LEGACY -> store, in that order   [HARD]
  5. help_store_check.py         -- every HELP_LINE row names a topic (the JOIN)        [HARD]
  6. program_freshness_check.py  -- EVERY program the push runs is newer than its source [HARD]

Steps 4 and 5 were added 2026-08-25. They exist because flush v5 lost cycles to
four failures a transcript CANNOT show, all of them ordering facts: a store
rebuilt by an exe that predated the change; CMDHELP BUILD LEGACY and BUILD .
<src> passed as one -CommandLines array so only the first ran; an exe built from
a dirty worktree; and 2,757 HELP_LINE rows with a blank TOPICKEY that survived
five rebuilds while CMDHELPCHK reported OK (AIF-126). Steps 1-3 check CONTENT.
Steps 4-5 check ORDER and the join. Neither half sees the other's failures.

Step 6 was added 2026-08-26, from the owner's structural note: "so step 1 is
really compile all of the programs first in the fullstack push". Step 4 answers
that for the ENGINE only. The push also runs `metacollect` -- a separate CMake
target, default OFF -- whose staleness nothing was testing until it was checked
BY HAND during v6 Phase 5, and a hand check is not a gate. Step 6 also reports
the version guard each Python program declares, because on the same day a
`!= (3, 12)` EQUALITY guard made a runnable tool read as blocked.

Exit 0 only if the two HARD checks pass. Steps 1 and 2 shell out to the existing
tools with the current interpreter, so run this on a host with Python 3.12
(command_catalog_sync guards on 3.12). See
docs/maintenance/lanes/full_stack_documentation/FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md
(Phase 0.5).

Usage:
  python tools/fullstack_docs/docpush_preflight.py --root D:/code/ccode \
      --catalog D:/dev/x64base-site/content/docs/dottalk/command-catalog.mdx
  python tools/fullstack_docs/docpush_preflight.py --root D:/code/ccode   # skip catalog check

Owner: member.derald . lane: AIF-088 . status: candidate
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

PLAN_REL = ("docs/maintenance/lanes/full_stack_documentation/"
            "FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md")


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--catalog", default=None,
                    help="site command-catalog.mdx (omit to skip the catalog check)")
    ap.add_argument("--no-git", action="store_true",
                    help="pass through to step 4: skip the worktree-binding check")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    py = sys.executable
    fails = []

    print("== docpush preflight ==")

    # 1. contract coverage (HARD)
    rc, out = _run([py, str(root / "tools/fullstack_docs/source_census.py"),
                    "--root", str(root)])
    cov = re.search(r"coverage:\s*([\d.]+)%", out)
    unc = re.search(r"uncovered:\s*(\d+)", out)
    print("  1. @dottalk.file coverage: %s%%  (uncovered=%s)"
          % (cov.group(1) if cov else "?", unc.group(1) if unc else "?"))
    if not (cov and float(cov.group(1)) >= 100.0 and unc and unc.group(1) == "0"):
        fails.append("source_census: coverage < 100%% or uncovered files remain")

    # 2. catalog drift (HARD, if a catalog path was given)
    if a.catalog:
        rc, out = _run([py, str(root / "tools/fullstack_docs/command_catalog_sync.py"),
                        "check", "--source-root", str(root), "--catalog", a.catalog])
        line = next((l for l in out.splitlines() if "command_catalog check" in l),
                    out.strip().splitlines()[-1] if out.strip() else "(no output)")
        print("  2. catalog: %s" % line)
        if rc != 0:
            fails.append("command_catalog_sync check: catalog drifted from source")
    else:
        print("  2. catalog: skipped (no --catalog)")

    # 3. house-style ASCII on the plan doc (advisory)
    plan = root / PLAN_REL
    if plan.is_file():
        bad = [i for i, l in enumerate(
            plan.read_text(encoding="utf-8", errors="replace").splitlines(), 1)
            if any(ord(c) > 127 for c in l)]
        print("  3. plan ASCII: %s (advisory)"
              % ("clean" if not bad else "non-ASCII on lines " + ",".join(map(str, bad))))

    # 4. build order: catalogs -> exe -> LEGACY -> store (HARD)
    cmd = [py, str(root / "tools/coordination/help_build_order_check.py")]
    if a.no_git:
        cmd.append("--no-git")
    rc, out = _run(cmd)
    for line in out.splitlines():
        if line.strip().startswith(("PASS", "FAIL", "WARN", "skip")):
            print("  4. %s" % line.strip())
    if rc == 1:
        fails.append("help_build_order_check: build/store ordering is wrong "
                     "-- see the FAIL lines above")
    elif rc not in (0, 1):
        print("  4. build order: could not run (rc=%d)" % rc)

    # 5. store join: every HELP_LINE row names a topic (HARD)
    rc, out = _run([py, str(root / "tools/coordination/help_store_check.py")])
    line = next((l for l in out.splitlines() if l.startswith("RESULT:")), "(no output)")
    print("  5. store join: %s" % line)
    if rc == 1:
        fails.append("help_store_check: the store has unreachable rows "
                     "-- CMDHELPCHK cannot see this, it checks one table at a time")

    # 6. every program the push runs is newer than its sources (HARD)
    rc, out = _run([py, str(root / "tools/coordination/program_freshness_check.py"),
                    "--root", str(root)])
    for line in out.splitlines():
        s = line.strip()
        if s.startswith(("PASS", "FAIL", "skip", "ERROR", "note", "NOTE", "ok", "none")):
            print("  6. %s" % s)
    if rc == 1:
        fails.append("program_freshness_check: a program the push runs is OLDER "
                     "than its sources -- it would report the tree as it was "
                     "BEFORE the change under test")
    elif rc not in (0, 1):
        print("  6. program freshness: could not measure (rc=%d)" % rc)

    print()
    if fails:
        print("PREFLIGHT FAIL:")
        for f in fails:
            print("  - " + f)
        return 2
    print("PREFLIGHT PASS -- Phase 0/0.5 foundation is clean; proceed to Phase 1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
