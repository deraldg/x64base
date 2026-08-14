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
import re
import sys
from pathlib import Path

INTAKE = "docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md"
AIF_DIR = "coordination/aif"
ROW_RE = re.compile(r"^\|\s*(AIF-\d{3})\b", re.MULTILINE)
CLAIM_RE = re.compile(r"AIF-(\d{3})\.claim$")


def intake_numbers(root: Path):
    p = root / INTAKE
    if not p.exists():
        return []
    return ROW_RE.findall(p.read_text(errors="ignore"))


def claimed(root: Path):
    d = root / AIF_DIR
    if not d.is_dir():
        return set()
    return {"AIF-" + m.group(1) for f in d.glob("AIF-*.claim") if (m := CLAIM_RE.search(f.name))}


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
        if args.strict and (orphan_claims or unclaimed_rows):
            fail = True
            print("STRICT: ledger/intake not reconciled -> FAIL", file=sys.stderr)

    if fail:
        return 1
    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
