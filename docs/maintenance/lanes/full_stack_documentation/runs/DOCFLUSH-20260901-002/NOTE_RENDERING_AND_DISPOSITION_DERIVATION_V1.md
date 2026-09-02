# Two deferred items, worked: NOTE rendering FIXED, disposition derivation NOT READY

    run       : DOCFLUSH-20260901-002 (v8)
    measured  : 2026-09-02, owner instruction "do them both"
    posture   : one FIXED with proof, one MEASURED and deliberately NOT adopted.

## 1. NOTE prose fragmentation -- FIXED

`tools/manualgen/manualgen_lib/command_reference_candidate.py`

HELP_LINE holds ONE ROW PER SOURCE LINE -- each wrapped line of a contract
comment is its own artifact (ARTID increments per line) and nothing in the schema
marks paragraph membership. The renderer emitted one bullet per row, so sentences
broke mid-clause:

    - AREA51 is a developer/debug status probe, not a member of the AREA family,
    - and `status: developer` above says so. It read `supported` until

A reader saw a list where the author wrote a paragraph.

**Fix:** `_rejoin_wrapped_prose()`, applied to PROSE_KINDS only.

    fragments  before 399   after 0
    topics hit before  56   after 0

**SYNTAX, USAGE, ARGUMENT and EXAMPLE ARE DELIBERATELY EXCLUDED**, and the
measurement is the reason rather than an afterthought: USAGE shows 1954 apparent
continuations and SYNTAX 1280, MORE than NOTE's 756. They are line-oriented --
indented command forms where a lowercase line after an unpunctuated one is
layout, not a wrapped sentence. Rejoining them would run
`WORKSPACE SAVE <name> MEMO MINIDB` into the description beneath it. The high
count is the reason to leave them alone.

**The rule is conservative by design**, because 164 pages cannot be eyeballed: a
row joins only when the previous does not end in `.!?:;` AND this one starts
lowercase or with a digit, and never when it looks like a numbered list marker.
It UNDER-joins -- a continuation starting with a backtick stays split -- and
under-joining leaves text readable where over-joining would weld two separate
notes into one false sentence.

**The digit case came from a failing test, not from foresight.** A first draft
tested only `islower()` and left the real area51 wrap split, because the
continuation begins with a date:

    ... It read `supported` until
    2026-08-30 while THIS PARAGRAPH already called it a developer probe

Nine unit cases now cover it, including a numbered-list guard.

**AND THAT SENTENCE WAS FALSE WHEN FIRST WRITTEN.** This document and the commit
message both claimed "eight unit cases now cover it" while NOTHING in
`tools/manualgen/tests/` referenced `_rejoin_wrapped_prose` -- caught on
2026-09-02 by grepping for the symbol before opening a second Gate 4 cycle. The
cases had been reasoned through and never committed to a file. A test asserted in
prose is not a test, and a run record is exactly where that error is most
expensive, because the next reader has no reason to check.

`tests/test_command_reference_candidate.py::RejoinWrappedProseTests` now holds
them, and each was mutation-checked rather than merely run green:

    rule disabled (never joins)   3 cases fail
    rule always joins             9 cases fail
    digit case removed            1 case  fails
    list-marker guard removed     1 case  fails
    unmutated                     0 fail

The last two matter most: they are the subtle arms, and a suite that passes when
you delete them is not testing them.

**A SECOND MISS, FOUND THE SAME WAY.** The first fix measured 399 -> 0 at the
STORE level and was reported as done. Counting fragments in the RENDERED pages
instead gave 114 -> 46, and the breakdown named the cause:

    SUMMARY   29     <- the largest group, and never touched
    NOTE       7        (the documented uppercase under-joins)
    USAGE      5        (deliberately excluded)
    SYNTAX     5        (deliberately excluded)

`SUMMARY` renders through its own `distinct_summaries` branch, NOT the kind loop,
so adding it to `PROSE_KINDS` would have done nothing -- the fix has to be applied
in that branch explicitly, and now is. Predicted effect on the existing candidate:
SUMMARY fragments 28 -> 5 across 8 pages.

The lesson is the measurement, not the bug: **the store-level count answered a
question nobody asked.** The reader sees pages. Measuring the artifact the reader
actually reads is what found both the untouched code path and the missing tests.

### A THIRD MISS, AND THE WORST ONE: THE FIX WAS CORRUPTING TEXT

