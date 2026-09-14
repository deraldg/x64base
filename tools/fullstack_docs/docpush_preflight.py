#!/usr/bin/env python3
"""docpush_preflight.py -- one-shot Phase 0/0.5 gate before a full-stack doc push.

The last few doc-push iterations learned to run the cheap, deterministic checks
FIRST, so contract/catalog gaps surface immediately instead of at commit time.
This runs them in one command:

  1. source_census.py            -- @dottalk.file coverage must be 100% (0 uncovered)  [HARD]
  1b. audit_contracts.py         -- helper-aware usage and dotref coverage [measure HARD; debt advisory]
  2. command_catalog_sync check  -- website catalog matches the registry (no drift)    [HARD]
  3. house-style ASCII scan      -- no non-ASCII (em-dash etc.) in this plan doc        [advisory]
  4. help_build_order_check.py   -- catalogs -> exe -> LEGACY -> store, in that order   [HARD]
  5. help_store_check.py         -- every HELP_LINE row names a topic (the JOIN)        [HARD]
  6. program_freshness_check.py  -- EVERY program the push runs is newer than its source [HARD]
  6b. metacollect is BUILT       -- Phase 5's exe must exist, not merely be fresh   [HARD]
  7. harvest freshness (E5)      -- the CANONICAL harvest matches the live HELP/META store [HARD]
  8. contract drift              -- every source usage contract is in the store, unchanged  [HARD]

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

Steps 7 and 8 were added 2026-09-14, and step 7 is here because the run that
added it had already been fooled. DOCFLUSH-20260914-001 re-exported the harvest,
then built the whole manual candidate chain -- reference, disposition, command
reference, publication structure -- and every stage reported PASS. All four were
built from the PREVIOUS harvest. Exporting writes a CANDIDATE workspace;
promoting it into manualgen/harvested/ is a SEPARATE AUTHORIZED GATE, by the
input contract's own design, and nothing between the two acts checked which one
manualgen would read. The tell was in the output and looked like success:
`lines=29700/29700`, a perfect match, because the old harvest was being compared
with itself.

THIS IS THE SAME CLASS AS STEPS 4 AND 5 -- an ordering fact, invisible in a
transcript, producing output that looks correct. The steward's own summary of
the export ("E5 cleared") was wrong for twenty minutes and nothing could
contradict it. A checklist could not have caught this; the checklist was
followed. A clock catches it.

Step 6b exists because step 6 reports an UNBUILT program as `skip`, and a skip
does not fail. That is right for the general tool and wrong for a doc push:
`metacollect` is Phase 5, its CMake option DOTTALK_BUILD_METACOLLECT DEFAULTS
TO OFF, and a fresh configure therefore drops the target. The push would then
run six green steps and silently omit a phase. Owner, 2026-09-14: "those should
be obvious recorded steps in the fullstack document push, we should not be able
to skip steps." A step that can vanish without a finding is a step that is not
in the push.

Step 8 is the owner's standing ask from 2026-09-13 -- "the command contract
inventory ... a curated part of the fullstack doc push in the harvest phase,
reproduceable". It was reproducible from the day it was written and still
depended on someone remembering to type it. Now it does not.

Exit 0 only if all HARD checks pass. Steps 1 and 2 shell out to the existing
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

# The harvest manualgen actually reads. Export runs land in export_runs/<id>/
# and are NOT this path until a promotion gate moves them.
CANONICAL_HARVEST_REL = "docs/manuals/developer/manualgen/harvested"

# The live HELP store the engine writes and the manual is supposed to describe.
HELP_STORE_REL = "dottalkpp/data/help"


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def contract_audit_summary(output):
    """Parse the stable summary emitted by tools/selfdoc/audit_contracts.py."""
    match = re.search(
        r"^SUMMARY file_missing=(\d+) usage_missing=(\d+) "
        r"unregistered=(\d+) helpers=(\d+)$",
        output,
        re.MULTILINE,
    )
    if not match:
        return None
    return {
        "file_missing": int(match.group(1)),
        "usage_missing": int(match.group(2)),
        "unregistered": int(match.group(3)),
        "helpers": int(match.group(4)),
    }


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

    # 1b. command-contract coverage (advisory during the observation cycle)
    rc, out = _run([py, str(root / "tools/selfdoc/audit_contracts.py"),
                    "--root", str(root)])
    summary = contract_audit_summary(out)
    if summary:
        problems = (summary["file_missing"] + summary["usage_missing"]
                    + summary["unregistered"])
        print("  1b. command contracts: file_missing=%d usage_missing=%d "
              "unregistered=%d helpers=%d (%s)"
              % (summary["file_missing"], summary["usage_missing"],
                 summary["unregistered"], summary["helpers"],
                 "clean" if problems == 0 else "advisory debt"))
    else:
        print("  1b. command contracts: unavailable (rc=%d)" % rc)
        fails.append("audit_contracts: command-contract coverage could not be measured")

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

    # 6b. metacollect must be BUILT, not merely fresh (HARD)
    #
    # Step 6 prints "skip <name> not built" and does not fail -- correct for a
    # general freshness tool, wrong for a push that has metacollect as Phase 5.
    # DOTTALK_BUILD_METACOLLECT defaults OFF, so this is one reconfigure away
    # at any time.
    if re.search(r"^\s*skip\s+metacollect\b", out, re.MULTILINE):
        print("  6b. metacollect: NOT BUILT -- Phase 5 would be skipped silently")
        fails.append(
            "metacollect is not built. It is Phase 5 of the push and its CMake "
            "option DOTTALK_BUILD_METACOLLECT defaults to OFF, so a fresh "
            "configure drops it. Build it: cmake -S . -B build "
            "-DDOTTALK_BUILD_METACOLLECT=ON, then cmake --build build "
            "--target metacollect --config Release.")
    elif re.search(r"^\s*(PASS|FAIL)\s+metacollect\b", out, re.MULTILINE):
        print("  6b. metacollect: built (freshness reported by step 6)")
    else:
        print("  6b. metacollect: UNRUN -- step 6 said nothing about it")
        fails.append("metacollect: step 6 reported no verdict for it -- unrun "
                     "is not pass")

    # 7. the canonical harvest matches the live store (HARD)
    #
    # NOT the newest export run -- the CANONICAL one, because that is the only
    # workspace the manual candidate chain reads by default. An export that was
    # taken and never promoted leaves this FAILING, which is the correct and
    # useful answer.
    harvest = root / CANONICAL_HARVEST_REL
    if not harvest.is_dir():
        print("  7. harvest freshness: canonical workspace missing (%s)"
              % CANONICAL_HARVEST_REL)
        fails.append("harvest freshness: canonical workspace not found at "
                     + CANONICAL_HARVEST_REL)
    else:
        tool = root / "tools/fullstack_docs/check_help_meta_harvest_freshness.py"
        rc, out = _run([py, str(tool), "--repo-root", str(root),
                        "--workspace", str(harvest)])
        # A VERDICT IS ONLY A VERDICT IF THE TOOL SPOKE. `python <missing>` and
        # an import error both exit non-zero with no E5 line, and reporting
        # that as a stale harvest is G1's "unrun reported as a finding".
        line = next((l for l in out.splitlines() if l.startswith("E5 ")), None)
        if line is None:
            print("  7. harvest freshness: UNRUN -- no verdict (rc=%d)" % rc)
            print("     %s" % (out.strip().splitlines()[-1] if out.strip()
                               else "(no output)"))
            fails.append("harvest freshness: UNRUN (rc=%d) -- the check did not "
                         "report. Unrun is not pass, and it is not drift "
                         "either." % rc)
        else:
            print("  7. harvest freshness: %s" % line)
        if line is not None and rc == 1:
            for l in out.splitlines():
                if l.startswith("  "):
                    print("     %s" % l.strip())
            fails.append(
                "harvest freshness: the CANONICAL harvest does not match the "
                "live HELP/META store. Every manual candidate built now would "
                "describe the PREVIOUS store and report PASS while doing it. "
                "Export, then run the promotion gate "
                "(build_help_meta_harvest_promotion_plan.py -> "
                "apply_help_meta_harvest_promotion.py) -- exporting alone "
                "does not promote.")
        elif line is not None and rc not in (0, 1):
            print("     UNRUN -- unexpected exit (rc=%d). Not a pass." % rc)
            fails.append("harvest freshness: unexpected exit (rc=%d)" % rc)

    # 8. contract drift: source usage contracts vs the saved store (HARD)
    store = root / HELP_STORE_REL
    if not store.is_dir():
        print("  8. contract drift: HELP store missing (%s)" % HELP_STORE_REL)
        fails.append("contract drift: HELP store not found at " + HELP_STORE_REL)
    else:
        rc, out = _run([py, str(root / "tools/fullstack_docs/"
                                       "contract_inventory.py"),
                        "drift", "--source-root", str(root),
                        "--store", str(store), "--limit", "10"])
        # contract_inventory exits 2 for DRIFT -- and so does the interpreter
        # for a missing script. Trust rc only when the tool printed a verdict.
        line = next((l for l in out.splitlines()
                     if l.startswith("CONTRACT DRIFT:")), None)
        if line is None:
            print("  8. contract drift: UNRUN -- no verdict (rc=%d)" % rc)
            print("     %s" % (out.strip().splitlines()[-1] if out.strip()
                               else "(no output)"))
            fails.append("contract drift: UNRUN (rc=%d) -- the check did not "
                         "report. Unrun is not pass, and an interpreter exit 2 "
                         "is not drift." % rc)
        else:
            print("  8. contract drift: %s" % line)
        if line is not None and rc == 2:
            for l in out.splitlines():
                if l.lstrip().startswith(("~", "+", "-")):
                    print("     %s" % l.strip())
            fails.append(
                "contract drift: the store no longer matches the usage "
                "contracts in source. Rebuild it (CMDHELP BUILD LEGACY, then "
                "CMDHELP BUILD . <src>) or account for each line above.")
        elif line is not None and rc not in (0, 2):
            print("     UNRUN -- unexpected exit (rc=%d). Not a pass." % rc)
            fails.append("contract drift: unexpected exit (rc=%d)" % rc)

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
