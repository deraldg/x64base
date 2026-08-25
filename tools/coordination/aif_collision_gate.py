#!/usr/bin/env python3
"""
AIF-collision gate (AIF-050 coordination enforcement).

The enforcement that makes coordination real: a duplicate AIF lane number cannot be committed.
Wire this into the pre-push gate so it runs at the one chokepoint every parallel session funnels
through -- the maintainer's commit -- regardless of whether any session ran the coordinator.

Checks:
  HARD  (exit 1)  duplicate AIF-NNN across intake-queue rows  <- the exact collision
  ADVISORY        claim ledger vs intake reconciliation:
                    - a claim with no intake row (abandoned/demo claim -> release it)
                    - an intake row with no claim (pre-coordination row; backfill or ignore)

--strict promotes the reconciliation to hard once the ledger is backfilled.
No third-party deps. Owner: member.derald - steward: member.ai.claude.cowork - lane: AIF-050.
"""
import argparse
import idcite
import re
import sys
from pathlib import Path

INTAKE = "docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md"
AIF_DIR = "coordination/aif"
# R126: an AIF number IS AN INTEGER. The zero padding is a DISPLAY convention.
# Match loosely (any width, any padding) and normalise to int; render with %03d,
# which is a MINIMUM width and widens by itself past 999. Measured 2026-08-25:
# `AIF-\d{3}` read "AIF-1000" as NO MATCH in five readers and, in
# tools/tracking/seed_tracking.py, as "AIF-100" -- a DIFFERENT, ALREADY-TAKEN
# number. Silent identity collision, not a decline.
ROW_RE = re.compile(r"^\|\s*AIF-0*(\d+)\b", re.MULTILINE)
CLAIM_RE = re.compile(r"AIF-0*(\d+)\.claim$")
# DELIBERATELY LOOSER THAN ROW_RE: one or more digits, any padding. A number
# written AIF-89 in prose is spoken for exactly as much as one written AIF-089,
# and this pattern is used ONLY to report, never to fail. Same reasoning as
# tools/coordination/next_aif.py's PAT -- padding is a display convention, not
# an identity.
MENTION_RE = re.compile(r"AIF-0*(\d+)")


def canon(n) -> str:
    """Digits (any width/padding) -> the one canonical spelling. R126."""
    return f"AIF-{int(n):03d}"


def intake_text(root: Path) -> str:
    p = root / INTAKE
    return p.read_text(errors="ignore") if p.exists() else ""


def intake_numbers(root: Path):
    # Canonicalise on the way out so AIF-43 and AIF-043 are ONE number, not two.
    # Without this the loosened pattern would make a duplicate INVISIBLE -- the
    # opposite of what this gate is for.
    return [canon(n) for n in ROW_RE.findall(intake_text(root))]


def claimed(root: Path):
    d = root / AIF_DIR
    if not d.is_dir():
        return set()
    return {canon(m.group(1)) for f in d.glob("AIF-*.claim") if (m := CLAIM_RE.search(f.name))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--intake", default=None, help="override intake path (for testing)")
    ap.add_argument("--strict", action="store_true", help="reconciliation is hard, not advisory")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    rows = ROW_RE.findall(Path(args.intake).read_text(errors="ignore")) if args.intake else intake_numbers(root)
    seen, dupes = set(), []
    for n in rows:
        (dupes.append(n) if n in seen else seen.add(n))
    dupes = sorted(set(dupes))

    print("=== AIF-collision gate ===")
    print(f"intake rows: {len(rows)}   distinct AIF: {len(seen)}")

    fail = False
    if dupes:
        fail = True
        print(f"\nHARD FAIL: duplicate AIF number(s) in the intake queue: {', '.join(dupes)}", file=sys.stderr)
        print("  -> two lanes claimed the same number. Renumber one via session_coordinator.py claim-aif.",
              file=sys.stderr)
    else:
        print("HARD: no duplicate AIF numbers  OK")

    if not args.intake:
        claims = claimed(root)
        rowset = set(rows)
        orphan_claims = sorted(claims - rowset)     # claim with no intake row
        unclaimed_rows = sorted(rowset - claims)    # intake row with no claim
        if orphan_claims:
            print(f"\nadvisory: claim(s) with no intake row (abandoned/demo -> release-aif): {', '.join(orphan_claims)}")
        if unclaimed_rows:
            print(f"advisory: intake row(s) with no claim file (pre-coordination): {len(unclaimed_rows)}")

        # ADVISORY -- AIF numbers CITED in the register with no row of their own.
        # Added 2026-08-25 (AIF-128 follow-on). PRINT ONLY: it cannot move the
        # exit code, and must not -- a cross-reference is not a collision.
        #
        # WHY IT EXISTS. R-numbers already get this advisory ("N number(s) cited
        # in the tree with no register row, back-fill welcome") and AIF numbers
        # did not, so the class was invisible here. It surfaced only because two
        # counters in the same prepush output disagreed by one -- next_aif.py
        # reporting 126 against this gate's 125 -- and someone diffed them by
        # hand. One number today; the class grows silently.
        #
        # SCOPE IS THE REGISTER, NOT THE TREE, and that is a deliberate limit.
        # The R gate walks 1,884 files; this reads the one file already in hand,
        # so it costs nothing and catches the case that actually bit. An AIF
        # number cited only in source or a lane doc is NOT reported. Say so
        # rather than let the line read as full coverage.
        cited_no_row = sorted(
            {canon(n) for n in
             {int(m) for m in MENTION_RE.findall(
                 idcite.live_text(intake_text(root)))}}
            - rowset)
        if cited_no_row:
            print(f"advisory: AIF number(s) cited in the register with no row of "
                  f"their own (register scope only, not the tree; back-fill "
                  f"welcome): {', '.join(cited_no_row)}")
        if args.strict and (orphan_claims or unclaimed_rows):
            fail = True
            print("STRICT: ledger/intake not reconciled -> FAIL", file=sys.stderr)

    if fail:
        return 1
    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
