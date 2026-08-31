# R129 -- THE WORKSPACE CURSOR: A CURSOR THAT NOTHING ELSE OBEYS IS NOT A CURSOR

    Number  : R129, allocated 2026-08-27 with
              `tools\coordination\next_r.py` -- union of the declared
              register and 126 citations in the tree, highest taken
              R128. Register row prepared and NOT self-inserted; see the
              closeout for why the two shared coordination files were
              left to the maintainer.
    Ruled   : 2026-08-27 by member.derald, IN TWO PASSES.
              Part 1, before the measurement:
              "there needs to be a workspace cursor, we have an area
               cursor and the table/row cursor already I think"
              Sections 6.1, 6.1a and 6.2, AFTER the measurement and
              after the external answers:
              "I think all in 6.x are valid, especially allowing an
               empty workspace, there will be times we want to open
               and add to it. You have to have a place to start."
              "If it turns [out] wrong we will find out quickly"
              "6.2 is valid"
    Drafted : member.ai.claude.cowork. Sections 6.1, 6.1a and 6.2
              were drafted as PROPOSALS, corrected twice, and are now
              RULED -- see the Ruled line. What each section says about
              its own drafting history is kept rather than tidied.
    Lane    : AIF-078 (multi-workspace), downstream of R128 (additive
              open), R112 (name ambiguity), R110 (WorkspacePath kept,
              reason struck).
    Reconciles with :
              AIPR-20260827-GROK-001, `WORKSPACE_IDENTITY_AND_CATALOG_
              PRECEPTS_V1.md`, co-authored member.derald + xAI Grok,
              owner-accepted 2026-08-27. THIS RULING DOES NOT RESTATE
              P6. See sec 7 -- the question that was 5.3 in the first
              cut of this document is answered there and is struck
              here on purpose.
    Status  : review-needed. The author does not self-approve.
    Basis   : source read on 2026-08-27 against the working tree at
              D:\code\ccode. Every claim is marked MEASURED (read in the
              tree, line cited), RUNTIME-PROVEN (sec 5 -- it ran, and
              sec 5 names what it ran against) or NOT MEASURED.
    Records : the design conversation of 2026-08-26/27, and the
              corrections in sec 10.

## 1. WHAT WAS RULED

**There is a workspace cursor, and it is a peer of the other two.** The owner's
words: *"there needs to be a workspace cursor, we have an area cursor and the
table/row cursor already I think"*.

That is part 1 and it is settled. What follows is what the tree says about it,
and two questions the ruling raises that are NOT settled.

## 2. THE THREE CURSORS, MEASURED

**MEASURED.** All three already exist. They do not nest the same way.

**The row cursor** is `DbArea::recno()` (`include/xbase.hpp:353`), a member of
`DbArea`. There is one per area. It nests correctly: ask a different area and
you get that area's row.

**The area cursor** is `Engine::_current` (`include/xbase.hpp:623`), one `int`
on the engine. `selectArea()` (`:615`) range-checks `0 <= idx < MAX_AREA` and
assigns. That is the whole body. `currentArea()` at `:619` reads it back.

**The workspace cursor** is `WorkspaceTable::current_`
(`include/xbase/workspace_membership.hpp:163`, free forwarder at `:469`).

So the ruling is not "build one". It is **"finish the one that is there"** --
and the reason it needs finishing is in its own comment.

## 3. THE WORKSPACE CURSOR IS A PLACEMENT CURSOR, NOT A RESOLUTION CURSOR

**MEASURED.** `workspace_membership.hpp:160-163` states the job in its own
words:

    // The workspace a newly opened area joins.

That answers **where does the next thing go**. It does not answer **which one
am I looking at**, and no resolver in the tree asks it that question.

**Four name-resolution paths, none of them workspace-filtered:**

- `find_open_area_by_name_ci()` (`src/cli/workarea_util.hpp:53`) -- **the
  main one, 36 call sites across the tree**, 21 of which the header says
  depend on its first-match-wins behaviour. This is the INSTRUMENTED path;
  sec 5 is about it.
- `find_open_area_by_alias()` (`src/cli/cmd_use.cpp:471`) sweeps
  `for (int i = 0; i < xbase::MAX_AREA; ++i)` comparing `logicalName()`.
- `find_open_area_by_alias()` again (`src/cli/cmd_codasyl.cpp:287`), a second
  function of the same name in a different translation unit, same sweep.
- `resolve_area_by_alias()` (`src/browser/browser_builders.cpp:159`), a third.
  NOT read in detail; named so a scoping pass does not stop at the others.

`cmd_select.cpp` resolves `SELECT <name>` by scanning work areas for a label
or DBF base-name match and calls `eng->selectArea((size_t)idx)` at `:200`. The
word `workspace` appears in that file exactly once, in a category tag.

