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

Eight unit cases now cover it, including a numbered-list guard.

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

### (a) The rules do not check for a usage CONTRACT

Thirteen disagreements are the table saying `DEFER_NO_RUNTIME_IDENTITY` where the
rules say `ROUTE_SOURCE_FACT_APPENDIX`. Those are different claims:
DEFER means "a real command, deferred"; ROUTE_SOURCE_FACT means "not a command at
all". Verified by grep: `RPG`, `TRIGGER`, `VMWARE`, `VT200` and `TTESTAPP` each
carry a `command:` usage contract in their own `cmd_*.cpp`.

So the table encodes a fact the derivation never looks at, and that fact IS
measurable. Adding a `has_contract` predicate should resolve most of these
thirteen. That is the single highest-value improvement.

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
