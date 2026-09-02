#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: manualgen
# layer: tool
# owns: the report-only comparison between the status a command DECLARES in its
#       @dottalk.usage contract and the status the accepted manual PUBLISHES
# project: project.x64base.runtime
# lane: full_stack_documentation
# owner: member.derald
# status: review-needed
"""check_contract_status_drift.py -- does the manual publish what the source declares?

THE FINDING THIS TOOL EXISTS TO KEEP MEASURED
---------------------------------------------
Measured 2026-09-02: of the published commands that ALSO declare a status in
their own `@dottalk.usage` contract, 33 DISAGREE with the manual -- and every
single disagreement runs the same direction. The manual says `supported`; the
contract says `developer`, `experimental`, `stub`, `deprecated`,
`sample-extension` or `implementation-shim`.

    LMDB_UTIL     manual: supported    contract: deprecated
    TVISION       manual: supported    contract: stub
    AREA51        manual: supported    contract: developer
    SQL           manual: supported    contract: experimental

That is the NORTH_STAR missing-plank signature stated plainly: a fact wrong in
more than one place at once. Status lives in the authored contract AND in
dotref/catalog, the manual reads the catalog, and nothing compares them.

AREA51 IS THE CANARY, and it is worth knowing before reading the numbers. Its
own contract prose already says: "It read `supported` until 2026-08-30 while THIS
PARAGRAPH already called it a developer probe." The author caught this on one
command and wrote it down. The systemic count is 33.

WHY THE NUMBER MIGHT NOT MEAN WHAT IT LOOKS LIKE
------------------------------------------------
Read honestly, there are two explanations and this tool does not choose:

  1. DRIFT. The catalog is stale or the contract is, and they should agree.
  2. TWO AXES, ONE WORD. Catalog `supported` may mean "registered and
     dispatchable"; contract `status:` may mean maturity and intent. Both true,
     different questions, same word.

The second is likely the deeper one -- 242 contracts use 24 distinct status
values, which is one field answering five questions (audience, completeness,
mechanism, lifecycle, process). Glossary rows TERM.CONTRACT.AUDIENCE,
TERM.CONTRACT.COMPLETENESS, TERM.CONTRACT.LIFECYCLE and TERM.CONTRACT.SUPPORTED
propose splitting them; they are GREEN_TENTATIVE and awaiting an owner ruling as
of 2026-09-02.

So this REPORTS and groups by the proposed axis. It does not rewrite a contract,
does not touch the manual, and does not assert which side is right.

    exit 0   report-only, always (the default)
    exit 2   with --strict, if any command disagrees

`--strict` is for after the vocabulary is ruled on. Blocking today would go red
on 33 pre-existing rows from the first run and be switched off by the second,
which is the failure `check_house_style.py` documented and avoided.
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

# The PROPOSED axes (glossary, GREEN_TENTATIVE 2026-09-02). Grouping by these
# turns "33 disagreements" into "which question was the contract answering?",
# which is the actionable form. Values are the 24 observed in the tree.
AXIS = {
    "audience": {"developer", "dev-tool", "dev-canary", "sample-extension",
                 "backend-helper", "supplemental", "documentation-example",
                 "implementation-helper"},
    "completeness": {"experimental", "stub", "supported-stub",
                     "supported-stub-mixed", "supported-conditional",
                     "implementation-present", "placeholder-shim"},
    "mechanism": {"implementation-shim", "compatibility-shim",
                  "compatibility-alias", "active"},
    "lifecycle": {"deprecated", "deprecated-compat"},
    "process": {"review-needed", "document-control-readonly"},
}
DEFAULT_MANUAL = ("docs/manuals/developer/manualgen/published/"
                  "developer_manual_publication_v1/command_reference_v1/README.md")
ROW = re.compile(r"\|\s*\d+\s*\|\s*\[([^\]]+)\]\([^)]+\)[^|]*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`")


def axis_of(value: str) -> str:
    for name, values in AXIS.items():
        if value in values:
            return name
    return "unclassified"


def contract_statuses(root: Path) -> dict[str, set[tuple[str, str]]]:
    """KEY -> {(status, source file)}. Parsed line-wise, NOT with a windowed regex.

    An earlier version used `@dottalk.usage v1(.{0,900}?)(?=@dottalk\\.|\\Z)` and
    silently missed every contract whose block ran past 900 characters -- SQLHELP
    among them, the very command being investigated. It reported 11 contracts
    where there are 242. A parser that quietly under-matches produces a number
    that looks like evidence and is not.
    """
    out: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)
    for path in list(root.glob("src/**/*.cpp")) + list(root.glob("src/**/*.hpp")):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines):
            if "@dottalk.usage" not in line:
                continue
            command = status = None
            for follow in lines[index + 1:index + 40]:
                if "@dottalk." in follow and "usage" not in follow:
                    break
                match = re.match(r"\s*//\s*command:\s*(\S+)", follow)
                if match and not command:
                    command = match.group(1).strip().upper()
                match = re.match(r"\s*//\s*status:\s*(\S+)", follow)
                if match and not status:
                    status = match.group(1).strip().lower()
            if command and status:
                out[command].add((status, path.name))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--manual-index", default=DEFAULT_MANUAL)
    ap.add_argument("--strict", action="store_true",
                    help="Exit 2 on any disagreement. For after the vocabulary is ruled on.")
    a = ap.parse_args(argv)

    root = Path(a.repo_root).resolve()
    index = root / a.manual_index
    if not index.is_file():
        print(f"contract-status: no accepted index at {a.manual_index}")
        return 0

    published = {}
    for line in index.read_text(encoding="utf-8", errors="replace").splitlines():
        match = ROW.match(line)
        if match:
            published[match.group(1).strip().upper()] = match.group(3).strip().lower()

    declared = contract_statuses(root)
    both = sorted(set(published) & set(declared))
    disagree = [(c, published[c], s, f)
                for c in both for s, f in sorted(declared[c]) if s != published[c]]

    print(f"contract-status: {len(declared)} command(s) declare a contract status")
    print(f"  published in the accepted manual        : {len(published)}")
    print(f"  declare a status AND are published      : {len(both)}")
    print(f"  DISAGREE with the manual                : {len(disagree)}")
    if not disagree:
        print("contract-status: PASS -- every published command matches its contract")
        return 0

    directions = collections.Counter(p for _, p, _, _ in disagree)
    print(f"  what the manual says, where they differ : {dict(directions)}")
    if len(directions) == 1:
        print("    ALL IN ONE DIRECTION -- the manual is not drifting randomly, it is")
        print("    over-claiming uniformly. That points at a missing comparison, not")
        print("    at scattered staleness.")

    grouped = collections.defaultdict(list)
    for command, pub, con, src in disagree:
        grouped[axis_of(con)].append((command, pub, con, src))
    print("\n  grouped by the question the contract was answering")
    print("  (axes PROPOSED in the glossary, GREEN_TENTATIVE 2026-09-02):")
    for axis in ("lifecycle", "completeness", "audience", "mechanism", "process", "unclassified"):
        rows = grouped.get(axis)
        if not rows:
            continue
        print(f"\n    {axis.upper()} ({len(rows)})")
        for command, pub, con, src in sorted(rows):
            print(f"      {command:<14} manual={pub:<11} contract={con:<22} {src}")

    print("\n  Neither side is assumed correct. Two readings stay open: the catalog is")
    print("  stale, OR `supported` means dispatchable there and mature here -- one word,")
    print("  two questions. The glossary rows exist to settle that.")
    if a.strict:
        print("  --strict: failing.")
        return 2
    print("  Report-only. Nothing is blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