**So today the answer to "which STUDENTS?" is "whichever one is in the lowest
slot".** Under R128 -- where two directories opened are two populated
workspaces -- two tables of the same name in two workspaces is no longer an
exotic arrangement, it is the ordinary one.

**This is the asymmetry.** The row cursor nests under the area cursor. The area
cursor does NOT nest under the workspace cursor. One of the three is a cursor
in name only.

## 4. THE DIVERGENCE IS LIVE NOW -- THE R5 SHAPE

**MEASURED.** Two authorities answer "which workspace am I in":

    xbase::workspace::current_handle()                    -- the declared one
    engine.area(engine.currentArea()).wsHandle()          -- where you stand

`wsHandle()` is `include/xbase.hpp:300`; it is stamped by `DbArea::open()` via
`src/xbase/dbf_file.cpp:231`, which reads `workspace::current_handle()` at open
time.

**They diverge at three call sites, and none of them says so:**

1. `WORKSPACE SWITCH` (`src/cli/cmd_workspace.cpp:5151`) calls
   `set_current_handle(h)` and prints handle, name, depth and member count.
   It never calls `selectArea()`. **The instant after you switch into MCC, the
   area cursor is still parked in the workspace you left.**
2. `WORKSPACE OPEN` calls `set_current_handle()` at `:4593` (re-entry) and
   `:4625` (fresh). Neither is accompanied by a `selectArea()`.
3. `close_workspace_tree()` (`:1524`) closes members and never touches
   `selectArea()`. **Close the workspace you are standing in and the area
   cursor points at a closed slot** -- which is the R6 shape as well as R5: an
   absent area is still representable as the place you are.

R5 says one tree one ladder, and names the defect precisely: *two answers to
one question IS the defect*. Both readings above are computable, they disagree
after any of those three commands, and **nothing tells the caller which one it
got.** This ruling does not create that; it removes the last reason it was
rarely reached.

## 5. R112 ALREADY RULED THE AMBIGUITY HALF, AND R128 ARMED ITS TRIPWIRE

**MEASURED in source, then RUN. This section is the only runtime-proven
material in this document.**

The first cut of this ruling did not cite R112 at all, and was written as
though cross-workspace name collision were unconsidered. It was ruled on
2026-08-22 and an instrument was built for it.

**The rule** (`src/cli/workarea_util.hpp:41-52`):

    R112 sec 6a ruled that first-wins-plus-warning is admissible only as an
    INSTRUMENTED migration phase whose counter has to reach a measured zero
    -- so this records, and does not merely print.

**The instrument** is `record_ambiguity()` (`src/cli/workarea_util.cpp:102`),
which latches one entry per (name, site) pair and records **`ws_handles`
alongside `engine_slots`** (`:120`). `WORKSPACE REGISTRY` reads it
(`cmd_workspace.cpp:4740-4757`) and prints it even at zero, deliberately, so
that "no collision occurred" and "nothing is instrumented" cannot look alike.

**THE RESOLVER ALREADY HOLDS THE WORKSPACE DATA AND DOES NOT FILTER ON IT.**
`record_ambiguity()` can name the workspace of every candidate;
`find_open_area_by_name_ci()` records that and takes the lowest slot anyway.

### 5.1 THE RUN

**RUNTIME-PROVEN, 2026-08-27, interactive CLI session via `.\datarun.ps1`.**

WHAT IT RAN AGAINST: the binary reporting `dottalk++ v0.6 (2026-08-24,
c39d966c dirty) (Aug 26 2026 14:47:54)`. **The version string does NOT
identify this build and is not the evidence** -- it names 2026-08-24, before
R128 landed. The evidence that this is an R128 binary is BEHAVIOURAL and is
in the transcript: the second `WORKSPACE OPEN` placed its 13 tables at engine
slots 13..25 and left the first workspace's 13 standing at 0..12. Under the
replacing OPEN the second would have closed the first.

Fixtures: `dottalkpp\data\dbf\x64` and `...\dbf\x32`, which share eight
basenames. Read-only on the tables.

    WORKSPACE REGISTRY                       -> ambiguity 0, DEFAULT, 0 members
    WORKSPACE OPEN ...\dbf\x64 AS WSX64     -> handle 2, WS_ID 208, slots 0..12
    WORKSPACE OPEN ...\dbf\x32 AS WSX32     -> handle 3, WS_ID 209, slots 13..25
    WORKSPACE REGISTRY                       -> ambiguity 2
    REL LIST                                 -> "Relations for parent: BUILDING" / "(none)"
    SELECT students                          -> "Selected area 8"
    WORKSPACE REGISTRY                       -> ambiguity 6

### 5.2 THE TRIPWIRE FIRED BEFORE ANY NAME WAS TYPED