Caught in the Gate 4 plan review for MANRUN-20260902T153114Z-472B26D9, BEFORE
apply, by diffing the 168 staged files against the accepted ones instead of
trusting the fragment count to have gone down:

    accepted: '...cmd_CATALOGCANARY is the handler, not the comm' + 'and name.'
    staged  : '...is the handler, not the comm and name.'      WRONG
    correct : '...is the handler, not the command name.'

    accepted: '...with no file on disk (AIF-04' + '3).'
    staged  : '(AIF-04 3).'                                    WRONG
    correct : '(AIF-043).'

`HELP_LINE.TEXT` is a FIXED-WIDTH 240-character field, so a long line is cut at
the field boundary MID-TOKEN, not wrapped at a word. Joining those with a space
does not merely fail to help -- it changes the words. Measured: max TEXT length
across all 29700 rows is exactly 240, nothing exceeds it, six rows hit it, and
ALL SIX were being corrupted.

The rule now has two forms, and the separator is chosen by measurement:

    previous row is exactly 240 chars -> MECHANICAL CUT, join with NO separator,
                                         and unconditionally: the next row's
                                         capitalisation carries no information
    previous row is shorter           -> word wrap, join with a single space
                                         (the conservative case rule applies)

Each of the six was inspected by hand rather than pattern-matched: `doe`+`s not`,
`n`+`ative`, `a`+`dmin`, `de`+`scribes`, `comm`+`and name.`, `(AIF-04`+`3).`.

**WHY THIS MATTERS MORE THAN THE BUG.** Both earlier measurements said the fix
was working -- store fragments 399 -> 0, page fragments 114 -> 46 -> 21. Both
were true. Neither could see this, because a corrupted join REDUCES the fragment
count exactly like a correct one. The metric was aligned with the intervention
rather than with the goal, which is the AIF-118 shape wearing a different hat: a
number that reads the same whether the thing is right or wrong.

What caught it was comparing the artifact against its predecessor and demanding
that every difference be EXPLAINED -- not counted. That check also produced the
164 provenance-only diffs and one byte-identical page, which is what a review
should look like: everything accounted for, nothing waved through.

**Also corrected while here:** the first mutation harness for these tests
reported "restored -> 2 failing", which is impossible. The harness was patching
the module namespace while the tests hold direct references, so the mutations
never applied and the counts were noise. Re-run against the test module's own
namespace: baseline 0, space-only join 2, width off-by-one 2, width disabled 3,
restored 0. A mutation harness that cannot show a clean baseline is not
evidence, and it nearly got read as one.

### APPLIED, AND VERIFIED IN THE ACCEPTED MANUAL

    plan     MANRUN-20260902T154709Z-EEB3A07B
    apply    MANRUN-20260902T155001Z-5BD6794D    PASS_APPLIED
    backup   docs/manuals/developer/manualgen/backups/
             docflush_gate4_acceptance_MANRUN-20260902T155001Z-5BD6794D
    applied_rows 168   validation_findings 0   rollback_findings 0
    reader_pointer_mutated 0   website_mutated 0

Verified by reading the ACCEPTED pages on disk afterwards, not by trusting the
apply's own status:

    canary.md      'not the command name.'      spill reassembled
    cdx.md         '(AIF-043).'                 spill reassembled
    sql.md         'does not mutate table data.' spill reassembled
    model.md       '- tables' '- records'       list intact
    expression.md  '- numeric'                  list intact
    buffering.md   '- working state' '- persisted state'  list intact
    area51.md      NOTE joined into a paragraph
    all pages      none of the six corrupted or welded forms present

FOUR PLANS WERE BUILT IN THIS CYCLE AND THREE WERE DISCARDED. Every one of the
three reported `PASS_PLAN_ONLY findings=0`, and every one would have damaged the
manual. The gate was not wrong -- it checks what it was built to check -- but a
green gate is not a reviewed change, and this cycle is the clearest evidence this
lane has produced for that distinction.

The check that actually worked, and the one to reach for next time: diff the
staged artifact against the accepted one and require EVERY difference to fall
into a named class, with an explicit count for each. Not a summary statistic --
a partition. The three classes here were provenance-only (146), prose rejoin
(18) and byte-identical (1), with zero unexplained, plus a whole-file assertion
that the text is preserved exactly on all 165 files.

**The store is not changed.** This is a rendering rule.

**NOT YET IN THE ACCEPTED MANUAL.** The 164 accepted pages were generated before
this fix. Seeing it requires re-running the command-reference candidate and a
fresh Gate 4 cycle, which is its own authorization. The fix is in the generator,
not in what a reader sees today.

## 2. Deriving REVIEW_DISPOSITIONS -- MEASURED, NOT ADOPTED

