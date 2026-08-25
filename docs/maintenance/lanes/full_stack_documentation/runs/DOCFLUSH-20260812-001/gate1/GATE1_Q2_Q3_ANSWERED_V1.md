# Gate 1 -- Q2 and Q3 answered

    Run    : DOCFLUSH-20260812-001 (flush v5) / COWORK-20260825-001
    By     : member.ai.claude.cowork (ALPHA), for member.derald
    Date   : 2026-08-25
    Status : **Q1, Q2 and Q3 all answered. Gate 1's questions are closed;
             one inherited action is blocked on coordination.** review-needed.

---

## 1. Both questions had a premise that measurement corrected

Q1's hypothesis was refuted by one grep. Q2's and Q3's framings were also off,
in the same direction: each assumed something absent that turned out to be
present, or present-but-different.

## 2. Q2 -- foxref and FILE(). ANSWERED: a pointer entry.

**The framing was "add an entry recording the deliberate divergence, or leave
foxref silent". The divergence was already recorded.**
`src/cli/expr/function_catalog.cpp:446`:

> "Deliberately broader than VFP's files-only FILE(): returns .T. for any
> filesystem entry, directories included -- 'nothing means nothing' fails on a
> leftover empty directory too."

with the path-slot semantics at :452. That is the function authority, and it is
what feeds HELP.

**MEASURED:**

    foxref.hpp divergence language of any kind    0 occurrences
    foxref.hpp Item struct                        {name, syntax, summary, supported}
                                                  -- no divergence field exists
    foxref function entries                       31, ALL VFP-identical in meaning
    FILE in foxref                                ABSENT entirely

**So both options in the original framing were wrong.** Writing the divergence
into foxref would create a second home for one fact -- the R5 shape -- in a
header with no concept of divergence. But silence was wrong too: foxref is
where a FoxPro reader looks, and with no entry at all they cannot distinguish
*"x64base does not have FILE()"* from *"x64base has it, differently"*. **Absent
and present-but-different rendering identically is R6.**

**RULED (owner, 2026-08-25): a POINTER, not a duplicate.** The entry says FILE
exists, is supported, and deliberately differs, and sends the reader to the
function catalogue for the divergence itself. One home for the fact; foxref
stops being silent about existence.

    VERIFIED: refcheck exit 0. foxref 175 -> 176 entries, fn 28 -> 29,
    GUARDED phantoms 0 -- FILE resolves as a function, so the guard that would
    have caught an invented name confirms this one is real.

## 3. Q3 -- `risk:` blocks. ANSWERED, and it is bigger than recorded.

The envelope measured "risk keys appear 0 times in built HELP DATA" and filed
it as *"a lane question, not a defect; recorded so nobody writes more expecting
them to surface."*

**The zero is confirmed. The "nobody writes more" is not: 206 files carry a
`risk:` block.** That is most of the contract corpus -- 231 files carry
`@dottalk.usage`. Authors are writing them at near-total coverage, and none of
it is retrievable by any operator.

**And the blocks are not prose. They are `key: value` -- which is the problem:**

    mutates_table_data   182 uses, 16 distinct values
    mutates_cursor        43 uses, 14 distinct values
    requires_open_table   38 uses,  5 distinct values
    ...then a tail of roughly 250 keys, MOST USED ONCE

    mutates_table_data:  no (158)  yes (5)  depends (6)  delegated  indirectly
                         schema  edit  create  filesystem-level  interactive
                         on  IMPORTSQL  VALIDATE  REPAIR
                         create/add/insert/move/delete/rebuild

Several of those are not values -- they are the first word of a wrapped
sentence. **It looks machine-readable and is not, which is worse than looking
like prose**, because nobody writes a parser for a paragraph and everyone
writes one for `key: value`.

**RULED (owner, 2026-08-25): harvest as PROSE now, close the vocabulary
later.** Mine `risk:` into HELP as a NOTE-like kind with NO key semantics, so
206 files of safety notes stop being invisible, while claiming nothing about
what the keys mean.

**BLOCKED ON COORDINATION, NOT ON A DECISION.** The act needs
`src/help/helpdata_source_miner.cpp` changed and the HELP store rebuilt, and
`dottalkpp/data/help/*` belongs to a concurrent session -- reads only for this
lane. **It must be scheduled with that session, not taken.** Recorded rather
than attempted.

## 4. What Q3 produced: AIF-129

`status=` (R127 (b)) and `risk:` are the same defect one sub-block apart, in
one corpus, written by the same authors. **Owner ruling: one lane, both
vocabularies** -- AIF-129,
`docs/maintenance/lanes/full_stack_documentation/AIF129_CONTRACT_SUBBLOCK_VOCABULARIES_V1.md`.

`status=` is REPAIR (R127 (b) already made it decide whether a command is
supported). `risk:` is PREVENTION (zero consumers, so it misleads nobody yet;
the defect is that it is ready to be consumed wrongly).

## 5. Gate 1 status

    Q1  ANSWERED 2026-08-25. Hypothesis REFUTED -- the miner scans ./src
        recursively. The reframed question is BLOCK WELL-FORMEDNESS: 231 files
        carry @dottalk.usage, @dottalk.end appears 17 times tree-wide, the
        ad-hoc build mined 205. STILL OPEN as a measurement, and the next step
        is to mine and count UNDER OBSERVATION, not to reason further.
    Q2  ANSWERED and IMPLEMENTED this commit.
    Q3  ANSWERED. Implementation blocked on coordination; lane chartered.

**Gate 1's questions are closed. Gate 1 itself is not**, because Q1's reframed
measurement has not been run. That distinction is kept deliberately: a gate
whose questions are answered is not a gate that has been executed, and the
envelope for this run has said Gate 1 was never executed since 2026-08-12.

## 6. Good neighbour

    What changed:      include/foxref.hpp gains one pointer entry (Q2);
                       AIF-129 chartered and claimed (Q3); this record.
    Whose area:        full_stack_documentation / AIF-067 for foxref; the HELP
                       miner and store are OUT of scope and are named as such.
    Authorization:     member.derald, 2026-08-25 -- three rulings taken from
                       options: pointer entry, harvest-as-prose, one lane.
    How to verify:     `refcheck_v1.py` exit 0 with foxref 176 / fn 29 /
                       phantoms 0; section 3's counts reproduce by parsing
                       `risk:` blocks out of src/**/*.cpp.
    How to undo:       tmp/foxref.hpp.bak, or revert. AIF-129 stays spent.