The ledger went non-zero on the **second OPEN**, with no user command that
names a table:

    NAME: 'BUILDING' is open in 2 areas (ws 2 area 0, ws 3 area 13);
          resolved to area 0 [REL refresh parent].

Current handle was **3**. It resolved to workspace **2**.

TRACED IN SOURCE: `refresh_relations_if_enabled_safe()` runs on workspace
operations (`cmd_workspace.cpp:2587`, `:5266`, `:5422`, `:5480`) ->
`refresh_for_current_parent()` (`set_relations.cpp:717`) ->
`current_parent_name()` (`:709`) -> with no override set,
`infer_parent_from_workarea()` -> `refresh_from_parent_name()` ->
`find_open_area_by_name_ci(parent_name, "REL refresh parent")` (`:464`).

**THE SHAPE, STATED ONCE: THE RELATION STORE IS PARTITIONED BY WORKSPACE AND
THE RELATION PARENT IS NOT.** **This is now AIF-137**, claimed
2026-08-27T11:03:14Z, and it has its own finding document --
`AIF137_FINDING_RELATION_PARENT_IS_WORKSPACE_BLIND_V1.md`. It is recorded
here because this ruling's measurement found it, and it is NOT this ruling's
subject: R129 is the cursor, AIF-137 is the resolver. AIF-078 I1.2 partitioned the store --
`relations_store_for(current_handle())` at `:109` -- but
`current_parent_override()` is ONE global string, and both
`current_parent_name()` (`:710`) and `refresh_from_parent_name()` (`:464`)
resolve through the unscoped resolver. **A scoped store consulting an
unscoped lookup.**

This is what the RS regression spec recorded on 2026-08-23 as "the next
workspace-blind piece of relation state ... should not be found by surprise."
It was not a surprise. It was measured.

**IT NEEDS NO RELATION TO EXIST.** `REL LIST` answered
`Relations for parent: BUILDING` / `(none)` -- an EMPTY store whose inferred
parent is an area in ANOTHER workspace. The crossing rode in on
`WORKSPACE OPEN` alone.

**WHAT WAS AND WAS NOT DAMAGED, stated rather than implied.** With the store
empty, `refresh_from_parent_name()` called `parent->readCurrent()` on
WSX64's BUILDING and returned at the store lookup. That is a READ across the
boundary, not a cursor move. It is **one `SET RELATION` away** from
`goto_first_match()` (`:477`) driving WSX32's child from WSX64's parent
values. Not claimed as harm; named as the next thing that would be.

### 5.3 SEC 4'S DIVERGENCE IS NOW RUNTIME-PROVEN, AND SEC 6.2'S CASE WITH IT

    . select students
    Selected area 8.
    Current area: 8
      File: D:\code\ccode\dottalkpp\data\dbf\x64\STUDENTS.dbf  Recs: 200

**Current handle was 3 (WSX32). Area 8 belongs to workspace 2 (WSX64).**
WSX32's own STUDENTS was at area 21 and was not selected. The area cursor
crossed the boundary, and the session said nothing about it.

So after that command:

    current_handle()                            == 3   (WSX32)
    area(currentArea()).wsHandle()               == 2   (WSX64)

Sec 4 predicted this from source. It is now observed. **"Whichever one is in
the lowest slot" is not a reasoned consequence; it is a transcript.**

### 5.4 THE INSTRUMENT DOES NOT SEE THE CROSSING IT JUST DEMONSTRATED

**NEW FINDING, and it is an AIF-118 shape.** Read the site tag on the
STUDENTS entry:

    name STUDENTS  site REL refresh parent  chose area 8  hits 2
                   candidates ws2:a8 ws3:a21

**`REL refresh parent`, not a SELECT site.** `cmd_select.cpp` runs its own
scan (`:200`) and does NOT call `find_open_area_by_name_ci()`, so it records
nothing. The STUDENTS row exists only because the relation refresh that
followed the select happened to resolve the same name.

**Consequence: had SELECT crossed a boundary on a name the refresh did not
touch, the ledger would have read zero while a crossing occurred.** R112 sec
6a made the counter the gate -- "a measured zero" retires the migration
phase. A counter blind to one of its own crossing paths cannot retire
anything, and a zero from it would mean "not instrumented" while looking like
"clean". That is the exact failure AIF-118 names and the exact failure the
print-even-at-zero rule was written to prevent, reappearing one level in.

### 5.5 THE COUNTS

`ambiguity_count()` increments per resolution; the ledger latches per
(name, site). Both readings are consistent:

    after two OPENs   : 2 resolutions   BUILDING hits 2
    after one SELECT  : 6 resolutions   BUILDING hits 4, STUDENTS hits 2

**One `SELECT` caused four cross-workspace resolutions** -- two more BUILDING
and two STUDENTS -- none of them requested, none of them announced except by
the R112 line.

