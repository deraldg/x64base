#!/usr/bin/env python3
"""Require that a NEWLY ADDED intake row cites a claimed AIF number.

AIF-092. The anti-collision loop has two halves and only one had teeth:

  ALLOCATOR  `session_coordinator.py claim-aif` -- atomic O_EXCL, writes
             coordination/aif/AIF-NNN.claim. Correct, and entirely optional.
  DETECTOR   `aif_collision_gate.py` -- HARD-fails a DUPLICATE number in the
             intake queue. Correct, and only fires AFTER two lanes have already
             collided.

Nothing forced a lane through the allocator. An agent could hand-write
`AIF-093` into a row and the detector was satisfied, because it only checks
uniqueness after the fact. Measured 2026-08-07: 25 claim files against 89 intake
rows. With that many legacy rows, "next free by eye" is a plausible mistake, and
by eye is exactly what the ledger exists to replace -- grep is not an allocator.

This closes the gap from the front: a row that ENTERS the queue must name a
number the allocator issued.

WHY ADDED LINES ONLY. Sixty-five rows predate coordination and have no claim
file. Failing on those would block every commit and the gate would be disabled
within a day. So the rule is the one `check_house_style.py` already proves works
here: the historical backlog is not your problem; the lines this change
introduces are. New violations become impossible while the backlog drains at
whatever pace the owner chooses.

    python tools/coordination/check_aif_claimed.py             # staged (pre-commit)
    python tools/coordination/check_aif_claimed.py --range A..B
    python tools/coordination/check_aif_claimed.py --warn      # adoption cycle

Exit codes: 0 clean, 2 an added row names an unclaimed AIF number.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

INTAKE = "docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md"
CLAIM_DIR = "coordination/aif"

# An intake ROW, not a passing mention: the table's first cell. A row that only
# discusses AIF-041 in its notes must not be treated as claiming it.
ROW_RE = re.compile(r"^\|\s*AIF-(\d{3})\b")


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c / ".git").exists() and (c / "AI_README.md").exists():
            return c
    print("check-aif-claimed: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def _git(root: Path, *args: str) -> str:
    """Read-only git. Never takes .git/index.lock."""
    out = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60, check=False,
    )
    return out.stdout if out.returncode == 0 else ""


def _numbers_in(text: str) -> set[int]:
    return {int(m.group(1)) for m in
            (ROW_RE.match(l) for l in text.splitlines()) if m}


def added_rows(root: Path, rng: str | None) -> list[tuple[int, str]]:
    """(aif_number, text) for rows whose NUMBER is NEW to the queue.

    A DIFF MARKER IS NOT A NEW ROW. Editing an existing row -- fixing a typo,
    updating a status, appending evidence -- surfaces in `git diff` as a `+`
    line exactly like a brand-new row. Sixty-five legacy rows have no claim
    file, so trusting the marker meant routine maintenance on any of them would
    be blocked. Measured 2026-08-07 before the advisory-to-hard flip: editing
    the AIF-041 row returned exit 2.

    So the question is not "is this line added" but "is this NUMBER new to the
    file". The pre-image answers it: HEAD for a staged check, the range base
    otherwise.
    """
    args = ["diff", "--cached", "-U0"] if rng is None else ["diff", "-U0", rng]
    diff = _git(root, *args, "--", INTAKE)
    if not diff:
        return []

    base = "HEAD" if rng is None else rng.split("..", 1)[0]
    already = _numbers_in(_git(root, "show", f"{base}:{INTAKE}"))

    rows, seen = [], set()
    for raw in diff.splitlines():
        if raw.startswith("+") and not raw.startswith("+++"):
            m = ROW_RE.match(raw[1:])
            if m:
                n = int(m.group(1))
                if n in already or n in seen:
                    continue  # edited in place, not newly introduced
                seen.add(n)
                rows.append((n, raw[1:]))
    return rows


def claimed(root: Path) -> set[int]:
    d = root / CLAIM_DIR
    if not d.is_dir():
        return set()
    out = set()
    for p in d.glob("AIF-*.claim"):
        m = re.match(r"AIF-(\d{3})\.claim$", p.name)
        if m:
            out.add(int(m.group(1)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="New intake rows must cite a claimed AIF.")
    ap.add_argument("--range", dest="rng", default=None, help="commit range, e.g. HEAD~1..HEAD")
    ap.add_argument("--warn", action="store_true", help="report but never exit 2")
    args = ap.parse_args()

    root = repo_root()
    rows = added_rows(root, args.rng)
    if not rows:
        print("check-aif-claimed: no new intake rows in scope -- nothing to check")
        return 0

    have = claimed(root)
    bad = [(n, t) for n, t in rows if n not in have]

    if not bad:
        nums = ", ".join(f"AIF-{n:03d}" for n, _ in rows)
        print(f"check-aif-claimed: PASS -- new row(s) {nums} cite claimed numbers")
        return 0

    print(f"check-aif-claimed: {'WARN' if args.warn else 'FAIL'} -- "
          f"{len(bad)} new intake row(s) name an AIF number with no claim file",
          file=sys.stderr)
    for n, text in bad:
        print(f"  AIF-{n:03d}  (no {CLAIM_DIR}/AIF-{n:03d}.claim)", file=sys.stderr)
        print(f"      | {text.strip()[:96]}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Claim the number atomically instead of choosing one by eye:", file=sys.stderr)
    print("", file=sys.stderr)
    print("      python tools/coordination/session_coordinator.py claim-aif \\",
          file=sys.stderr)
    print("        --member <member.id> --run <RUN-ID> --lane <lane-name>",
          file=sys.stderr)
    print("", file=sys.stderr)
    print("  Grep is not an allocator: two sessions share one working tree and", file=sys.stderr)
    print("  will read the same 'next free' number. Only ADDED rows are checked,", file=sys.stderr)
    print("  so the pre-coordination backlog is not your problem.", file=sys.stderr)
    return 0 if args.warn else 2


if __name__ == "__main__":
    sys.exit(main())