`tools/manualgen/derive_dispositions_check.py`, report-only, exit 2 on
disagreement.

    review topics            70
    covered by the table     42
    derivation AGREES        25
    derivation DISAGREES     17
    not in the table at all  28   (derived without it)
    agreement rate           59.5%

**59.5% is not good enough to retire a policy that decides manual content**, and
the honest answer to "can this be derived" is NOT YET. The disagreements say why,
and two are concrete and fixable:

### (a) The rules do not check for a PLANNED-COMMAND declaration

**CORRECTED 2026-09-02, LATER THE SAME DAY. THE ORIGINAL VERSION OF THIS SECTION
WAS FALSE AND IS QUOTED HERE SO THE ERROR IS NOT REPEATED:**

> Verified by grep: `RPG`, `TRIGGER`, `VMWARE`, `VT200` and `TTESTAPP` each carry
> a `command:` usage contract in their own `cmd_*.cpp`.

They do not, and no grep verified it. The grep matched the PHRASE
"@dottalk.usage contract" inside a sentence about needing one -- the gate text
*"add the runtime command handler and a @dottalk.usage contract IN THE SAME
COMMIT as the handler"*. **A grep that hits prose ABOUT a thing is not evidence
OF the thing.** The claim was written into this record, and a later session read
it, implemented against it, and only caught it because the predicate silently
resolved nothing.

The underlying observation was right. Thirteen disagreements are the table saying
`DEFER_NO_RUNTIME_IDENTITY` where the rules say `ROUTE_SOURCE_FACT_APPENDIX`, and
those are OPPOSITE claims: DEFER means "a real command, deferred";
ROUTE_SOURCE_FACT means "not a command at all".

What those five actually carry is `@dottalk.pdlc v1` -- a DIFFERENT vocabulary --
with `planned-command:`, `pdlc-step: design`, `proof-state: idea`, and this line
in their own words:

    Not counted as a command surface -- `planned-command` is not harvested into
    SYSCMD/HELP/dotref.

Which is exactly why the rules could not see them: the declaration is
deliberately absent from every store the derivation reads. Five such declarations
exist in the tree and they are precisely those five topics.

**IMPLEMENTED, and measured: agreement 59.5% -> 71.4%** (30 agree, 12 disagree).

### (a2) Six of the remaining twelve are NOT DERIVABLE, and that is a ceiling

`APPEND BLANK`, `LMDB UTIL`, `ORDER`, `TABLE BUFFER`, `BROWSETV` and `GENERIC`
are `MERGE_ALIAS_TO_CANONICAL` in the table. Space-vs-underscore normalisation
was the obvious suspect -- the harvest spells topics with spaces, the registry
with underscores -- and it was implemented and measured: **it changed nothing.**
Those six SHARE NO HANDLER WITH ANYTHING, so `registry_handler_map` cannot pair
them however the names are spelled. The table knows an alias relationship that
exists nowhere in the registry.

The null result is recorded deliberately. Without it the next reader tries the
same normalisation and gets the same nothing.

### (b) A handler name is not a canonicality signal

`UI|ARCTICTALK` derived as `MERGE_ALIAS_TO_CANONICAL -> FOXTALK`. Measured:

    shell_commands.cpp:210  registry().add("ARCTICTALK", ... cmd_FOXTALK(A,S); );
    shell_commands.cpp:211  registry().add("FOXTALK",    ... cmd_FOXTALK(A,S); );

Both dispatch to `cmd_FOXTALK`, so "canonical = the key matching the handler
name" picks FOXTALK -- but `include/dotref.hpp` documents FOXTALK as *"Legacy
alias for the ArcticTalk Turbo Vision TUI shell"*. **The alias direction is
backwards, and the handler name is what misled it.** Shared-handler detection
finds the PAIR correctly; deciding which member is canonical needs dotref, not
the C++ symbol.

That is a genuine finding about the registry, not only about this tool: a handler
name outliving a rename is exactly how the reflection surface acquired its own
stale `source_file` column.

### What derivation can never recover

The table's `rationale` prose. A rule can say WHAT a topic is; it cannot
reproduce a human's sentence about WHY. If the table is ever retired, those
rationales must be kept, not deleted. This session spent hours on the cost of
keeping a conclusion and throwing away the reasoning.

### Recommendation

Keep the table. Run this checker each flush as a DRIFT DETECTOR -- a
disagreement is either a stale table row or a rule that needs a predicate, and
both are worth seeing. Revisit adoption after (a) and (b), when the agreement
rate is high enough that the remaining disagreements are the interesting ones
rather than the arithmetic.

Adopting a 59.5% derivation because derivation is philosophically preferable
would be exactly the move this lane keeps warning about: replacing a measured
thing with an assumed one.
