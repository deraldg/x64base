#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: manualgen
# layer: tool
# owns: the candidate-stage report of non-ASCII text flowing from source
#       contracts into the manual, attributed to the source that emits it
# project: project.x64base.runtime
# lane: full_stack_documentation
# owner: member.derald
# status: review-needed
"""check_harvest_ascii.py -- where does non-ASCII enter the manual, and from whom?

WHY THIS EXISTS, AND WHY IT IS NOT A BLOCKING GATE
--------------------------------------------------
On 2026-09-02 a commit was blocked by `check_house_style.py` over 9 non-ASCII
characters in the ACCEPTED manual: 3 x U+26A0 in the command reference README
and 6 x U+2192 in `commands/pshell.md`.

By then it was far too late to be useful. The Gate 4 apply had already written
those characters into the accepted manual, and the only two moves left were to
bypass the gate or to unwind and redo the entire cycle. The bypass is what
happened (OI-026).

Worse, the demand was unsatisfiable in its own terms. Both files are GENERATED.
Editing a rendered page to please a checker is undone by the next regeneration
-- enforcement on the far bank, the missing-plank shape NORTH_STAR names. The
characters do not live in the page; they live in the renderer and in the source
contracts the harvest carries.

So the rule moved upstream. `check_house_style.py` now excludes generated
manualgen output, the renderer emits `(!)` instead of U+26A0, and THIS tool
reports what the harvest is still carrying, at candidate stage, attributed to
the source that emits it.

REPORT-ONLY, DELIBERATELY, AND EXIT 0 EVEN WHEN IT FINDS THINGS.

`check_house_style.py` earned this the hard way and wrote the reasoning down:
checking ADDED lines only, because "a gate that fails on day one because of
somebody else's decade of text is a gate that gets bypassed, and a bypassed gate
is worse than none because it looks like protection."

A candidate build has no notion of an added line -- the harvest is a snapshot,
not a diff. A hard gate here would go red on 28 pre-existing rows from the first
run and be switched off by the second. So this reports, names the owner of each
finding, and lets a human decide which source file is worth opening. When the
backlog is empty, THEN it can be made to block, and that is a decision with
evidence behind it rather than an aspiration.

    exit 0   always (report-only). --strict makes it exit 2 on any finding,
             for the day the backlog is clear and blocking is affordable.
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys
from pathlib import Path

# Keys are ESCAPED, not literal. This file names the characters it hunts, so
# writing them literally would make the tool a violation of the rule it reports
# on -- and `check_house_style.py` already solved this the same way.
NAMED = {
    "\u2014": "em-dash        -> --",
    "\u2013": "en-dash        -> --",
    "\u2018": "left quote     -> '",
    "\u2019": "right quote    -> '",
    "\u201c": "left dquote    -> \"",
    "\u201d": "right dquote   -> \"",
    "\u2192": "right arrow    -> ->",
    "\u2190": "left arrow     -> <-",
    "\u21d2": "double arrow   -> =>",
    "\u26a0": "warning sign   -> (!)",
    "\u00d7": "times          -> x",
    "\u2260": "not-equal      -> !=",
}


def describe(ch: str) -> str:
    return NAMED.get(ch, f"U+{ord(ch):04X}       -> ASCII equivalent")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--harvest", default="docs/manuals/developer/manualgen/harvested")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 2 on any finding. For when the backlog is clear.")
    a = ap.parse_args(argv)

    path = Path(a.repo_root).resolve() / a.harvest / "HELP_HELP_LINE.csv"
    if not path.is_file():
        print(f"harvest-ascii: no harvest at {a.harvest} -- nothing to check")
        return 0

    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        rows = list(csv.DictReader(handle))

    findings = [r for r in rows if any(ord(c) > 127 for c in r.get("TEXT", ""))]
    if not findings:
        print(f"harvest-ascii: PASS -- {len(rows)} harvest rows, none carry non-ASCII")
        return 0

    by_source: dict[str, list[dict]] = collections.defaultdict(list)
    for row in findings:
        by_source[row.get("SOURCE", "?").strip() or "?"].append(row)
    chars = collections.Counter(
        c for r in findings for c in r.get("TEXT", "") if ord(c) > 127)

    print(f"harvest-ascii: {len(findings)} of {len(rows)} harvest rows carry non-ASCII")
    print(f"  topics affected : {len(set(r.get('TOPIC', '') for r in findings))}")
    print("  characters:")
    for ch, count in chars.most_common():
        print(f"    {count:>4}  {describe(ch)}")
    print("  by producer:")
    for source, group in sorted(by_source.items(), key=lambda kv: -len(kv[1])):
        topics = sorted({r.get("TOPIC", "").strip() for r in group})
        print(f"    {len(group):>4}  {source:<16} {', '.join(topics[:6])}")
    print("")
    print("  These reach the manual through the harvest, so they must be fixed in the")
    print("  SOURCE CONTRACT that emits them. Editing a rendered page does not hold:")
    print("  the next regeneration writes the character back.")

    if a.strict:
        print("  --strict: failing.")
        return 2
    print("  Report-only. Nothing is blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