### 5.6 RESIDUE

`WORKSPACE CLOSE ALL` closed 26 areas and printed `REL: cleared all`.
`WORKSPACE DESTROY` retired WS_ID **208** and **209**: live rows superseded,
names free, handles 2 and 3 not reused, history kept (D10.3). Two superseded
rows added to `WORKSPACES.dbf` by this run, which is the D10.1 cost precept
P3 proposes to end.

## 6. THE TWO QUESTIONS THIS RULING MUST ANSWER

Separable, and each is a place where drift will settle the answer if a person
does not.

### 6.1 Does WORKSPACE SWITCH move the area cursor? -- RULED: YES

**RULED 2026-08-27.** `WORKSPACE SWITCH mcc` moves the area cursor to that
workspace's lowest-numbered member, and prints the slot it landed on.

**The refusal-on-empty arm this section originally proposed is STRUCK** -- see
below and 6.1a. An empty workspace is a legal position.

The alternative -- switch the handle, leave the area cursor -- is what happens
today, and it is the state where the two authorities in sec 4 disagree. A
cursor that can point outside the thing it is scoped to is not scoped.

**THE OWNER'S REASON FOR THE EMPTY WORKSPACE IS THE PRODUCT REASON, AND IT IS
STRONGER THAN THE FORMAL ONE.** The external reviewer argued from the
invariant -- I1 forbids a NULL workspace, not an EMPTY one. The owner argued
from use: *"there will be times we want to open and add to it. You have to
have a place to start."* Both are recorded because they are different
arguments and the second is the one a reader will need: an empty workspace is
not a tolerated edge case, it is **the intended starting state for building
one up.**

**RISK ACCEPTED EXPLICITLY, AND RECORDED AS ACCEPTED RATHER THAN ABSENT.**
Owner, same ruling: *"If it turns [out] wrong we will find out quickly."* That
is a judgement that the cost of being wrong here is cheap and visible, not a
claim that it cannot be wrong. 6.1a names precisely what would go wrong.

**This is where the precepts stopped.** P7 said *"SWITCH is the named current
pointer (SELECT-like)"* -- ambiguous exactly here -- and never named
`Engine::_current`.

**GROK ANSWERED IT (ANSWERS_TO_CLAUDE_2026-08-27.md, Q2), MARKED OWNER-FINAL:**
SWITCH should move `_current` to that workspace's lowest member so
`current_handle()` and `area().wsHandle()` do not disagree. **And the cost
this ruling named is refuted:** *"Empty workspace after NEW then SWITCH is
legal: no current table, next OPEN joins it. I1 forbids a null workspace, not
an empty one."*

That distinction is correct and this ruling's proposed REFUSAL was
over-engineering. **The refusal arm is withdrawn.**

**BUT AN EMPTY WORKSPACE NEEDS A REPRESENTATION FOR "NO CURRENT TABLE", AND
`Engine::_current` HAS NONE.** MEASURED: it is a plain `int` defaulting to 0
(`xbase.hpp:623`) and `selectArea()` accepts only `0 <= idx < MAX_AREA`
(`:615`). There is no unset value. So after `SWITCH` into an empty workspace,
`_current` keeps pointing at whatever it pointed at -- **a foreign, OPEN
area** -- and `infer_parent_from_workarea()` reads it
(`set_relations.cpp:159`, via `workareas::current_slot()`) and hands its name
straight back into the AIF-137 path.

**So SWITCH-into-empty is precisely the state that keeps AIF-137 alive, and it
is the one Grok's answer makes legal.** This is not an objection to the
answer; it is the sub-question the answer surfaces:

**6.1a -- what does the area cursor point at inside an empty workspace? -- RULED: THE POSITION IS LEGAL; ITS REPRESENTATION IS AIF-138**

**THE QUESTION IS MIS-ADDRESSED, AND THAT IS THE FINDING. IT IS NOT A
WORKSPACE QUESTION.** `Engine::_current` cannot say "nothing selected" at all,
has never been able to, and multi-workspace did not cause that -- it made it
reachable.

**SLOT 0 MEANS THREE DIFFERENT THINGS. MEASURED:**

    1. area 0 -- a real, addressable work area. In the 2026-08-27 transcript
       it is where WSX64's BUILDING landed and what the ambiguity ledger
       resolved to ("chose area 0").
    2. the startup position -- `shell.cpp:528` calls `eng.selectArea(0)`
       explicitly, so a fresh session is PARKED on slot 0 by decision.
    3. NO ENGINE AT ALL -- `workareas::current_slot()` (`workareas.hpp:120`)
       reads `if (!eng) return 0;`.

