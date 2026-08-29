# R131 -- A WORKSPACE OWNS ITS ENVIRONMENT, AND `SET PATH` IS HOW IT GETS ONE

    ruling  : R131
    date    : 2026-08-29
    kind    : ruling
    lane    : AIF-078
    ruler   : member.derald (owner)
    author  : member.ai.claude.cowork, run COWORK-20260829-001
    status  : review-needed -- the author does not self-approve
    build   : dottalk++ v0.6 (2026-08-29, c7c94e18)

## 1. The ruling

Owner, 2026-08-29:

> "allow workspace `new` for parallel workspaces, without the parent, or child
> annotation. Once we have a new named workspace, we switch to it and then we
> can set the environment etc. before an open"

So the sanctioned sequence for standing up a second system is FOUR STEPS:

    WORKSPACE NEW <name>        -- parallel sibling, no UNDER
    WORKSPACE SWITCH <name>     -- it becomes current
    SET PATH DBF|INDEXES|LMDB   -- THE ENVIRONMENT BINDS TO THAT WORKSPACE
    WORKSPACE OPEN ...          -- fill it

**THE NEW RULE IS THE THIRD LINE.** `SET PATH` retargets the CURRENT
WORKSPACE, not the session. Everything else in the sequence already works.

## 2. WHAT THIS RULING DOES NOT CHANGE, stated first so it is not credited

`WORKSPACE NEW <name> [UNDER <parent>]` -- the UNDER clause is ALREADY
optional and parallel siblings are ALREADY the default. Measured 2026-08-29:
`workspace new workspaces` produced `handle 4  name workspaces  parent 0
depth 0  WS_ID 267`. No code is required to "allow" it.

Naming that matters, because a ruling that appears to grant something already
granted invites a reader to look for the change in the wrong place. **The
change is that the environment acquires an owner.**

## 3. The hole this closes

Measured and recorded the same day (`open_mcc_and_cascade.dts`, and the
session that produced it):

- The three path slots -- DBF, INDEXES, LMDB -- are GLOBAL.
- `WORKSPACE SWITCH` moves MEMBERSHIP and does NOT move them.
- So with MCC and CASCERP both open, `SET ORDER TO TAG SID` on MCC's STUDENTS
  answered `openCdx: LMDB env missing:
  ...SYSTEMS\CASCADE_ERP\LMDB\STUDENTS.cdx.d` -- an MCC table resolved under
  the Cascade bundle, because Cascade was opened last.
- Both systems stay READABLE either way. What breaks is anything that must
  RESOLVE a container or an LMDB env.

Consequence today: a switch is FOUR LINES, not one, and the script that opens
two systems has to say so in its own output.

## 4. The engine already named the answer, twice, and deferred it

**`cmd_workspace.cpp:4773`**, on why the origin map records rather than
derives:

> THE MEMBERS CANNOT ANSWER IT. Deriving the origin from where member 0's file
> lives works UNTIL THE WORKSPACE IS EMPTY, and an empty workspace would then
> answer the same as a mismatched one -- R6, the same defect one layer down.

**`cmd_workspace.cpp:4779`**, four lines later:

> SESSION-LOCAL AND STATED AS SUCH: this is a process map, not a catalog
> field. ... **WORKSPACES.dbf carries DBF_ROOT and is the place a durable
> answer belongs; wiring that is not this change.**

**R129, "ALSO NOT RULED"**: `WorkspaceIdentity::profile_path`, *"a declared
field with NO writer and NO reader anywhere in the tree and the natural home
for per-workspace environment"*.

**THE EMPTY WORKSPACE IS THE STATE THAT FORCES THIS.** The owner's sequence
switches into a workspace with no members, and a workspace with no members has
nothing to derive an environment from. That is the same reason the origin map
exists, one level up: an empty workspace cannot answer where it lives, so
somebody has to TELL it. This ruling makes `SET PATH` the telling.

## 5. THREE CANDIDATE HOMES, AND THEY ARE NOT THE SAME THING

Named a month apart by different hands and never reconciled:

| home | file | what it is |
|---|---|---|
| `profile_path` | `include/reference/data_address.hpp:32` | a field on an ADDRESSING type |
| `DBF_ROOT` / `IDX_ROOT` | `WORKSPACES.dbf` | DURABLE catalog columns, already present on every row |
| the live `Entry` | `include/xbase/workspace_membership.hpp` | RUNTIME membership, where `owner_of_slot` went |

**MEASURED 2026-08-29:** `profile_path` has ONE declaration, ZERO writers, and
TWO readers -- `unspecified()` and `operator==` in `data_address.cpp:45,50`.
It is not merely unused: it participates in EQUALITY, so two workspaces with
different environments compare EQUAL today. R129 recorded "no reader", which is
very nearly right and worth correcting to "read only by code that asks whether
it is empty, which it always is".

**NOT RULED HERE, and it is the implementation's central question.** R129's own
finding argues these are different axes -- it separated RESOLUTION from
NAVIGATION for exactly this reason -- so the live roots and the durable roots
may legitimately be two things that are SAVED into each other rather than one
thing stored twice.

## 6. WHAT THIS RULING MAKES LOAD-BEARING: AIF-138

**`WORKSPACE SWITCH` DOES NOT DO WHAT R129 RULED.** R129 sec 6.1 ruled that
SWITCH moves `_current` to the target's lowest member so the two authorities
agree. Measured 2026-08-29, the whole body is:

    xbase::workspace::set_current_handle(h);
    std::cout << "WORKSPACE SWITCH: current handle " << h ...

R129 states "NO CODE WAS WRITTEN" and none has been written since.

