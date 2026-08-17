#!/usr/bin/env python3
"""Surface open items whose NEXT LOOK date has passed.

WHY THIS EXISTS (2026-08-17)
    `coordination/OPEN_ITEMS.md` is the rung below a lane: small deferred work
    that is too small for an AIF lane and too real to lose in chat. A register
    nobody surfaces decays -- AIF-006's warning text measured exactly that, an
    obligation with no gate holding at 33 percent compliance against 83-94 for
    gated ones. This is the surfacing.

WHY IT NEVER BLOCKS
    Every row here is deferred BY CHOICE. A gate that blocked on them would
    teach people to delete rows rather than do the work, which is strictly worse
    than not having the register: you would lose the item AND believe you were
    clean. So this prints and returns 0 for "nothing due", 3 for "something is
    due" -- an advisory code the pre-push gate reports and does not fail on.

WHY IT PARSES DATES RATHER THAN COUNTING ROWS
    A count is noise: it reads the same on day one and day two hundred, so it
    stops being read. A due date makes the reminder periodic and honest -- the
    row is silent until you said you wanted to hear about it, then it speaks
    every commit until you move the date or do the work.

    The RAISED date is deliberately also parsed and reported once an item is
    overdue, because "snoozed since March" is the fact that matters and a NEXT
    LOOK date alone hides it.

NO YAML ON PURPOSE
    None of the gates in this repo import yaml (measured 2026-08-17: zero across
    prepush_gate, aif_collision_gate, check_session_log_row, check_seed_budget).
    The host runs these under whatever python the git hook has, which is not
    guaranteed to carry PyYAML -- the repo keeps a separate .venv312 precisely
    because the default interpreter lacks it. A gate that cannot run is a gate
    that is not there, so this parses a markdown table with the standard library.

Exit codes: 0 nothing due (or no register), 2 register unreadable, 3 items due.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REGISTER = "coordination/OPEN_ITEMS.md"

# | OI-001 | 2026-08-17 | 2026-09-15 | dns | text ... |
ROW = re.compile(
    r"^\|\s*(OI-\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|"
    r"\s*([a-z]+)\s*\|\s*(.+?)\s*\|\s*$"
)


def repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".git").exists() and (p / "AI_README.md").exists():
            return p
    return start


def parse(path: Path):
    """Return (rows, malformed). A row is (id, raised, next_look, where, text)."""
    rows, malformed = [], []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("| OI-"):
            continue
        m = ROW.match(line)
        if m:
            rows.append(m.groups())
        else:
            # A row that LOOKS like an item but does not parse is reported, not
            # skipped. Silently dropping it would be the absent-vs-fine defect
            # this repository keeps finding: the register would look shorter and
            # healthier for being broken.
            malformed.append((n, line[:70]))
    return rows, malformed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    ap.add_argument("--all", action="store_true", help="list every item, not just due")
    ap.add_argument("--today", default=None, help="override today (YYYY-MM-DD), for tests")
    args = ap.parse_args(argv)

    root = Path(args.root) if args.root else repo_root(Path(__file__).resolve().parent)
    path = root / REGISTER
    if not path.is_file():
        # Absent register is not an error. It means nobody has parked anything.
        print(f"open-items: no register at {REGISTER} -- nothing parked")
        return 0

    try:
        rows, malformed = parse(path)
    except OSError as exc:
        print(f"open-items: cannot read {REGISTER}: {exc}", file=sys.stderr)
        return 2

    today = (dt.date.fromisoformat(args.today) if args.today else dt.date.today())

    due = []
    for oid, raised, nxt, where, text in rows:
        try:
            when = dt.date.fromisoformat(nxt)
            born = dt.date.fromisoformat(raised)
        except ValueError:
            malformed.append((0, f"{oid}: unparseable date"))
            continue
        if when <= today:
            due.append((oid, born, when, where, text))

    if args.all:
        print(f"open-items: {len(rows)} item(s) in {REGISTER}")
        for oid, raised, nxt, where, text in rows:
            print(f"  {oid}  raised {raised}  next {nxt}  [{where}]  {text[:72]}")

    for line_no, raw in malformed:
        where = f"line {line_no}" if line_no else "row"
        print(f"open-items: MALFORMED {where}: {raw}", file=sys.stderr)

    if not due:
        if not args.all:
            print(f"open-items: {len(rows)} parked, none due before {today}")
        return 2 if malformed else 0

    print(f"\nopen-items: {len(due)} of {len(rows)} item(s) DUE as of {today}")
    for oid, born, when, where, text in due:
        age = (today - born).days
        overdue = (today - when).days
        print(f"  {oid}  [{where}]  raised {born} ({age}d ago)"
              f"{f', due {overdue}d ago' if overdue else ', due today'}")
        print(f"        {text[:100]}")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