**That third one is the AIF-118 shape in the accessor
`infer_parent_from_workarea()` actually calls: absent and fine return the same
answer.** And the first two are R6: "nothing selected" is ABSENT, `_current`
holds only PRESENT values, and absence is spelled with a present one.

**SO THE CLOSED-SLOT PROPOSAL IS WITHDRAWN.** Parking `_current` at "a closed
slot the workspace will fill" means parking it at SOME slot, and which slot
depends on what other workspaces happen to hold -- the cursor becomes a
function of unrelated state. If the answer is slot 0 it collides with all
three meanings above; if it is a higher free slot it is arbitrary and
unstable.

**THE SENTINEL IS RIGHT AFTER ALL, AND FOR THE REASON THE FIRST DRAFT GAVE
AND THE SECOND TALKED ITSELF OUT OF: R6.** Absent needs its own
representation. The cost -- `selectArea()` rejecting negatives, every
`currentArea()` reader becoming two-case -- is the price of the defect, not an
argument against fixing it, and it is owed whether or not workspaces exist.

**THE INVARIANT, RESTATED OVER THE PAIR AND NOT OVER `wsHandle()` ALONE:**

    Let A = the current area.
      A is open   ->  A.wsHandle() == current_handle(). Never another
                      workspace's handle, AND NEVER 0 -- 0 on an OPEN area is
                      a MISSED STAMP, which is a registration defect
                      `reconcile_unregistered_areas()` (`:1578`) exists to
                      name and which `compute_save_scope` already counts as
                      `skipped_unregistered` (`:1963`).
      nothing selected -> the cursor says so IN ITS OWN VALUE, not by pointing
                      at a slot that happens to be closed.

**Stating it over `wsHandle()` alone -- as the previous revision of this
section did -- silently accepts the missed-stamp case as a legal empty
position, because an open unregistered area and a closed area both read 0.
That is the AIF-118 shape reappearing inside the invariant written to prevent
it.** Recorded because it was written that way and caught by the owner rather
than by the author.

**WHY THE `(5, 0)` ARGUMENT STILL HOLDS, narrowed.** Sec 4's defect is the
pair `(3, 2)` -- standing in one workspace while the cursor sits in ANOTHER.
"Standing in workspace 5 with nothing selected" is not that shape, and a rule
demanding strict agreement between the two cursors would forbid a legal
position. That reasoning survives. What does not survive is spelling "nothing
selected" as slot 0.

**PROPOSED SEPARATION: THIS IS NOT R129's DEFECT AND SHOULD NOT SHIP INSIDE
IT.** "The area cursor cannot express 'nothing selected', and slot 0 carries
three meanings including a no-engine fallback" is an engine defect that
predates multi-workspace, sits in `include/xbase.hpp` and
`src/cli/workareas.hpp`, and is reachable from any session. It wants its own
AIF number and its own finding, exactly as AIF-137 was separated from this
ruling. **It is now AIF-138**, claimed 2026-08-27T11:33:46Z, with its own finding
document `AIF138_FINDING_AREA_CURSOR_CANNOT_SAY_NOTHING_V1.md`. R129 keeps
the question and defers the defect.

R129 then keeps only what is its own: the workspace cursor is a peer, the
three cursors do not nest, and the invariant above governs the pair.

**RULED 2026-08-27 -- AND THE RULING CHANGES AIF-138's STATUS, NOT ITS
CONTENT.** The owner ruled the empty workspace legal: *"there will be times we
want to open and add to it. You have to have a place to start."*

**So AIF-138 moves from LATENT to ON THE PATH.** Before this ruling, "the area
cursor cannot say nothing selected" was a defect nobody could reach on
purpose. After it, the empty workspace is the **intended starting state**, and
the engine has no value for the position a user is now invited to occupy.
AIF-138 is not a curiosity found while drafting; it is the work this ruling
depends on.

**WHAT IS RULED AND WHAT IS NOT.** Ruled: the position exists and is legal.
NOT ruled, and it belongs to AIF-138: how the cursor SAYS it -- a negative
sentinel, an `optional`, or a `hasCurrent()` predicate -- and what happens to
the callers. This ruling deliberately does not choose, because choosing a
representation before counting the readers is what produced the two withdrawn
answers above.

**THE RISK THE OWNER ACCEPTED IS THIS ONE.** *"If it turns [out] wrong we will
find out quickly"* -- and 6.2(a) names how it would show: in an empty
workspace arm 1 never applies, so every name refuses or misses. If that reads
badly in use, this is the section to reopen.

The external reviewer was asked and the question did not reach him across four
attempts; it is answered here rather than left open.

### 6.2 What does SELECT do across a workspace boundary? -- RULED (three-way)

**RULED 2026-08-27, owner: *"6.2 is valid"*, on the three-way rule below.**

**THE FIRST CUT OF THIS RULING PROPOSED A BLANKET "REFUSE AND NAME THE
HOLDER". THAT WAS WRONG, AND P6 ALREADY ANSWERED IT.**

