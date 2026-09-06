#!/usr/bin/env python3
"""Portal check: a header that declares `status: supported` must be reachable.

WHAT THIS SEES THAT NOTHING ELSE DOES. Every other gate in this house checks a
POINTER against a TARGET: `cited-paths` finds a document citing a path it does
not ship, `mandatory-tracked` finds a declared file that is not tracked,
`manual-link-integrity` finds a link with no page. This one checks the inverse
-- a file that ships, is tracked, declares itself supported, and that NO
TRANSLATION UNIT CAN SEE. It is not a widow; it is the thing no pointer reaches.

MEASURED 2026-09-06: 61 of 348 headers under include/ are unreachable from every
.cpp in src/ and tests/, following #include transitively. 58 of the 61 declare
`status: supported`. The one that declares `reserved` is include/devref.hpp, and
the normalization gate prints "devref (empty) status: reserved -- empty by
declaration" on every commit -- so the vocabulary ALREADY HAS the right answer
for a declared-but-unbuilt file, and 58 files are not using it.

REACHABILITY IS TRANSITIVE AND THAT IS NOT A DETAIL. A first cut counted only
direct .cpp includes and reported 78. Seventeen of those are reached THROUGH
another header -- xindex/index_backend.hpp, dt/data/cell.hpp, memo/dtx_format.hpp
among them -- so a naive check names working files and gets itself switched off.
The graph is walked from every source, through headers, to fixpoint.

UNREACHABLE IS NOT THE SAME AS WRONG, WHICH IS WHY THIS IS ADVISORY.
include/snx/snx.hpp is in the set and its own purpose block opens "Future custom
compound index family (peer to CNX/CDX)" -- a specification written ahead of its
implementation, entirely deliberate. Some fraction of the other 57 will be the
same, and this check cannot tell which. It reports; it does not judge.

WHY IT NEVER BLOCKS, and this is argued rather than assumed:

  1. THE BACKLOG IS 61. A blocking gate would fail every commit in the repo
     until someone triaged all of them, which is how a gate gets disabled
     instead of obeyed.
  2. HEADER-BEFORE-IMPLEMENTATION IS A LEGITIMATE COMMIT. Writing the interface
     in one commit and the .cpp in the next is normal practice, and a gate that
     forbids it teaches people to bundle unrelated work into one commit.
  3. THE VOCABULARY IS NOT SETTLED. What `status: supported` asserts is not
     written down anywhere this session could find, and a broad search of docs/
     times out on the mounted worktree and returns empty rather than erroring --
     so absence is not evidence. Blocking on an unread contract is guessing.

So it behaves like `open-items` and the R-number gate: it says the number out
loud, every commit, and names what CHANGED. Promotion to blocking is an owner
call after the 61 are triaged -- the same shape as a regression spec staying
explicit-run until it soaks.

THE BASELINE IS WHAT MAKES IT USEFUL RATHER THAN NOISY. A bare count of 61
scrolls past. `header_reachability_baseline.txt` holds the known set, so this
check can say the two things that are actually actionable:

  NEW   -- unreachable and not in the baseline. Someone added a header no build
           can see, or removed the last include of one. This is the drift.
  FIXED -- in the baseline and now reachable. Drop it; a baseline that only ever
           grows stops describing anything.

SCOPE. The walk reads ~950 files, so it runs only when the change set touches a
header or a source. A documentation commit prints one line and returns.

Exit: 0 clean or out of scope, 1 advisory. NEVER 2 -- see above.

OBSERVED ON THE REAL TREE 2026-09-06, both paths:

  in 385563746, whose change set was two tools/staging files --
    "no headers or sources in scope -- nothing to check"      (scope guard)

  against 7f9bc25db~1, a range reaching back past source commits --
    "348 header(s), 287 reachable, 61 UNREACHABLE
     (58 declare status: supported)
     PASS -- unreachable set matches the baseline exactly."   (the walk)

The second run also settles the cost question empirically. It was priced by
ANALOGY when wired in -- the R-number gate already walks 2054 files every
commit and this walks 950 -- and it returns promptly on the host disk. The
two-minute figure seen while authoring it was the mounted worktree, not the
algorithm.
"""

import os
import re
import subprocess
import sys
from collections import defaultdict

INCLUDE_DIR = "include"
SOURCE_DIRS = ("src", "tests")
SKIP_DIRS = {"AIPortal"}          # session archives, not build input
HDR_EXT = (".hpp", ".h")
SRC_EXT = (".cpp", ".cc")
BASELINE = os.path.join("tools", "staging", "header_reachability_baseline.txt")

