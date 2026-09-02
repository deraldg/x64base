# Flush field notes -- the diagnoses behind the cookbook's warnings

    written  2026-09-02
    purpose  Keep the reasoning without putting it in the runbook.

`FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V2.md` is meant to be RUN. Every warning
in it is one line, because a runbook you have to read around is a runbook people
stop reading. This page holds the evidence those one-liners compress.

**Nothing here is required to execute a flush.** It is here because the cookbook's
rules look arbitrary without it, and a rule whose reason is lost gets dropped by
the first person in a hurry.

## Why "a green gate is not a reviewed change"

Four Gate 4 acceptance plans were built on 2026-09-02. Three were discarded.
**All four reported `PASS_PLAN_ONLY findings=0`.**

    472B26D9   would have corrupted text
    CBC1CCB6   would have welded lists
    (a third)  missed the SUMMARY render path entirely
    EEB3A07B   applied

The first joined 240-byte field spills with a space. `HELP_LINE.TEXT` is a
fixed-width field, so a long line is cut MID-TOKEN; joining with a space turned
"not the command name." into "not the comm and name." and "(AIF-043)." into
"(AIF-04 3).". Six rows affected, three of them in topics with no page among the
164, so half the damage was latent.

The second had no minimum line length, so it fused list items into sentences:
`model.md` tables/records/fields/indexes/relations, `expression.md`
numeric/character/date/logical, `buffering.md` working state / persisted state.
About thirty items across eight pages. The list introducer ends in a colon, which
correctly stopped the FIRST item being absorbed -- which is why the damage started
at the second item and read like prose.

**The measurement endorsed all three.** Fragment count went 399 -> 0 at store
level, then 114 -> 46 -> 21 across rendered pages. Every number was true. None
could see the defects, because a corrupted or welded join lowers the fragment
count exactly like a correct one.

That is the general form: **the metric moved with the intervention rather than
with the goal.** It is the same shape as AIF-118 -- a check that returns the same
answer whether the thing is right or wrong.

What worked was partitioning: diff each staged file against its accepted
counterpart, assign every difference to a named class, count each class, and
require zero unexplained. Plus a whole-file assertion that text is preserved
exactly. The final plan partitioned as 164 byte-identical, 1 marker change, 3
JSON artifacts, 0 unexplained.

## Why "fix at the producer"

The ASCII rule blocked a commit over three U+26A0 in the generated
command-reference README. The demand could not be satisfied in its own terms: the
only way to make a rendered page ASCII-clean is to change the generator or its
source. Editing the page is undone by the next regeneration.

**A rule whose fix is guaranteed to be overwritten produces a bypass**, and it
did -- OI-026, committed with `--no-verify`.

The correct scoping already existed in the checker, above `PRUNE`, written for
the `--audit` walk: "mostly vendored and generated text that nobody authored and
nobody should edit." It had been applied to the reporting mode and never to the
enforcing one.

This generalises past ASCII. **Classify the artifact before choosing where to
enforce.**

## Why the manual reassembly is not a heuristic

An early fix detected 240-byte spills by measuring line length against a
hardcoded constant and guessing at the separator. It was reimplementing, worse, a
mechanism whose own source comment says:

> HELP_LINE IS A PSEUDO-MEMO, AND THAT IS DELIBERATE. DO NOT "FIX" IT. ... one
> logical line is split into 240-byte PARTS across numbered rows, and the reader
> reassembles by LINE_NO + PART_NO

`src/help/helpdata_export_dbf.cpp`, measured 2026-08-25. The counts derived by
hand during the flush -- 6 rows at exactly 240, PART_NO 1/2/3 = 29693/6/1 -- are
printed in that comment. It also predicted the misreading: "An agent reading
LINE_NO / PART_NO / TEXT(240) cold reads it as an implementation quirk -- one did,
the same week." Two did.

The owner's question, "do we have a simple problem of needing longer fields?", is
what sent the session to the producer. The answer is no. The field is not too
short; it is a memo written in the vocabulary dBase III had, and it is barely
exercised -- seven continuation rows out of 29,262.

## Why null results are recorded

Six of the twelve remaining disposition-derivation disagreements are
`MERGE_ALIAS_TO_CANONICAL`. Space-versus-underscore normalisation was the obvious
suspect: the harvest spells topics with spaces (`APPEND BLANK`, `LMDB UTIL`), the
registry with underscores.

It was implemented and measured. **It changed nothing.** Those six share no
handler with anything, so `registry_handler_map` cannot pair them however the
names are spelled. The table knows an alias relationship that exists nowhere in
the registry.

