#!/usr/bin/env python3
"""docpush_preflight.py -- one-shot Phase 0/0.5 gate before a full-stack doc push.

The last few doc-push iterations learned to run the cheap, deterministic checks
FIRST, so contract/catalog gaps surface immediately instead of at commit time.
This runs them in one command:

  1. source_census.py            -- @dottalk.file coverage must be 100% (0 uncovered)  [HARD]
  2. command_catalog_sync check  -- website catalog matches the registry (no drift)    [HARD]
  3. house-style ASCII scan      -- no non-ASCII (em-dash etc.) in this plan doc        [advisory]

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
