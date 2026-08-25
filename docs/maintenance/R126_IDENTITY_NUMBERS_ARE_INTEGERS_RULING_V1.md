# R126 -- an identity number is an INTEGER; the padding is display

    Run    : COWORK-20260825-001 (member.ai.claude.cowork), for member.derald
    Ruled  : 2026-08-25, member.derald
    Number : R126, from the allocator's own output in the prepush gate the same
             day -- "declared: 17   cited in tree: 123   highest: R125".
    Status : review-needed. The author does not self-approve.

---

## 1. The question as it was put

> "3 chars is too limiting, expand it to space and preceding zero trimmed
> 999999? or convert to a real?"

Raised after `AIF-128` recorded that `aif_collision_gate.ROW_RE` matched
exactly three digits, so a row written `| AIF-1000 |` would be invisible to the
duplicate check.

## 2. The ruling

**An AIF number and an R number are INTEGERS. Zero padding is a DISPLAY
convention and carries no meaning.**

Therefore:

  - **Readers match loosely** -- `AIF-0*(\d+)`, any width, any padding -- and
    **normalise to int**. `AIF-43` and `AIF-043` are ONE number.
  - **Writers keep `%03d`**, which is a MINIMUM width, not a fixed one, and so
    widens by itself past 999 with no rewrite.
  - **Nothing in the corpus is re-padded.** Every existing citation stays valid.

## 3. Why not the two options that were offered

**Six digits with leading zeros trimmed** answers a display question, and
display is not what was broken. Re-padding means rewriting every citation
across the ten scan directories plus 60 claim filenames, and during any
transition every tool must accept both widths anyway -- so the rewrite is paid
for AND the loose matcher is still needed. The loose matcher alone is the whole
fix.

**A real** is the wrong type for an identity, and there is nowhere to put it:
no DBF has an AIF column. These numbers live in markdown rows and `.claim`
filenames only. Identity needs equality and `max()`, nothing else; a real
invites representability and ordering questions in exchange for no capability.
The house has a fresh scar from a numeric-width assumption meeting a format
that could not hold it -- `SUMMARY` asked for C256, wrapped to 0, and wrote a
zero-width column (AIF-126).

## 4. This was already ruled once, in one file, and six others never heard

`tools/coordination/next_aif.py` carries the reasoning verbatim, written after
an earlier instance of exactly this bug:

> "Match loosely and normalise to int; the padding is a display convention,
> not the identity."

One reader had it. Eight did not. **The value of R126 is not the insight -- it
is putting the insight somewhere all nine readers are obliged to look.**

## 5. What was measured, including the part that corrects me

**THE FORMATTER WAS NEVER THE CEILING.** `f"AIF-{n:03d}"` renders 1000 as
`AIF-1000` and 999999 as `AIF-999999`; `%03d` is a minimum width. I said on
that basis that "the writers are already fine". **That was wrong**, and the
correction belongs here rather than in a quiet edit: `session_coordinator.py`
carried `AIF_LO, AIF_HI = 6, 999`, and the candidate scan stopped dead at 999.
At `AIF-999` the formatter would have been perfectly happy while `claim-aif`
returned no candidate at all. The ceiling was in the ALLOCATOR'S RANGE, one
line away from the formatter I had checked.

**THE READERS, MEASURED AGAINST `AIF-1000`:**

    aif_collision_gate.ROW_RE     NO MATCH
    check_aif_claimed.ROW_RE      NO MATCH
    session_coordinator claim     NO MATCH
    lane.LANE_RE (exact match)    NO MATCH
    next_r.CITE / .ROW  (R1000)   NO MATCH
    seed_tracking.AIFPAT          'AIF-100'   <-- NOT a decline
    next_aif.PAT                  'AIF-1000'  <-- the one that was right

`seed_tracking` did not fail to match. It returned **a different, already-taken
number**. A ceiling that declines is a nuisance; a ceiling that silently
truncates an identity into another live identity is a collision.

**THE SIBLING SEQUENCE IS CLOSER TO THE WALL.** `next_r.py` used
`R0*(\d{1,3})`, so `| R1000 |` matched nothing -- and R is at **R125** against
AIF's 128, with the same three-digit ceiling and no separate warning.

## 6. The false positive the widening created, and how it was caught

Widening a pattern can only ADD matches, so the added set was measured rather
than assumed: every token in the readers' scope matching `AIF-\d{4,}` or
`AIF-\d{1,2}`, and every token matching `R0*\d{4,}`.

  - R: **zero** across all ten `SCAN_DIRS` and all five suffixes. The widened R
    pattern matches exactly what it matched before.
  - AIF: **one**, and it was real.
    `docs/maintenance/SESSION_CLOSEOUT_AIF112_PHASE1_AND_LOCK_MUTUAL_EXCLUSION_2026-08-15.md`
    line 60 writes `AIF-11{6,7}.claim` -- a brace-expansion shorthand for the
    PAIR 116 and 117. `{` is a non-word character, so `\b` matched `AIF-11`
    and resolved it to **AIF-011**, a real number wrongly cited.