INCLUDE_RE = re.compile(r'#include\s+"([^"]+)"')
STATUS_RE = re.compile(r"^// status:\s*(\S+)", re.M)


def git(args):
    out = subprocess.run(["git", "--no-optional-locks"] + args,
                         capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


def in_scope(range_spec):
    if range_spec:
        names = git(["diff", "--name-only", "--diff-filter=ACMR", range_spec])
    else:
        names = git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    return [p for p in names.splitlines()
            if p.endswith(HDR_EXT) or p.endswith(SRC_EXT)]


def read(path, limit=None):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit) if limit else fh.read()
    except OSError:
        return ""


def walk(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
        for f in files:
            yield os.path.join(root, f).replace("\\", "/")


def main(argv):
    range_spec = argv[0] if argv else None

    if not in_scope(range_spec):
        print("header-reachability: no headers or sources in scope -- nothing to check")
        return 0

    if not os.path.isdir(INCLUDE_DIR):
        print("header-reachability: no include/ directory -- nothing to check")
        return 0

    headers = {}
    for p in walk(INCLUDE_DIR):
        if p.endswith(HDR_EXT):
            m = STATUS_RE.search(read(p, 1200))
            headers[p] = m.group(1) if m else "(none)"

    by_base = defaultdict(list)
    for p in headers:
        by_base[os.path.basename(p)].append(p)

    def resolve(spelling):
        s = spelling.replace("\\", "/")
        direct = INCLUDE_DIR + "/" + s
        if direct in headers:
            return direct
        tail = [p for p in headers if p.endswith("/" + s)]
        if len(tail) == 1:
            return tail[0]
        # A bare basename resolves only when it is UNAMBIGUOUS. Two headers of
        # the same name would otherwise let one vouch for the other.
        cand = by_base.get(os.path.basename(s), [])
        return cand[0] if len(cand) == 1 else None

    seeds = [p for base in SOURCE_DIRS if os.path.isdir(base)
             for p in walk(base) if p.endswith(SRC_EXT)]

    reach, stack = set(), []
    for s in seeds:
        for sp in INCLUDE_RE.findall(read(s)):
            r = resolve(sp)
            if r and r not in reach:
                reach.add(r)
                stack.append(r)
    while stack:
        for sp in INCLUDE_RE.findall(read(stack.pop())):
            r = resolve(sp)
            if r and r not in reach:
                reach.add(r)
                stack.append(r)

    unreachable = sorted(p for p in headers if p not in reach)

    base_set = set()
    have_baseline = os.path.exists(BASELINE)
    if have_baseline:
        base_set = {ln.strip() for ln in read(BASELINE).splitlines()
                    if ln.strip() and not ln.startswith("#")}

    new = [p for p in unreachable if p not in base_set]
    fixed = sorted(base_set - set(unreachable))

    supported = sum(1 for p in unreachable if headers[p] == "supported")
    print("header-reachability: %d header(s), %d reachable, %d UNREACHABLE "
          "(%d declare status: supported)"
          % (len(headers), len(reach), len(unreachable), supported))

    if not have_baseline:
        print("  baseline %s is absent -- reporting the whole set as the backlog."
              % BASELINE)
        for p in unreachable:
            print("    %-14s %s" % (headers[p], p))
        return 1

    rc = 0
    if new:
        rc = 1
        print("  NEW -- unreachable and not in the baseline:")
        for p in new:
            print("    %-14s %s" % (headers[p], p))
        print("  Either a header arrived that no build can see, or the last "
              "include of one was removed. If it is deliberate (a spec written "
              "ahead of its implementation, as include/snx/snx.hpp is), say so "
              "in its `status:` and add it to the baseline.")
    if fixed:
        rc = 1
        print("  FIXED -- in the baseline and now reachable, drop these lines:")
        for p in fixed:
            print("    %s" % p)

    if rc == 0:
        print("  PASS -- unreachable set matches the baseline exactly.")
    else:
        print("\n  ADVISORY -- the unreachable-header set moved. NOT blocking; "
              "the backlog is a known %d and header-before-implementation is a "
              "legitimate commit. Update %s when the move is intended."
              % (len(base_set), BASELINE))
    return rc


if __name__ == "__main__":
    sys.exit(main([a for a in sys.argv[1:] if not a.startswith("-")]))