Grok's Q3 answer (owner-final): *"Finding 3 is both sides having STUDENTS. P6
says use the current workspace's (area 21), not refuse and not follow. Refuse
only when the name is not here but exists elsewhere. SELECT is not a second
SWITCH."*

That is correct and the error in the first cut is worth naming, because it is
a category mistake and not a detail. **This ruling was reasoning about the
CROSSING when the question is about RESOLUTION.** When a name is present in
the current workspace, there is nothing to decide -- the local one wins, by
P6, and refusing it would refuse a name that is right there. The crossing only
becomes a question when the current workspace does NOT hold the name.

So the rule is three-way, and only the third arm is new:

    name present in current workspace   -> resolve to it. P6. Not a crossing.
    name absent everywhere              -> the existing not-found path.
    name absent HERE, present ELSEWHERE -> REFUSE, and say which workspace
                                           holds it and how to qualify it.

The measured transcript is the FIRST case, not the third: WSX32 held STUDENTS
at area 21 and `SELECT students` took WSX64's area 8 anyway. **That is P6
being violated, not a boundary policy being absent.**

**TWO CONSEQUENCES OF THIS RULING THAT ARE NOT OBVIOUS FROM THE THREE ARMS,
STATED SO THEY ARE NOT DISCOVERED:**

**(a) IN AN EMPTY WORKSPACE, ARM 1 CAN NEVER APPLY.** Nothing is present, so
every name falls to arm 2 or arm 3 -- meaning an empty workspace is a place
where nothing resolves and most names refuse with "it is over there." That is
correct under 6.1's ruling and it is a real user-visible consequence of making
the empty workspace the intended starting state. It is not a defect; it is
what "you have to have a place to start" costs.

**(b) THE REFUSAL ARM DOES NOT MEAN "PRINT AN ERROR" ON THE ENGINE'S OWN
LOOKUPS.** P6 is a resolver rule (external Q1 answer), so arm 3 governs
internal resolutions too -- but an internal refusal has nobody to tell. For
`refresh_from_parent_name()` the correct behaviour under arm 3 is simply
**find no parent and return**, which is what P6 implies and what closes
AIF-137. Said explicitly because "refuse" reads as "diagnose", and a
diagnostic on the refresh path would be wrong.

## 7. THE THIRD QUESTION IS ANSWERED ELSEWHERE -- AND IS STRUCK FROM HERE

The first cut of this document carried a section 5.3, *"does an unqualified
name search only the current workspace? PROPOSED: YES"*.

**It is struck.** `WORKSPACE_IDENTITY_AND_CATALOG_PRECEPTS_V1.md` P6, co-
authored by the owner and owner-accepted on 2026-08-27, rules it:

    Unqualified STUDENTS means the current workspace's member. Other
    workspaces are invisible until SWITCH or a qualified name.

with `SALES:STUDENTS.FNAME` as the qualified form, `.` reserved for field
access, and `#n.FNAME` retained as the engine-slot escape hatch rather than
the happy path.

**Struck rather than kept-and-agreed on purpose.** Both documents said the same
thing, which is not a contradiction -- it is a duplication, and a duplication
is the R5 shape one layer up from the code. Two authorities that agree today
diverge silently the first time one is amended. **P6 is the authority; this
ruling cites it and does not restate it.**

**P6 is also Q8, and Q8's preconditions are now satisfied.**
`include/reference/data_address.hpp` has said since 2026-07-30 that

    Q8 (does an unqualified name walk up ancestors? proposed: NO) must be
    ruled before any depth > 1 is resolved.

The four blockers that comment names -- runtime workspace registry, containment
invariant, cycle guard, depth cap -- are all now present as `Entry` and
handles, the parent pointer, `would_cycle()` and `kMaxWorkspaceDepth`, landed
at AIF-078 stage 3. MEASURED. **P6 answers Q8 in the negative, which is what
that comment proposed, so a question that has blocked depth > 1 for four weeks
is closed.**

**What P6 leaves standing for this ruling:** P6 rules RESOLUTION. Sections 6.1
and 6.2 rule NAVIGATION. **P6 is load-bearing on a cursor model it does not
state** -- if a bare name resolves in the current workspace, but the area
cursor may sit in a foreign workspace's area, then "the current workspace" has
two computable answers at the moment you ask. Sec 4 is that defect. P6 cannot
be implemented correctly until 6.1 and 6.2 are ruled.

**And P6 has a cheap implementation path it does not name:** the filter belongs
in `find_open_area_by_name_ci()`, which per sec 5 already has each candidate's
`wsHandle()` in front of it.

## 8. WHAT THIS MAKES WRONG THAT IS NOT WRONG TODAY

