#!/usr/bin/env python3
"""Report the next free AIF number.

WHY THIS EXISTS AND WHY IT IS NOT A ONE-LINER: an AIF number can be taken in
TWO places, and reading either one alone hands out a number that is already
spoken for.

  1. docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md -- the intake register.
     Rows are `| AIF-NNN | ...`. A row may exist with NO claim file yet; the
     prepush gate calls those "pre-coordination" and there are dozens of them.
  2. coordination/aif/AIF-NNN.claim -- the claim files. Far fewer than the
     intake rows.

So the authority is the UNION. Scanning only the claim directory is the
tempting mistake and it collides with every pre-coordination row.

NEXT FREE IS max + 1, NEVER the lowest gap. Gaps in the sequence are not
free real estate -- a number may have been split, withdrawn or reserved
elsewhere, and a reused number makes two different things share an identity
in a record that is supposed to be permanent. Gaps are REPORTED so a human
can rule on them; they are never handed out.

Run:  $py12 tools\\coordination\\next_aif.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
INTAKE = ROOT / "docs" / "ai-friendly" / "AI_INTERACTION_INTAKE_QUEUE_V1.md"
CLAIMS = ROOT / "coordination" / "aif"

# ONE OR MORE digits, deliberately. The first cut of this script used
# \d{3,} because the corpus is zero-padded to three -- which means a number
# written AIF-89 anywhere would have matched NOTHING and been reported as
# FREE. That is the AIF-118 shape (a check that answers the same for "absent"
# and "fine") inside the tool meant to prevent collisions. Match loosely and
# normalise to int; the padding is a display convention, not the identity.
PAT = re.compile(r"AIF-0*(\d+)")


def main() -> int:
    intake_nums: set[int] = set()
    if INTAKE.is_file():
        text = INTAKE.read_text(encoding="utf-8", errors="replace")
        intake_nums = {int(m) for m in PAT.findall(text)}
    else:
        print(f"WARNING: intake register not found: {INTAKE}", file=sys.stderr)

    claim_nums: set[int] = set()
    if CLAIMS.is_dir():
        for p in CLAIMS.glob("AIF-*.claim"):
            m = PAT.search(p.name)
            if m:
                claim_nums.add(int(m.group(1)))
    else:
        print(f"WARNING: claim directory not found: {CLAIMS}", file=sys.stderr)

    taken = intake_nums | claim_nums
    if not taken:
        print("REFUSING: found zero AIF numbers in either source.")
        print("  That is far more likely to be a broken path than an empty")
        print("  project, and handing out AIF-001 on it would be a collision.")
        return 2

    hi = max(taken)
    nxt = hi + 1

    print(f"intake register : {len(intake_nums)} number(s)  {INTAKE.relative_to(ROOT)}")
    print(f"claim files     : {len(claim_nums)} number(s)  {CLAIMS.relative_to(ROOT)}/")
    print(f"union           : {len(taken)} distinct")
    print(f"highest taken   : AIF-{hi}")
    print()
    print(f"NEXT FREE       : AIF-{nxt}")
    print()

    claim_only = sorted(claim_nums - intake_nums)
    if claim_only:
        print(f"claim file but NO intake row ({len(claim_only)}): "
              + ", ".join(f"AIF-{n}" for n in claim_only))

    gaps = sorted(set(range(min(taken), hi)) - taken)
    if gaps:
        print(f"gaps, NOT reusable ({len(gaps)}): "
              + ", ".join(f"AIF-{n}" for n in gaps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
