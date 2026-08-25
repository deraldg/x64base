#!/usr/bin/env python3
"""
id-cite:ignore -- let a document QUOTE an identity number without SPENDING it.

WHY THIS EXISTS, AND WHAT IT COST TO LEARN
    R126 ruled that AIF and R numbers are integers and widened nine readers to
    match any width. The ruling document, explaining that a three-digit-bounded
    pattern cannot match a four-digit R row, contained three literal four-digit
    R tokens as EXAMPLES. The widened scanner -- widened by that same ruling --
    read all three as citations, and the gate reported the tree's highest R
    number as one thousand. next_r hands out max + 1, and gaps are reserved and
    never reissued, so 874 numbers were about to be spent on three examples.

    The first draft of the section describing that recreated it.

    A rule about numbers cannot be explained without example numbers. The
    workaround shipped in the meantime -- spelling every number out in words --
    works, does not scale, and makes documents worse to read.

THE PATH ANALOGUE ALREADY EXISTED
    tools/staging/check_cited_paths.py carries `cite-check:ignore` for exactly
    the same shape one layer over: a document that DOCUMENTS an ignored path
    would otherwise be flagged on every commit that touched it. This is that
    idiom applied to identity numbers, deliberately spelled the same way and
    deliberately greppable rather than magic:

        the gate reported `highest: R1000`   <!-- id-cite:ignore -->

    IT SUPPRESSES ONLY THE LINE IT APPEARS ON, so it cannot silence a document.

THE SAFETY PROPERTY THAT MAKES THIS SOUND -- READ BEFORE EXTENDING IT
    A CITATION may be suppressed. A DECLARATION MAY NOT.

    A row id in the R register or the AIF intake queue, and a claim filename,
    are how a number is CLAIMED. If the marker could hide one of those, it
    would become a way to conceal a duplicate -- turning an anti-collision gate
    into the instrument of a collision. So the declaration-side patterns
    (`^\\|\\s*R0*(\\d+)\\s*\\|`, `^\\|\\s*AIF-0*(\\d+)\\b`, `AIF-NNN.claim`) do
    not consult this module AT ALL, and next_aif unions its row ids in
    unsuppressibly before applying the marker to the looser mention scan.

    The marker can cost you a reminder. It cannot cost you a number.

Owner: member.derald -- steward: member.ai.claude.cowork -- ruling: R126.
"""

SUPPRESS = "id-cite:ignore"


def live_text(text: str) -> str:
    """`text` with every marked line removed, newlines preserved.

    Returns a STRING rather than a list so callers can keep using whatever
    pattern they already have, unchanged -- the point is that adopting this
    costs one wrapper call and no rewrite of the caller's regex.
    """
    return "\n".join(l for l in text.replace("\r\n", "\n").split("\n")
                     if SUPPRESS not in l)


def suppressed_count(text: str) -> int:
    """How many lines opted out. For tools that want to REPORT the opt-outs.

    A suppression nobody can see is indistinguishable from a scanner that
    silently stopped working -- the same reason check_cited_paths prints its
    ignored paths rather than dropping them.
    """
    return sum(1 for l in text.replace("\r\n", "\n").split("\n")
               if SUPPRESS in l)
