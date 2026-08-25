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

SEE ALSO: R-numbers (doctrine rules and lane rulings) are a SEPARATE flat
sequence with their own allocator, tools/coordination/next_r.py. They are not
per-lane and they are not derived from an AIF number. Cross-linked in both
directions on purpose: AIF-090 D1 measured what happens to a tool nothing
points at -- recall.py was cited by ZERO entry-path documents and a cold probe
hunting for exactly that kind of tool found six others and missed it.

Run:  $py12 tools\\coordination\\next_aif.py
"""
import idcite
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

# THE DECLARATION PATTERN, AND IT IS NOT SUPPRESSIBLE. A row id is how an AIF
# number is CLAIMED. `id-cite:ignore` may hide a citation; if it could hide a
# row the marker would become a way to conceal a duplicate. So row ids are
# unioned in BEFORE the marker is applied to the looser scan below.
ROW_PAT = re.compile(r"^\|\s*AIF-0*(\d+)\b", re.MULTILINE)


def main() -> int:
    intake_nums: set[int] = set()
    opted_out = 0
    if INTAKE.is_file():
        text = INTAKE.read_text(encoding="utf-8", errors="replace")
        rows = {int(m) for m in ROW_PAT.findall(text)}          # never suppressible
        mentions = {int(m) for m in PAT.findall(idcite.live_text(text))}
        intake_nums = rows | mentions
        opted_out = idcite.suppressed_count(text)
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

    # WHY THIS NUMBER READS HIGHER THAN THE COLLISION GATE'S, added 2026-08-25.
    #
    # The prepush output prints these two lines a few apart:
    #     next_aif.py          intake register : 126 number(s)
    #     aif_collision_gate   intake rows: 125   distinct AIF: 125
    #
    # BOTH ARE RIGHT. They ask different questions on purpose. This tool
    # matches AIF-NNN ANYWHERE in the register, because a number someone has
    # merely WRITTEN DOWN is spoken for and handing it out would collide.
    # The gate matches row ids (`| AIF-NNN |`) because a row id is the only
    # thing that can be DUPLICATED. An allocator should over-count; a
    # duplicate detector must not.
    #
    # Measured 2026-08-25, the difference was exactly one number: AIF-043,
    # cited three times inside other rows' Notes and in a delivery note, with
    # no row of its own. Recorded here so the next reader does not re-derive
    # it or "fix" one tool to agree with the other. See AIF-128 for the
    # general rule: name what is in a count, and say which question it answers.
    print(f"intake register : {len(intake_nums)} number(s)  {INTAKE.relative_to(ROOT)}")
    if opted_out:
        # REPORT the opt-outs. A suppression nobody can see is
        # indistinguishable from a scanner that silently stopped working --
        # the same reason check_cited_paths prints its ignored paths.
        print(f"                  ({opted_out} line(s) marked {idcite.SUPPRESS},"
              f" citations there not counted; row ids always are)")
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

    # One line, always printed. Stamping a RULING needs the other allocator,
    # and the moment a lane number is issued is the moment someone is about to
    # need one. A pointer that only appears in a docstring is a pointer nobody
    # reads at the moment it matters.
    print()
    print("Stamping a RULING (an R-number)? Different sequence, different "
          "allocator:")
    print("  $py12 tools\\coordination\\next_r.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