So in the window this ruling opens -- between SWITCH and OPEN -- the session
sits in a workspace with NO members while `currentArea()` still points at the
PREVIOUS workspace's table. `current_handle()` and
`area(currentArea()).wsHandle()` disagree, which is the R5 divergence R129
measured, and anything reading "the current area" in that window acts on a
FOREIGN table: LIST, DBAREA, and `infer_parent_from_workarea()`, which is the
AIF-137 path.

**AIF-138 MOVES FROM LATENT TO BLOCKING.** An empty workspace has no lowest
member to move to, so R129 6.1 cannot be implemented until the area cursor can
say "nothing" in its own value. This ruling's sequence REQUIRES occupying that
state deliberately, every time a workspace is built.

**THE INSTRUMENT FOR THE WINDOW ALREADY EXISTS, by accident.** DBAREA and GPS
gained an owning-workspace line beside the current-workspace line on
2026-08-29 (same session, owner instruction). It was built for the
SELECT-across-workspaces case and it reports THIS divergence from the other
side: `Owning workspace : MCC handle 2` beside `Current workspace : NEWWS
handle 4` names the window while you are standing in it.

## 7. Q1 IS RULED: THE EXPLICIT CLAUSE, AND NO PROMPT

**THE GRAMMAR GAINS ONE FORM**, owner 2026-08-29:

    SET PATH <slot> <value>                    -- binds to the CURRENT workspace
    SET PATH <slot> <value> IN <ws-or-handle>  -- binds EXPLICITLY

The bare form keeps today's behaviour exactly, silently. The explicit form is
how a caller says which workspace it means, and it is the whole answer to the
misordering hazard: `NEW -> SET PATH -> SWITCH` binds to the OLD workspace,
and the remedy is to name the target rather than to rely on standing in it.

**`IN` IS ALREADY THE HOUSE WORD FOR "TARGET SOMETHING OTHER THAN CURRENT"** --
`SET ORDER TAG <tag> IN <alias>` (`cmd_setorder.cpp:19`) and
`USE <table> IN <n>` (AIF-121). Both take AREAS. After `SET PATH` it can only
mean a workspace, because paths have no per-area meaning, so the keyword is
reused without a namespace collision.

**A y/n PROMPT WAS PROPOSED AND WITHDRAWN THE SAME DAY, and the reason is worth
keeping.** The first form of this ruling was *"Reset path(s) in current
workspace? (y/n)"*, fired only when more than one workspace is open. It was
withdrawn on measurement: **THIS ENGINE HAS NO SCRIPT-MODE PROMPT
SUPPRESSION.** `g_suppress_prompts` (`src/cli/dirty_prompt.cpp:27`) is set only
on the QUIT path and by one local save/restore; `DOTSCRIPT` never touches it.
So a prompt inside a `.dts` reads from the console -- it blocks, or it consumes
the next script line as its answer.

**AND IT WOULD HAVE BITTEN ON THE FIRST SCRIPT WRITTEN AGAINST THIS RULING.**
`dottalkpp/data/scripts/open_mcc_and_cascade.dts` sets the Cascade roots WHILE
MCC IS ALREADY OPEN -- two workspaces, no `IN` clause -- so it would have
prompted mid-script, in a file that is a candidate for the regression suite.

A gate was available (`g_dotscript_depth`, `cmd_dotscript.cpp:340`, already
thread-local and already counted for the nesting limit), so the prompt COULD
have been made interactive-only. The owner dropped it anyway, and the simpler
rule is better: **one grammar, no mode-dependent behaviour, and no verb that
does something different depending on who is typing.**

**OPTIONAL AND NOT RULED:** `SET PATH` already prints `SETPATH: DBF = <path>`.
Naming the workspace it bound to on that existing line costs nothing and is
this house's habit for state changes. Take it or leave it; it is not a prompt
and creates no script hazard.

## 7a. Q2 REMAINS OPEN -- WHAT ARE A NEW WORKSPACE'S ROOTS BEFORE ANY SET PATH?

**Author's recommendation: (a) INHERIT**, for the same reason AIF-148 puts
`OrderBackend::Natural` at the floor -- NO STATE WITHOUT AN ANSWER. Empty roots
is a question with no answer, which is the shape this lane keeps finding, and
inheriting makes the change strictly additive so no existing script alters
behaviour. Not ruled; recorded so the reasoning is not re-derived.
 Two answers, and
the ruling on the TREE does not decide it -- "no parent, no child" is about
nesting, and this is a different kind of inheritance:

  (a) INHERIT whatever is current at NEW time. Never unresolvable;
      `WORKSPACE OPEN dbf` always has something to resolve against.
  (b) START EMPTY. `WORKSPACE OPEN dbf` refuses until told where to look,
      which makes the sequence's third step mandatory rather than customary.

(b) is the stricter reading of the owner's sentence -- "we CAN set the
environment before an open" describes an expectation. (a) cannot produce a
state with no answer. They differ only for a caller who skips step 3.

## 8. Not ruled, named so they are not settled by drift

- Which of the three homes in sec 5 carries the roots, and whether live and
  durable are one thing or two.
- Whether DEFAULT's roots are the INIT slots by definition, and what happens
  when someone SET PATHs while standing in DEFAULT.
- Whether `WORKSPACE OPEN <dir> AS <name>` should also RECORD the three roots
  it resolved against, since it knows them at that moment for free. The
  session-local origin map already records ONE string (the directory) and is
  read only for re-entry detection.
- What retires the four-line switch idiom in `open_mcc_and_cascade.dts`, which
  is a workaround this ruling is meant to make unnecessary.

## 9. NO CODE WAS WRITTEN FOR THIS RULING

`src/cli/**` and `src/xbase/**` are engine and want an explicit go. The
measurements cited here were taken on build `c7c94e18` during the session that
produced the ruling; every source claim is a read at that HEAD.

Ships **review-needed** -- the author does not self-approve.