**Line-cited claims are MEASURED; the consequences are reasoned, not run.**

- **`derive_distinct_alias()`** (`cmd_use.cpp:491`, called at `:917`) renames
  STUDENTS to STUDENTS2 when the name is taken, and asks
  `find_open_area_by_alias()` -- the workspace-blind one -- whether it is
  taken. Under a scoped cursor the name is NOT taken (it is taken in another
  workspace), so this uniquifies where it should not.

  **CONFIRMED 2026-08-31. RUNTIME-PROVEN, FIRST ATTEMPT, NO TUNING -- this
  bullet is no longer reasoned.** Probe:
  `dottalkpp/data/scripts/derive_distinct_alias_workspace_probe.dts`, six
  markers, FULL COUNT, predictions written into the file before the run. Two
  directories holding one table name with different labels; `WORKSPACE NEW`
  twice; `USE DDAT` in each. Guards G0a/G0b/G1a/G1b all `.T.`, so the
  arrangement the probe reasons about is the arrangement that existed. The
  engine named the defect in its own words:

      USE: alias 'DDAT' is held by area 0; this instance is named 'DDAT2'.
      Use ALIAS to choose your own.

  `DDA_P1_second_use_was_uniquified` reads `.T.` -- the second `USE`, in a
  DIFFERENT workspace, was renamed because the name was taken in the first.

  **AND THE SEVERITY IS LOWER THAN THIS BULLET IMPLIES, WHICH IS WORTH SAYING
  RATHER THAN LEAVING TO BE FOUND.** `derive_distinct_alias()`'s own comment
  claims *"Deterministic and announced; never silent"*, and that claim is now
  runtime-proven TRUE: the rename is printed, the holding area is named, and
  the remedy (`ALIAS`) is offered in the same line. This is a WRONG-BUT-LOUD
  defect, which is a different class from the silent crossings AIF-137
  measured, and it should be triaged as one.

  **THE COMPOUNDING IS WORTH MORE THAN THE CONFIRMATION.** The rename
  MANUFACTURES the exact precondition sec 6.2's refusal arm exists to catch.
  With B's copy renamed to `DDAT2`, the plain name `DDAT` is now ABSENT in
  workspace B and PRESENT in workspace A -- and `SELECT DDAT` issued from
  inside B selected **area 0, workspace A's copy**, with no refusal and no
  ledger line. `DDA_P2_plain_name_inside_B_is_B` reads `.F.`, which is the
  positive read of that crossing.

  **STATED PRECISELY, BECAUSE IT IS NOT A DEFECT AGAINST SHIPPED BEHAVIOUR:**
  sec 6.2 is RULED and NOT IMPLEMENTED -- the 2026-08-27 closeout says "no
  code is authorized and no fix is designed for either finding" -- so this
  measures the gap between the ruling and the engine, not a regression. It is
  also invisible to the R112 counter by construction, because `cmd_select.cpp`
  does not call the recording resolver (AIF-139). One run produced a LOUD
  crossing on the `USE` path and a SILENT one on the `SELECT` path, four lines
  apart.

  **SO THE TWO ITEMS ARE NOT INDEPENDENT AND THE ORDER MATTERS.** Scoping the
  alias resolver removes the precondition; implementing 6.2 catches it if the
  alias resolver is not scoped. Either alone helps and neither is redundant.

  **ALSO OBSERVED, unrelated to this bullet and recorded where it was seen:**
  `WORKSPACE NEW` prints `parent 0  depth 0` on every declaration. The engine
  COMPUTES and DISPLAYS both and the posture persists neither.
- **`current_parent_override()`** in `set_relations.cpp` is still ONE global
  rather than per workspace. **PROMOTED out of this list by sec 5.2: it is no
  longer a thing this ruling would make wrong, it is a defect measured active,
  and it is AIF-137 with its own finding document. Not carried further here.**
- **`USE ... IN FREE`** already prints the workspace name (`cmd_use.cpp:779`)
  and `find_free_area_for_workspace` is already workspace-aware. That half is
  done and does not need touching -- which is also the strongest argument
  against P8's slot banks: a slot bank would be a SECOND allocator answering a
  question one allocator already answers.

## 9. NOT RULED

- Whether `USE <table> IN <workspace>` is PLACEMENT or QUALIFICATION, given
  `cmd_workspace.cpp:138` states the model as "SWITCH-then-open, never
  open-then-assign". If `:` qualifies and `IN` places they are different
  operations and both may live; if they are the same operation they are two
  spellings of one question. P6 settles the separator and not this.
- `WorkspaceIdentity::profile_path` (`include/reference/data_address.hpp`) is
  a declared field with **NO writer and NO reader anywhere in the tree**.
  MEASURED. It is the natural home for per-workspace environment -- the
  question that started this conversation -- and is currently a promise
  nothing keeps.
