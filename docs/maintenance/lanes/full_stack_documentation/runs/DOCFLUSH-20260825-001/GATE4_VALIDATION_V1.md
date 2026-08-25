# v6 Gate 4 -- execute and validate, and what 6' still cannot see

    Run     : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Store   : rebuilt 2026-08-25 15:30 LEGACY -> 15:36 current
    Against : dottalkpp/data/help.bak-20260825-152718 (pre-run, 15:27)
    Status  : review-needed. 6' GREEN. 1' UNUSABLE, see section 3.

## 1. Assertion 6' -- topic SET diff. GREEN, and it named its departure.

    topic-set diff against dottalkpp/data/help.bak-20260825-152718
              GAINED FOX|FILE
              net +1  (665 -> 666)
    RESULT: clean

**ZERO LOST is the load-bearing half.** It is the result that would have
falsified the reasoning, and it did not.

The single gain is dispositioned: `FOX|FILE` entered `include/foxref.hpp` in
`6bcb5bb30` earlier the same day. The pre-run store was built 2026-08-24 19:47
by an exe that predated that commit, so the topic could not have existed in it.
Expected, explained, accepted.

This is 6' doing exactly the job the count floor could not. On 2026-08-24 the
floor scored a REPAIR as a regression because a total fell 530 -> 526. Here the
total ROSE by one and the reason is a named row, not a number.

## 2. THE LIMIT FOUND BY EXERCISING IT: a SET diff cannot see a SUBSTITUTION

The `include/dotref.hpp` repair committed in `c8aa6a583` is **invisible to 6'**,
and it is worth being precise about why.

`BUILD VECTORS` and `BUILD INFO` were topics BEFORE the run and topics AFTER it.
Before, they were generated placeholder rows -- `supported=no`, summary "is a
registered DotTalk++ command; curated DOTREF support status and help summary are
pending". After, they are catalog rows -- `supported=yes` with real text. The
topic KEY did not move, so:

    the count floor       sees nothing   (461 rows before, 461 after)
    the topic SET diff    sees nothing   (same keys before, same keys after)
    a content diff        sees it        (2 rows of 461 changed)

**Both adopted assertions are blind to the class of change this run actually
shipped.** That is not an argument against 6' -- it is strictly better than the
floor and it caught the FOX|FILE gain honestly. It is an argument that 6' must
be described as what it is: **a membership check, not a content check.** Anyone
reading "topic-set diff clean" as "the store is unchanged in substance" is
making the same inference error the floor invited.

The gap is real but it is NOT urgent, because the substitution here was proven
another way: an A/B build in a container, comparing `CMDHELP BUILD LEGACY`
output with and without the 13 changed lines, showed exactly two rows differing
out of 461. That is a content diff, run outside the gate. A content-level
assertion belongs in v7; the workaround until then is to diff the CMDHELP
listing, with the id column stripped -- ids renumber on insert and a raw diff
read 676 lines for a 2-row change.

## 3. Assertion 1' is UNUSABLE and should not be counted as adopted

1' is "the banner names a commit and is NOT `dirty`". Measured this run:

    dottalk++ v0.6 (2026-08-24, c39d966c dirty)  (Aug 25 2026 10:57:03)

`c39d966c` is from the previous day. The binary provably contains `c8aa6a583`
-- `BUILD VECTORS` renders `yes yes` with its real summary, which only the new
catalog can produce.

Cause: `CMakeLists.txt:59` reads git inside `execute_process`, which runs at
CMake **configure** time. `cmake --build` never refreshes it. The banner
therefore reports the worktree state at the last configure, not at the build
that produced the binary.

**The dangerous direction is the opposite one.** Configure on a clean tree,
then edit source and `cmake --build`: the banner reports a named commit and no
`dirty` flag while the binary carries uncommitted code. That is a FALSE GREEN on
the assertion adopted specifically to catch the 2026-08-12 "exe built from a
dirty worktree" failure -- a proxy that cannot answer the question put to it,
which is the family that already cost this lane three withdrawn assertions.

Until the stamp is a build-time step, the runnable substitute is the one the
sandbox handoff already prescribes -- grep the binary for a string only the
change under test introduces:

    grep -c 'Spaced spelling of BUILDVECTORS' build/src/Release/dottalkpp.exe
    1

That answers "is my change in this binary" directly, with no stamp in the path.
It is narrower than 1' intended to be and it is TRUE, which 1' currently is not.

## 4. Assertion 5b remains retired

Withdrawn as malformed in v5: an `EDREF` HELP_LINE row count cannot witness a
change landing in `HELP_TOPIC.TITLE`. Nothing this run changes that.

## Good Neighbor

    What changed  : one new document in this run's own directory. No source, no
                    data, no store, no rebuild.
    Whose area    : lane full_stack_documentation, run DOCFLUSH-20260825-001.
    Authorization : the owner's instruction of 2026-08-25 to keep going through
                    the phases and note minor items for v7 rather than stopping.
    Verify        : $py12 tools\coordination\help_store_check.py --against dottalkpp\data\help.bak-20260825-152718
                    expect RESULT: clean, GAINED FOX|FILE, net +1.
    Undo          : delete this document; it asserts nothing the store does not.
