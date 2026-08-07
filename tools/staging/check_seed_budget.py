#!/usr/bin/env python3
"""Enforce the byte budget a document declares about itself.

AIF-090 D4. `AI_TIER1_SEED_V1.md` declares `budget: 8192 B hard ceiling` in its
own header and `AI_PORTAL.md` holds that ceiling up as the project's exemplar of
a BOUNDED metric:

    "A bounded metric is a gate; the Tier-1 seed's 8,192-byte ceiling caught its
     author three times in one sitting, which an unbounded byte count would not
     have done once."

Measured 2026-08-06 by a cold probe: the seed was 8,990 B. 798 over. It caught
its author because its author was watching, and nothing was watching after that.
An unenforced obligation is a wish. This makes it a gate.

WHY THIS GATE HARDCODES NOTHING. The ceiling is read FROM THE FILE, so the rule
travels with the document that owns it and any future budgeted document is
covered without touching this code. A gate carrying its own copy of the number
would be a second source of truth, which is the defect class this repo keeps
paying for.

    python tools/staging/check_seed_budget.py                 # default targets
    python tools/staging/check_seed_budget.py FILE...         # explicit
    python tools/staging/check_seed_budget.py --warn          # never exit 2

Declaration syntax recognised anywhere in the first 40 lines:

    budget      : 8192 B hard ceiling (see "Maintenance contract")

Exit codes: 0 within budget or nothing declared, 1 unreadable target,
2 over budget (blocking, unless --warn).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_TARGETS = [
    "labtalk/ai_portal/AI_TIER1_SEED_V1.md",
]

# `budget` then a colon then an integer then an optional B. Tolerant of the
# aligned-colon header style this repo uses.
BUDGET_RE = re.compile(r"^\s*budget\s*:\s*([0-9][0-9_,]*)\s*B\b", re.IGNORECASE)
HEADER_LINES = 40


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c / ".git").exists() and (c / "AI_README.md").exists():
            return c
    print("check-seed-budget: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def declared_budget(text: str) -> int | None:
    for line in text.splitlines()[:HEADER_LINES]:
        m = BUDGET_RE.match(line)
        if m:
            return int(m.group(1).replace("_", "").replace(",", ""))
    return None


def check(path: Path, rel: str, warn_only: bool) -> int:
    try:
        # Budget is a byte budget, so measure bytes, not characters. Reading as
        # text and calling len() would undercount any multi-byte content and
        # quietly grant extra room -- a denominator error, which is the failure
        # class AIF-082 recorded three times.
        raw = path.read_bytes()
    except OSError as exc:
        print(f"check-seed-budget: cannot read {rel}: {exc}", file=sys.stderr)
        return 1

    budget = declared_budget(raw.decode("utf-8", errors="replace"))
    if budget is None:
        print(f"check-seed-budget: {rel} declares no budget -- skipped")
        return 0

    actual = len(raw)
    headroom = budget - actual
    if headroom >= 0:
        pct = round(100 * actual / budget)
        print(f"check-seed-budget: PASS -- {rel} {actual} B of {budget} B "
              f"({pct}%, {headroom} B headroom)")
        return 0

    print(f"check-seed-budget: {'WARN' if warn_only else 'FAIL'} -- {rel} is "
          f"{actual} B against its own declared {budget} B ceiling, "
          f"OVER BY {-headroom}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  The document states this ceiling about itself. Adding requires", file=sys.stderr)
    print("  REMOVING or DEMOTING to the trigger index -- and demoting means", file=sys.stderr)
    print("  MOVING, not restating. Without the ceiling the seed becomes the", file=sys.stderr)
    print("  corpus it was extracted from.", file=sys.stderr)
    return 0 if warn_only else 2


def main() -> int:
    ap = argparse.ArgumentParser(description="Enforce self-declared byte budgets.")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--warn", action="store_true",
                    help="report but never exit 2 (adoption cycle)")
    args = ap.parse_args()

    root = repo_root()
    targets = args.files or DEFAULT_TARGETS
    worst = 0
    for rel in targets:
        worst = max(worst, check(root / rel, rel, args.warn))
    return worst


if __name__ == "__main__":
    sys.exit(main())
