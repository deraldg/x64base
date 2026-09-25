#!/usr/bin/env python3
"""verified_search.py -- a search that cannot report a false negative.

WHY THIS EXISTS
---------------
Empty output from a search that did not FINISH is not evidence of absence.
That sentence is already written down in four places in this repository:

  * CLAUDE.md          -- walk the portal before you scan
  * PORTAL_SEARCH_MAP_V1.md, line 8 -- "broad find/grep over the tree is slow
                          (worse across the mount -- it times out)"
  * HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md, section 8 -- the 2026-08-10
                          incident: a timed-out grep reported as NOT FOUND
  * proof.golden_rule_verify_before_assert

On 2026-09-24 an agent was asked the SAME question that produced that section
("look up hangman"), ran a broad `find` across three mounts, got empty output
because the command timed out, and was one recalled detail away from reporting
NOT FOUND a second time. Four layers of correct, delivered, auto-injected
guidance did not prevent the repeat.

PREPUSH_GATE_REFERENCE_V1.md measured the difference: obligations carrying a
gate held 83-94 percent; the one without a gate held 33. So this is the gate.
It is deliberately small and has no dependencies.

WHAT IT GUARANTEES
------------------
Exactly one verdict line is printed, always, and the three cases are not
confusable:

    FOUND        -- n matches, search completed
    NO MATCHES   -- search COMPLETED and found nothing (this IS evidence)
    INCOMPLETE   -- timed out; the result is NOT evidence of absence

Exit codes: 0 found, 1 no matches (completed), 2 incomplete, 3 bad usage.
A caller that checks the exit code cannot mistake 2 for 1.

USAGE
-----
    python3 tools/search/verified_search.py hangman
    python3 tools/search/verified_search.py hangman --names-only
    python3 tools/search/verified_search.py "FieldRef::eval" --paths src include
    python3 tools/search/verified_search.py hangman --timeout 120

Default paths are the documentation and registry trees, which is where a
"where is X" question is nearly always answered. Widen deliberately with
--paths; the tool tells you what it searched and what it skipped.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SEARCH_MAP = REPO_ROOT / "labtalk" / "ai_portal" / "PORTAL_SEARCH_MAP_V1.md"

# Where a "where is X" question is usually answered. Not the whole tree: the
# whole tree is what times out, which is the defect this tool exists for.
DEFAULT_PATHS = ["docs", "labtalk", "tools", "coordination"]

# Never worth scanning, always expensive.
PRUNE = {".git", "build", "build-wsl", "node_modules", "__pycache__",
         ".venv312", "out", ".next", "vcpkg_installed"}


def consult_map(term: str) -> list[str]:
    """The portal rule is 'go straight there, do not scan'. Check first."""
    if not SEARCH_MAP.is_file():
        return []
    rows = []
    needle = term.lower()
    for line in SEARCH_MAP.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("|") and needle in line.lower():
            rows.append(line.strip())
    return rows


def build_cmd(term: str, paths: list[str], names_only: bool, regex: bool) -> list[str]:
    if names_only:
        cmd = ["find", *paths]
        for d in sorted(PRUNE):
            cmd += ["-name", d, "-prune", "-o"]
        cmd += ["-iname", f"*{term}*", "-print"]
        return cmd
    cmd = ["grep", "-r", "-n", "-I"]
    cmd.append("-E" if regex else "-F")
    cmd.append("-i")
    for d in sorted(PRUNE):
        cmd += [f"--exclude-dir={d}"]
    cmd += ["--", term, *paths]
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("term", help="text or filename fragment to look for")
    ap.add_argument("--paths", nargs="*", default=None,
                    help=f"roots to search (default: {' '.join(DEFAULT_PATHS)})")
    ap.add_argument("--names-only", action="store_true",
                    help="match FILENAMES instead of file contents")
    ap.add_argument("--regex", action="store_true",
                    help="treat term as an extended regex (default: literal)")
    ap.add_argument("--timeout", type=int, default=90,
                    help="seconds before the search is declared INCOMPLETE")
    ap.add_argument("--max-hits", type=int, default=60)
    ap.add_argument("--no-map", action="store_true",
                    help="skip the portal search-map consultation")
    a = ap.parse_args()

    os.chdir(REPO_ROOT)
    paths = a.paths if a.paths else DEFAULT_PATHS
    missing = [p for p in paths if not Path(p).exists()]
    if missing:
        print(f"BAD USAGE -- path(s) do not exist under {REPO_ROOT}: {', '.join(missing)}")
        return 3

    if not a.no_map:
        rows = consult_map(a.term)
        if rows:
            print("PORTAL SEARCH MAP already has a row for this -- go there, do not scan:")
            for r in rows[:5]:
                print(f"  {r}")
            print()

    cmd = build_cmd(a.term, paths, a.names_only, a.regex)
    started = time.monotonic()
    timed_out = False
    out = ""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout)
        out = proc.stdout
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
    elapsed = time.monotonic() - started

    hits = [ln for ln in out.splitlines() if ln.strip()]

    print(f"searched : {' '.join(paths)}")
    print(f"mode     : {'filenames' if a.names_only else 'contents'}"
          f"  term={a.term!r}  pruned={len(PRUNE)} dirs")
    print(f"elapsed  : {elapsed:.1f}s of {a.timeout}s budget")
    print()

    for ln in hits[:a.max_hits]:
        print(f"  {ln}")
    if len(hits) > a.max_hits:
        print(f"  ... {len(hits) - a.max_hits} more")
    if hits:
        print()

    # The verdict. Exactly one of three, never ambiguous.
    if timed_out:
        print(f"VERDICT: INCOMPLETE -- the search did NOT finish within {a.timeout}s.")
        print("         Any empty or short result above is NOT evidence of absence.")
        print("         Narrow --paths, or raise --timeout, and run it again.")
        if hits:
            print(f"         ({len(hits)} partial match(es) were seen before the cutoff.)")
        return 2
    if not hits:
        print(f"VERDICT: NO MATCHES -- search COMPLETED in {elapsed:.1f}s.")
        print("         This is a real negative for the paths listed above.")
        print("         It says nothing about paths that were not searched.")
        return 1
    print(f"VERDICT: FOUND {len(hits)} match(es) -- search completed in {elapsed:.1f}s.")
    print("         If locating this cost you a scan, ADD A ROW to")
    print("         labtalk/ai_portal/PORTAL_SEARCH_MAP_V1.md (its own maintenance rule).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