**The old three-digit pattern missed that by accident. The widened one has to
decline it on purpose**, so the three PROSE scanners carry `(?!\{)`. The
row-anchored patterns do not need it and did not get it: a row id sits at line
start and is followed by a pipe.

`session_coordinator` could not express the rule in its `git grep` because
POSIX ERE has no lookahead, so grep now returns whole LINES and the Python
pattern is the single extractor. One rule, one place.

## 7. Verification

    Every reader, on 043 / 128 / 999 / 1000 / 12345 / 999999 / 43
        all nine resolve to the same integer; MISS count 0.
        AIF-043 and AIF-43 both resolve to 43 -- one number, not two.

    Live tree, old binary vs new
        aif_collision_gate   output IDENTICAL
        check_aif_claimed    output IDENTICAL
        ecoschema.load_intake 125 keys, values identical
        lane.LANE_RE         AIF-085 accepted, AIF-85x and AIF- still rejected
        session_coordinator  git_committed_aifs 128, working_tree_aifs 125,
                             claimed_aifs 60, taken() 128 -- symmetric
                             difference EMPTY on every one; next free 129
                             before and after.

    Brace shorthand          'AIF-11{6,7}.claim' -> []   (was -> 11)
                             'AIF-116' -> [116], 'AIF-1000' -> [1000]

    py_compile clean on all nine; ASCII clean.

`next_r.py` itself was NOT run end to end here: it walks 1,884 files and the
sandbox shell caps at 45 seconds. Its equivalence is established by exhaustion
over its own declared scope instead -- zero `R0*\d{4,}` tokens exist in it --
which is a stronger statement than one diff, and the limitation is recorded
rather than glossed.

## 8. A near-finding that the measurement refuted

While reading the allocators it looked as though the two disagreed on the
allocation RULE: `next_aif.py` rules "max + 1, NEVER the lowest gap", while
`session_coordinator.claim_aif` takes the lowest free number in its range. Two
allocators, one sequence, different rules -- the R5 shape, in the most
consequential place it could sit.

**Measured before it was written down, and it is not a live defect.**
`session_coordinator.taken()` scans committed docs, the working tree and the
claim ledger, and returns 128 numbers with **no gaps below the high-water
mark**, so both tools answer 129 today. `next_aif`'s reported gaps -- AIF-89,
AIF-102 -- are gaps in the narrower intake-union only; the wider scan finds
them cited and treats them as taken.

The divergence is LATENT, not active: it would appear the first time a real
gap opens. Recorded, not filed. **A correct reading of two rules does not
license the claim that they have produced a wrong answer.**

## 9. Good neighbour

    What changed:      nine tools' read patterns, one allocator ceiling
                       (999 -> 999999, with a lazy candidate generator so the
                       wider bound costs nothing), and three prose scanners
                       gaining a brace-shorthand exclusion.
    Whose area:        shared coordination tooling, read by every lane.
    Authorization:     member.derald, 2026-08-25, "do it".
    How to verify:     section 7. The one-line check is that
                       `| AIF-1000 |` and `| R1000 |` now resolve, and
                       `AIF-11{6,7}` does not.
    How to undo:       revert this commit. No number was consumed, no corpus
                       file re-padded, no data migrated.

## 10. This document is read by the readers it describes, and that costs four numbers

`session_coordinator.git_committed_aifs` greps the whole of `docs/` at HEAD, so
the two files carrying this ruling are themselves scanned for AIF citations.
Measured after writing them and before committing:

    AIF-0        from the regex text `AIF-0*(\d+)` quoted in both files
    AIF-999      from the sentence about the old allocator bound
    AIF-1000     from the reader measurement table
    AIF-999999   from the new allocator bound

Those four join `taken()`. **Allocation is unaffected** -- `claim-aif` and
`next_aif` both still answer 129, and the fourteen other numbers these
documents mention were already taken. But AIF-999 and AIF-1000 are now
permanently spoken for by the document that explains why they would have been
unreachable.

**ACCEPTED, not worked around.** It is consistent with the doctrine already in
force -- a number written down is spoken for, and gaps are reserved rather than
reissued -- and the two burned numbers are roughly 870 away from the frontier.
Rewording the ruling to hide its own examples would make it worse to read in
exchange for nothing. **Recorded here so that whoever reaches AIF-998 finds the
reason instead of a mystery.**

If that trade is ever judged wrong, the fix is a suppression marker for AIF
citations mirroring `cite-check:ignore` in `tools/staging/check_cited_paths.py`
-- deliberately NOT built here, because new machinery on the strength of two
numbers is the wrong trade today.