That is a ceiling on the derivation, not a bug in it. The normalisation was kept
(it is correct in principle) and the null was documented, so the next reader does
not spend the same hour reaching the same nothing.

## Why claims in our own records get verified

Three times in one day, a claim in this repo's records turned out to be prose
mistaken for evidence.

**One.** A run record said RPG, TRIGGER, VMWARE, VT200 and TTESTAPP "each carry a
`command:` usage contract, verified by grep". They do not. The grep had matched
the PHRASE "@dottalk.usage contract" inside a sentence saying one would be needed:
"add the runtime command handler and a @dottalk.usage contract IN THE SAME COMMIT
as the handler." A later session implemented against that claim and caught it only
because the predicate resolved nothing.

What those files actually carry is `@dottalk.pdlc` with `planned-command:` and
their own statement: "Not counted as a command surface -- `planned-command` is not
harvested into SYSCMD/HELP/dotref." Which is precisely why the derivation could
not see them and the hand-kept table could.

**Two.** A run record and a commit message both said "eight unit cases now cover
it" while nothing in `tools/manualgen/tests/` referenced the function. The cases
had been reasoned through and never committed. Caught by grepping for the symbol
before opening a second Gate 4 cycle.

**Three.** The publication gate reported "catalog drifted from source" against a
clean catalog, because the version guard and real drift share an exit code.

**The pattern is not carelessness.** A grep that matches discussion of a thing
looks identical to a grep that matches the thing. That is why the cookbook says
to read what a check actually compared.

## Why the accepted manual is now tracked

From the 2026-07-18 acceptance until 2026-09-02, the accepted command reference
was NEVER IN GIT. All 165 pages landed as `create mode`. The reader page was
tracked; the 164 pages it links to were not, so nothing looked wrong from either
end.

Every Gate 4 apply in that window wrote into files git could not see, **which
means no apply could be reviewed as a diff** -- and that review is what caught
three bad plans on the day it was discovered. "Kept recoverable" was an assumption
nobody had tested.

`check_manual_link_integrity.py` now asserts it, hard, as prepush portal check 5d.
It confirmed live at `f3dcfa6fb`.

The same defect was then reintroduced in a second surface the same day: two Lab
pages were added to the website content manifest while untracked, and that gate
passed because it validates against the filesystem rather than git. See
`GATE_CORRECTIONS_REQUIRED_V1.md` G3.

## Why status vocabulary is being split

242 `@dottalk.usage` contracts declare **24 distinct status values**, and sorting
them by the question they answer shows one field doing five jobs: audience,
completeness, mechanism, lifecycle, process. `supported` at 178 is the default
that swallows whatever the vocabulary cannot express -- which is why
`supported-stub-mixed` and `supported-conditional` exist.

The consequence reaches the reader. Of 109 published commands that also declare a
contract status, **33 disagree with the manual, all in one direction**: the manual
says `supported` while the contract says `experimental`, `developer`, `stub`,
`sample-extension` or `deprecated`. `LMDB_UTIL` declares itself deprecated and is
published as supported.

Uniform direction is the informative part. Scattered staleness points both ways;
one direction means nothing is comparing them.

`AREA51` is the canary: its own contract prose already read "It read `supported`
until 2026-08-30 while THIS PARAGRAPH already called it a developer probe." The
author caught it on one command. The systemic count is 33.

Glossary rows TERM.CONTRACT.AUDIENCE / COMPLETENESS / LIFECYCLE / SUPPORTED were
proposed 2026-09-02, with two values already ruled by the owner: SQL and SQLSEL
are `in-progress` ("actively developing ... not a claim of completeness") and
TVISION is `template`, not `stub` ("a working template").

## Why the dev-mode warning in start-ai.ps1 is kept after the fix

The gateway could not carry a WebSocket upgrade, so `next dev` behind :3000 never
hydrated. Measured: 3 of 490 elements had a React fiber via :3000, against 445 of
493 on :3002 direct. Every client component was inert.

**Nothing errored.** The HTML arrived byte-identical, every chunk loaded, the
console was clean, and the page looked perfect. The only tell was that
`[HMR] connected` appeared on :3002 and never on :3000. It cost five rounds of
"fixing" a theme button that had never been able to run a click handler.

Fixed and verified live 2026-08-16 (AIF-118, `57de30b35`): 436 of 493 elements
hydrated on :3000.

The diagnosis is kept in the script after the fix, deliberately, and the script
says why: "it is how you recognise this shape the next time something looks
perfect and does nothing."

**That is the same shape as four green Gate 4 plans and a publication gate
reporting drift on a clean catalog.** Three instances in one day of a thing that
looks right and is not. It is the most valuable pattern in this lane, and it is
why the cookbook's rule 2 exists.