- The CLI `LOAD` half of R128: `schema_close_all()` at
  `cmd_workspace.cpp:2405` still makes CLI LOAD replacement-style while the
  GUI's is additive. Open since 2026-08-26.
- Whether the ambiguity ledger's counter, once read under R128, is a migration
  counter again rather than a tripwire -- and what number retires it. R112 sec
  6a says "a measured zero"; under P6 the target may instead be "every hit is
  a refusal", which is a different instrument.

## 10. CORRECTIONS TO THE FIRST CUT OF THIS DOCUMENT

Recorded rather than silently amended, because a draft that changes its claims
without saying so is the drift this house keeps finding.

1. **R112 and the ambiguity ledger were absent.** The first cut wrote sec 3 as
   though cross-workspace name collision were unconsidered. It was ruled
   2026-08-22 and instrumented. Sec 5 is new and is the most load-bearing
   section here. Found by reading `WORKSPACE_IDENTITY_AND_CATALOG_PRECEPTS_V1`
   P6, which cites the ledger correctly.
2. **"Three resolvers" was an undercount.** `find_open_area_by_name_ci()` with
   36 call sites is a fourth path and the instrumented one. Sec 3 corrected.
3. **5.3 is struck** in favour of P6 (sec 7), on R5 grounds.
4. **"The load-bearing question is what SELECT does across a boundary" was
   too narrow.** Runtime measurement (sec 5.2) shows the crossing happens
   with no user command at all, inside the relation refresh, on OPEN. Sec 6.2
   is necessary and not sufficient; sec 5 now carries the deeper defect.
5. **Sec 6.2's proposal was withdrawn entirely.** The first cut proposed that
   `SELECT` REFUSE across a boundary. It should resolve locally per P6 and
   refuse only when the name is absent here and present elsewhere. The error
   was reasoning about the crossing instead of the resolution. Corrected from
   Grok's Q3 answer, 2026-08-27.
6. **Sec 6.1's refusal arm was withdrawn.** "Refuse a SWITCH into an empty
   workspace" was over-engineering: I1 forbids a NULL workspace, not an EMPTY
   one. Corrected from Grok's Q2 answer. It surfaced 6.1a, which is open.
7. **6.1a was answered twice, wrongly, before it was answered.** The first
   pass proposed a closed slot and REJECTED the sentinel; it also retracted an
   R6 objection to overloading `wsHandle() == 0`, on the ground that "empty
   workspace" entails "current area closed" so the two never diverge. Both
   moves were wrong and both were caught by the owner, in two words each.
   **The method error is worth more than the conclusion: the author checked
   whether CLOSE produced a safe READING and never checked whether the cursor
   could SAY "nothing" at all.** That is verifying the consequence instead of
   the representation -- and R6 is a rule about representation. `slot 0` turns
   out to mean area 0, the startup position, AND "no engine"
   (`workareas.hpp:120`), which is the AIF-118 shape sitting in the accessor
   the AIF-137 path calls.
8. **6.1, 6.1a and 6.2 were RULED AFTER the measurement and after the
   external answers, not before either.** Worth recording as an ordering: the
   first cut of 6.2 proposed a blanket refusal and would have been ruled
   wrong, because the transcript showed the case was a LOCAL name being
   ignored rather than a boundary policy being absent. **A ruling made before
   its measurement would have shipped the wrong rule with the same
   confidence.**
9. **A criticism of the packet's directory layout was withdrawn.** The reviewer
   checked `git ls-files` inside `D:\code\ccode`, found no
   `change_packages/`, and concluded the layout was off-contract. The layout is
   an established convention six packages deep since 2026-07-24; the packages
   live outside the dev tree, so git was never going to see them. **R75: a gate
   sees the shape it was built to see, and its silence about a class of thing
   is not evidence the class is clean.** The rule was known and used as though
   absence were measurement.

## 11. NO CODE WAS WRITTEN

`src/cli/**` and `src/xbase/**` are engine and want an explicit go. Nothing in
this document has been implemented, and nothing in it has been run.

**GOOD NEIGHBOR**

- **What changed:** nothing in the tree. This is a draft ruling document only.
- **Whose area:** AIF-078 (multi-workspace). Would touch the engine's cursor
  model, `src/cli/workarea_util.cpp`, `cmd_use.cpp`, `cmd_select.cpp`,
  `cmd_workspace.cpp` and `src/browser/browser_builders.cpp` IF and WHEN sec 6
  is ruled and built.
- **What authorization:** the owner ruled part 1 (sec 1) on 2026-08-27, asked
  for a draft, and authorized this reconciliation against
  AIPR-20260827-GROK-001. Sections 6.1 and 6.2 await his call.
- **How to verify or undo:** delete this file. Nothing else exists.
