#!/usr/bin/env python3
"""R-number collision gate. The teeth on the R allocator.

THE NEAR-MISS THIS EXISTS FOR (2026-08-24). A ruling was about to be stamped R7
on the assumption that each AIF lane carried its own R1..Rn series. It does not:
the R-space is one flat global sequence, and R7 had been taken since 2026-08-06
by the owner ruling on AIF-090. Nothing detected it. There was no register, no
allocator and no gate -- the number was checked only because someone happened to
grep before typing. Grep is not an allocator, and luck is not a gate.

THE TWO HALVES, mirroring the AIF pair deliberately:

  ALLOCATOR  next_r.py -- reads the register AND the tree, reports max+1.
             Correct, and entirely optional.
  DETECTOR   this file -- HARD-fails a duplicate declared number, and HARD-fails
             a number ALLOCATED at or below the register's declared high-water
             without being marked `backfill`. The second check is the one that
             would have caught R7.

THE SECOND CHECK WAS WRONG TWICE BEFORE IT WAS RIGHT. Both failures are kept
here because each is cheaper to read than to rediscover.

  FIRST CUT compared a newly declared number against citations in the WHOLE
  WORKING TREE. Caught by reasoning before shipping: declaring R119 and citing
  it at its code sites in the same change is the CORRECT flow, and that compare
  cannot tell it from theft.

  SECOND CUT compared against files the change does not touch. It blocked the
  gate's OWN FIRST COMMIT -- the register's seeding rows for R1, R2, R3, R5,
  R6, R7, R110, R112, R113 and R114, every one of them a number correctly cited
  in the tree for years. And the failure was not a tuning error: CITATION
  CANNOT SEPARATE THEFT FROM BACK-FILL AT ALL. "R7 declared fresh as a new
  ruling" and "R7 declared to record what it always meant" produce identical
  evidence. The check was measuring something that does not carry the answer.

  THIS CUT stops guessing and makes the human state intent once, in the row. A
  number entering the register at or below the declared high-water must carry
  the token `backfill`; an allocation is above the high-water and needs no
  marker, because taking max+1 IS the statement. A first seeding passes freely
  -- with no rows at base the high-water is 0.

THE POPULATION IS NOT REDEFINED HERE. It is imported from next_r.py, because
two implementations of "which numbers are taken" is two answers to one question,
which is R5's definition of the defect. The gate and the allocator must be
unable to disagree.

WHY THE UNDECLARED BACKLOG IS ADVISORY AND NOTHING ELSE. Roughly a hundred
numbers are cited in the tree with no register row; they predate the register by
years. A gate that blocked on them would be red on every commit and switched off
within a day -- the reasoning that keeps check_open_items.py advisory, and that
kept check_aif_claimed.py to ADDED rows only.

    python tools/coordination/r_collision_gate.py            # staged (pre-commit)
    python tools/coordination/r_collision_gate.py --range A..B

Exit codes: 0 clean, 2 a hard collision, 3 advisory backlog only.
Owner: member.derald -- steward: member.ai.claude.cowork.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from next_r import REGISTER, ROOT, cited, cited_map, declared  # noqa: E402

REGISTER_REL = "docs/ai-friendly/R_RULING_REGISTER_V1.md"

# A DECLARED ROW, not a passing mention: the table's first cell. A row that only
# discusses R112 in its notes must not be treated as declaring it.
ROW_RE = re.compile(r"^\|\s*R0*(\d{1,3})\s*\|")


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


def declared_at_base(root: Path, rng: str | None) -> set[int]:
    """Numbers the register declared BEFORE this change."""
    base = "HEAD" if rng is None else rng.split("..", 1)[0]
    return _numbers_in(_git(root, "show", f"{base}:{REGISTER_REL}"))


def newly_declared(root: Path, rng: str | None) -> list[tuple[int, str]]:
    """Numbers NEW to the register's declared table.

    A DIFF MARKER IS NOT A NEW ROW -- back-filling what R44 meant edits a row in
    place and shows as a `+` line exactly like a fresh declaration. Back-filling
    is explicitly encouraged by the register, so trusting the marker would block
    the one maintenance activity the register asks for. The pre-image answers the
    real question: is this NUMBER new to the file.
    """
    args = ["diff", "--cached", "-U0"] if rng is None else ["diff", "-U0", rng]
    diff = _git(root, *args, "--", REGISTER_REL)
    if not diff:
        return []
    base = "HEAD" if rng is None else rng.split("..", 1)[0]
    already = _numbers_in(_git(root, "show", f"{base}:{REGISTER_REL}"))

    out, seen = [], set()
    for raw in diff.splitlines():
        if raw.startswith("+") and not raw.startswith("+++"):
            m = ROW_RE.match(raw[1:])
            if m:
                n = int(m.group(1))
                if n in already or n in seen:
                    continue
                seen.add(n)
                out.append((n, raw[1:]))
    return out


def changed_files(root: Path, rng: str | None) -> set[str]:
    """Repo-relative posix paths touched by this change."""
    args = (["diff", "--cached", "--name-only"] if rng is None
            else ["diff", "--name-only", rng])
    return {l.strip() for l in _git(root, *args).splitlines() if l.strip()}


def occupied_elsewhere(changed: set[str]) -> set[int]:
    """Numbers cited by files this change does NOT touch.

    NO LONGER THE HARD CHECK -- see the docstring's second cut. Retained
    because it is the honest way to ask "what does the tree already carry",
    which is useful context even though it cannot distinguish theft from
    back-fill. Exercised by the fixtures so it cannot rot unnoticed.

    THE POINT OF THE EXCLUSION. Declaring R119 and citing it at its code sites
    in the same change is the correct flow: allocate, declare, cite. A gate
    comparing against the whole working tree would see the change's own fresh
    citations and hard-fail every legitimate first use of a number -- and it
    would do so on the very first commit after the gate shipped.

    The register is excluded too: it is where the declaration is being made,
    so counting it would fail every new row against itself.
    """
    out: set[int] = set()
    for rel, nums in cited_map().items():
        if rel in changed or rel == REGISTER_REL:
            continue
        out |= nums
    return out


def unmarked_allocations(fresh: list[tuple[int, str]], base_hi: int) -> list[int]:
    """New rows that claim an already-passed number without saying `backfill`.

    THE WHOLE RULE, in one place, so the fixtures test the predicate the gate
    actually runs rather than a restatement of it. A test that re-implements
    its subject proves the test agrees with itself.
    """
    return sorted(n for n, row in fresh
                  if n <= base_hi and "backfill" not in row.lower())


def duplicate_rows() -> list[int]:
    if not REGISTER.is_file():
        return []
    seen, dupes = set(), set()
    for line in REGISTER.read_text(encoding="utf-8", errors="replace").splitlines():
        m = ROW_RE.match(line)
        if m:
            n = int(m.group(1))
            (dupes.add(n) if n in seen else seen.add(n))
    return sorted(dupes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--range", dest="rng", default=None)
    ap.add_argument("--no-git", action="store_true",
                    help="skip the added-row check (population checks only)")
    args = ap.parse_args()

    print("=== R-number collision gate ===")

    if not REGISTER.is_file():
        print(f"  (skipped: {REGISTER_REL} not present)")
        return 0

    reg = declared()
    cite, files = cited()
    print(f"declared: {len(reg)}   cited in tree: {len(cite)} "
          f"(over {files} file(s))   highest: R{max(reg | cite or {0})}")

    exit_code = 0

    dupes = duplicate_rows()
    if dupes:
        exit_code = 2
        print("\nHARD FAIL: duplicate declared R-number(s): "
              + ", ".join(f"R{n}" for n in dupes), file=sys.stderr)
        print("  -> two rulings cannot share one identity in a permanent "
              "record. Renumber one via next_r.py.", file=sys.stderr)
    else:
        print("HARD: no duplicate declared numbers  OK")

    if not args.no_git:
        # THE R7 CHECK -- SECOND FORMULATION. See the module docstring for why
        # the first one was wrong.
        #
        # A number ENTERING the register is one of exactly two things, and only
        # a human knows which:
        #
        #   AN ALLOCATION -- a decision made now, which must take max+1.
        #   A BACK-FILL   -- writing down what an already-cited number meant.
        #
        # Citation cannot separate them: R7-as-a-fresh-ruling and
        # R7-as-a-back-fill are both "already cited elsewhere". So the gate
        # stops guessing and makes the human SAY which, exactly once, in the
        # row: a new number at or below the register's own declared high-water
        # must carry the token `backfill`. An allocation is above it and needs
        # no marker, because taking max+1 IS the statement.
        #
        # A first seeding passes freely: with no rows at base the high-water is
        # 0, everything is above it, and a bulk seed is a back-fill by
        # definition with nothing to judge it against.
        fresh = newly_declared(ROOT, args.rng)
        if fresh:
            base_hi = max(declared_at_base(ROOT, args.rng) or {0})
            unmarked = unmarked_allocations(fresh, base_hi)
            if unmarked:
                exit_code = 2
                print("\nHARD FAIL: newly declared R-number(s) at or below the "
                      f"register's declared high-water (R{base_hi}) with no "
                      "`backfill` marker: "
                      + ", ".join(f"R{n}" for n in unmarked), file=sys.stderr)
                print("  -> this is the R7 shape: a decision made NOW must take "
                      "max+1, not a number that already means something. Run "
                      "next_r.py. If you are recording what an OLD number "
                      "meant, put `backfill` in the row and say so.",
                      file=sys.stderr)
            else:
                print(f"HARD: {len(fresh)} newly declared number(s), "
                      f"high-water at base R{base_hi}  OK")

    undeclared = sorted(cite - reg)
    if undeclared:
        print(f"\nadvisory: {len(undeclared)} number(s) cited in the tree with "
              f"no register row (reserved, never reusable; back-fill welcome)")
        if exit_code == 0:
            exit_code = 3

    if exit_code == 2:
        return 2
    print("\nPASS" if exit_code == 0 else "\nPASS (advisory backlog only)")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
