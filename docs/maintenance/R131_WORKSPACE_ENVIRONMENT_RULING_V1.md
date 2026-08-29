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

**THAT QUOTE IS THE PRE-R131 TEXT AND IS KEPT because it is what the engine
said when this ruling was written.** The implementation changed it the same
day; see sec 10.2 for the current wording and the corrected line numbers
(4773 -> 4799, 4779 -> 4804).

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

Two answers, and the ruling on the TREE does not decide it -- "no parent, no
child" is about nesting, and this is a different kind of inheritance:

  (a) INHERIT whatever is current at NEW time. Never unresolvable;
      `WORKSPACE OPEN dbf` always has something to resolve against.
  (b) START EMPTY. `WORKSPACE OPEN dbf` refuses until told where to look,
      which makes the sequence's third step mandatory rather than customary.

(b) is the stricter reading of the owner's sentence -- "we CAN set the
environment before an open" describes an expectation. (a) cannot produce a
state with no answer. They differ only for a caller who skips step 3.

**Author's recommendation: (a) INHERIT**, for the same reason AIF-148 puts
`OrderBackend::Natural` at the floor -- NO STATE WITHOUT AN ANSWER. Empty roots
is a question with no answer, which is the shape this lane keeps finding, and
inheriting makes the change strictly additive so no existing script alters
behaviour. Not ruled; recorded so the reasoning is not re-derived.

## 7b. RULED 2026-08-29 -- `WORKSPACE OPEN` LANDS IN THE CURRENT WORKSPACE

This was not one of the numbered questions. It surfaced as the thing BLOCKING
the whole sanctioned sequence, and it was found by running it rather than by
reading the source.

**MEASURED, live session, build `cdc00895`.** Three commands:

    workspace new mcc_x64     -> refused (name already live in the catalog)
    switch mcc_x64            -> current handle 2 (mcc_x64), depth 0, members 0
    do x64                    -> SETPATH DBF / INDEXES / LMDB = ...\x64
    workspace open dbf        -> workspace 4, NAME `x64`, WS_ID 207, areas 16..28

Three facts in that last line:

1. **OPEN never joined the current workspace.** `mcc_x64` still reported ZERO
   members while thirteen areas opened elsewhere.
2. **OPEN named its workspace from the RESOLVED DIRECTORY LEAF.** The person
   typed `dbf`. The workspace is called `x64`, because `SET PATH DBF` had just
   pointed the slot at `...\DBF\x64`. The same typed command produces a
   different workspace name in a different environment.
3. **OPEN minted a durable catalog identity for that name** (WS_ID 207), from
   an interactive session with no bracket around it.

Fact 2 is the ruling's own thesis inverted. R131 sec 1 says a workspace owns
its environment; leaf naming made **the environment name the workspace**. The
dependency ran the wrong way, and that is precisely why steps 1-3 of the
sanctioned sequence had no effect on step 4 -- OPEN walked out of the workspace
the person had just made and stood in.

### The ruling

**A bare `WORKSPACE OPEN <dir>` opens into the CURRENT workspace and names
nothing. `WORKSPACE OPEN <dir> AS <name>` is the only naming form, and remains
the minting form.** Directory-leaf naming is withdrawn entirely.

### What this does NOT repeal

R128's capability is untouched. "We can also open two dir into two workspaces
too" (owner, 2026-08-26) is still available, still additive, still re-entrant,
and its cross-root collision refusal still stands -- all of it now reached
through `AS`. **Only the implicit name goes**, the one nobody typed.

### What it costs, stated rather than discovered later

A bare OPEN no longer mints a durable row, so the "this workspace came from
here" record is no longer written for it. Thirteen tracked specs use the bare
form; they now land in DEFAULT, **which has no catalog identity** and reports
`WS_ID (none yet)`. Four `mcc_build_*` specs that exist to populate a named
home will want `AS` added -- a fixture edit, not a semantic loss. Whether
DEFAULT should mint is deliberately left to Q3 rather than bundled in here: the
naming defect and the minting policy are two problems, and only one of them was
running backwards.

### Rejected, and why it is worth recording

**"Join the current workspace only if it is empty, mint otherwise."** That is
the withdrawn y/n prompt wearing different clothes. The owner's own reason for
withdrawing the prompt in Q1 applies unchanged: one grammar, no mode-dependent
behaviour.

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

## 9. CODE STATUS

**Sections 1-7a: NO CODE WRITTEN.** Q2 and Q3 are unruled, and nothing that
depends on them has been built. The measurements cited in those sections were
taken on build `c7c94e18` during the session that produced the ruling; every
source claim there is a read at that HEAD.

**Section 7b: IMPLEMENTED 2026-08-29 on the owner's explicit go.** One site in
`src/cli/cmd_workspace.cpp` -- the directory branch of the OPEN dispatch --
now enters a workspace only when `AS <name>` was typed, and otherwise prints
which workspace it is opening into. The leaf-naming wrapper
`workspace_name_for_directory()` is deleted from that file;
`xbase::workspace::name_for_directory()` is NOT removed, because R122 keeps it
as the shared rule the GUI reads. `workspace_additive_open.dts` gained an
explicit `AS` on its three OPEN lines, which changes its spelling and not its
semantics. `workspace_open_joins_current.dts` (spec `OPENJOIN`, explicit-run)
is the discriminator, and it is registered but NOT YET RUN -- no green is
claimed for it here, and it has not been run against the pre-change binary.

**The roots half of R131 is still unbuilt and deliberately so.** 7b makes OPEN
land in the right workspace; it does not make that workspace RECORD where it
opened from. That is Q3, and `WORKSPACES.dbf` still declares `DBF_ROOT` and
`IDX_ROOT` only -- there is **no LMDB column**, so the third slot has no
durable home to be written to at all. That is a schema decision awaiting a
ruling, not an omission to be patched around.

Ships **review-needed** -- the author does not self-approve.

## 10. RE-REVIEW 2026-08-29, against HEAD `56bf6c4c`

This ruling was written on build `c7c94e18` and its own section 9 promised
that every source claim was a read at that HEAD. Four commits landed the same
day, one of them in the exact region this document quotes. Every claim was
therefore re-read. **Four hold, two had drifted, and one of the two is drift
this ruling's own implementation introduced.**

### 10.1 CONFIRMED, still true at `56bf6c4c`

- **`profile_path`: ONE declaration, ZERO writers, TWO readers.** Declared
  `include/reference/data_address.hpp:32`; read by `unspecified()` and
  `operator==` at `src/reference/data_address.cpp:45,50`. Section 5 stands
  unchanged, including the part that matters -- it participates in EQUALITY, so
  every workspace compares equal on it today and writing it would silently flip
  comparisons across a call surface nobody has enumerated.
  **A GREP TRAP, recorded so the next reader does not lose an hour:**
  `src/cli/cmd_ersatz.cpp:1131-1132` declares a LOCAL VARIABLE also called
  `profile_path`. It is an unrelated filesystem path. A bare grep reports four
  hits and two of them are noise.
- **`g_suppress_prompts` (`src/cli/dirty_prompt.cpp:27`) is still set only on
  the QUIT path and by one local save/restore.** Measured: 76-79 are the
  save/restore pair; 130, 146 and 167 each gate on `is_quit_like`. Nothing in
  `DOTSCRIPT` touches it. The reason the y/n prompt was withdrawn is intact.
- **`g_dotscript_depth` is still there and still thread-local**
  (`cmd_dotscript.cpp:340`, counted at 491/538). The gate that COULD have made
  a prompt interactive-only still exists and is still declined.
- **`SET ORDER TAG <tag> IN <alias>`** is still documented at
  `cmd_setorder.cpp:19`, so `IN` remains the house word Q1 reuses.

### 10.2 DRIFTED -- the section 4 block quote no longer matches its source

Section 4 quotes `cmd_workspace.cpp:4779` as ending:

> WORKSPACES.dbf carries DBF_ROOT and is the place a durable answer belongs;
> **wiring that is not this change.**

**THAT SENTENCE NO LONGER EXISTS.** The R131 implementation commit (`4fc5171`)
rewrote it, and the comment now reads "wiring that is R131 Q3 and is still
unruled -- and note WORKSPACES.dbf declares DBF_ROOT and IDX_ROOT only, so the
LMDB slot has no durable column to be written to at all." The line numbers
moved too: 4773 -> 4799, 4779 -> 4804.

**THIS RULING BROKE ITS OWN CITATION, ON THE SAME DAY, IN A COMMIT THAT DID
NOT NOTICE.** That is the drift shape this house keeps cataloguing -- a second
declaration of what the source already says -- arriving in the document whose
whole subject is a second declaration of where an environment lives. Recorded
rather than silently repaired, because the mechanism is the lesson: nothing
compares a block quote against the lines it quotes, and `cited-paths` checks
that a PATH is tracked, not that a QUOTE still matches.

### 10.3 DRIFTED -- "the whole body is" was a compression, and now reads false

Section 6 quotes `WORKSPACE SWITCH` as having a two-line body. Measured now, the
branch is sixteen lines: token split, an empty-target refusal, a
`resolve_workspace_token` lookup with a no-such-workspace refusal, then
`set_current_handle(h)` and the report line.

**THE CLAIM SURVIVES AND THE SENTENCE DOES NOT.** What section 6 needs is that
SWITCH does NOT move `_current` to the target's lowest member, so R129 6.1 is
still unimplemented and the divergence window is still real. That is true: no
line in the branch touches the area cursor. But "the whole body is" invites a
reader to check a literal and find it wrong, which spends their trust on a
paraphrase. **Read section 6 as: SWITCH sets the handle and reports; it does
not touch the area cursor.** AIF-138 remains blocking, unchanged.

### 10.4 MATERIALLY INCOMPLETE -- section 5's durable-roots row

Section 5's table calls `DBF_ROOT`/`IDX_ROOT` "DURABLE catalog columns, already
present on every row", which understates the situation in the direction that
makes Q3 look easier than it is. Measured 2026-08-29:

- They are **already WRITTEN**, twice: `ensure_durable_workspace()` writes both
  at birth (`cmd_workspace.cpp:3216-3217`) and the SAVE path writes them again
  (`3548-3549`). Both write `dbf_root()` / `idx_root()` -- **the SESSION slot at
  that moment**, not anything the workspace owns.
- They are **already READ**, and not by anybody wanting an environment:
  `3743-3744` reads them back and `3974-3979` plus `4286` consume them in
  `WORKSPACE LOAD`, **to relocate tables**.

**SO Q3 IS NOT "SHOULD WE START WRITING THESE".** They are written and read
today with a settled meaning. The question is what happens to LOAD's relocation
when the same two fields start carrying a workspace's declared environment
instead of a snapshot of the session that wrote the row. That is the
`profile_path` trap in a second pair of fields, and this time the fields have
real readers rather than vacuous ones.

**AND THE THIRD SLOT HAS TWO DIFFERENT KINDS OF ABSENCE**, which section 5 does
not distinguish and Q3 must:

- **No catalog column at all.** The schema ends at `DBF_ROOT`/`IDX_ROOT`
  (`cmd_workspace.cpp:2939`). There is nowhere durable to put an LMDB root.
- **A posture line that is inert.** The v3 DTSHEMA payload DOES carry
  `LMDBROOT`, and the loader prints it as `(recorded, not applied)` -- observed
  in every v3 load in the 2026-08-29 suite run.

So there are TWO durable surfaces for an environment, the catalog row and the
posture, and the LMDB slot is ABSENT from one and INERT in the other. A ruling
that says "record the roots" without saying WHICH surface has not decided
anything.

### 10.5 A FORMATTING DEFECT IN 7a, repaired

The author's-recommendation paragraph was inserted INTO the middle of the
sentence that introduces the two options, leaving " Two answers, and the ruling
on the TREE does not decide it" dangling with a leading space and no subject.
Repaired in place; no argument changed. Noted only because it was introduced by
an edit to this file and would otherwise read as a thought that trailed off.

### 10.6 WHAT THE RE-REVIEW DID NOT CHECK

The measurements in sections 3 and 6 that came from RUNNING (the
`SET ORDER TO TAG SID` cross-bundle resolution failure, the DBAREA/GPS
owning-workspace line) were not re-run. They are transcript facts from
2026-08-29 and nothing since is known to have touched those paths, but "not
known to have touched" is not a measurement and is not claimed as one.

## 11. Q2 AND Q3 CLOSED -- 2026-08-29

Reviewed with the owner the same day. **Three answers were RULED, two were
FORCED by measurement rather than chosen, and one earlier finding in this very
document is WITHDRAWN.** Each is labelled, because a ruling and a constraint
are not the same kind of thing and a later reader must be able to tell which
they are arguing with.

### 11.1 RULED BY THE OWNER: LMDB IS DERIVED

> "lmdb is not used in v32, it is not used in vdisks, when we do need lmdb
> files we can regenerate them, wherever we set the lmdb path. there are times
> when we want to keep lmdb on disk and that is when we are using x64base with
> x64 dbf"

**BOTH PREMISES MEASURED AND CONFIRMED, not taken on assertion.**
`src/xindex/cnx_backend.cpp` and `src/xindex/inx_payload.cpp` mention LMDB
ZERO times -- it lives only in `cdx_backend`, `lmdb_backend` and
`index_manager` -- so the v32 index forms genuinely never reach it. And
`include/xbase/ramfs.hpp:24` states *"LMDB is out of scope here (it must mmap a
real OS file)"*, which is the same owner rule already recorded verbatim in the
WORKSPACE_RAM regression entry from 2026-08-11: *"lmdb only for disks"*. This
ruling is consistent with one made eighteen days earlier.

**THE PRECEDENT IS ALREADY IN THIS HOUSE, one layer up.** WORKSPACE WRITEBACK
ruled the same way about index FILES: *"derived, rebuildable at the
destination, WITH INDEXES for a byte-mirror, while the CHOICE travels in the
posture."* LMDB is the more derived of the two -- a CDX is the container, LMDB
is the built form of its tags -- so the rule extends rather than being invented.

### 11.2 FORCED, NOT CHOSEN: the live roots are `Entry` plus a SWITCH swap

Section 5 offered three homes as if all three were live options. **They are
not.** Measured 2026-08-29: `paths::get_slot` has **102 call sites across
thirty-odd files**, and they are not workspace code -- `src/bbs/bbs_store.cpp`,
`cmd_smtp.cpp`, `cmd_drawio.cpp`, `edu/edu_cobol.cpp`, `src/cli/expr/fn_string.cpp`.
Making resolution workspace-aware means handing a workspace to code that has
none and wants none. That is not a design option, it is a rewrite.

So there is ONE live shape: **`Entry` gains the roots as a STAMP, and
`WORKSPACE SWITCH` writes them into the global on the way in.** All 102
readers are untouched; they keep reading one global that now happens to be the
current workspace's.

**AND IT IS THE DOCTRINE `Entry` ALREADY CARRIES**, written for `ws_id`
(`workspace_membership.hpp:131-135`): *"derivation runs DOWNWARD ONLY, so this
field is a STAMP and not a lookup... A handle knows its WS_ID because it was
told; it cannot go and find out."* Roots on `Entry` are exactly that -- three
strings xbase can hold and cannot resolve, told to it by the CLI. Same rule,
second application, and the header does not have to reach up into `paths::`.

### 11.3 RULED OUT: `profile_path` is not a candidate

Not deferred -- excluded. It is a field on an ADDRESSING type
(`data_address.hpp:32`) and it participates in `operator==`
(`data_address.cpp:45,50`), so writing it changes equality across a call
surface nobody has enumerated. It would buy a home we do not need, because
`Entry` already carries per-workspace durable state and is the right layer.

**A GREP TRAP, recorded:** `cmd_ersatz.cpp:1131` declares an unrelated LOCAL
also named `profile_path`. A bare grep reports four hits; two are noise.

### 11.4 THE DURABLE HALF: two roots keep, one does not exist

- **`DBF_ROOT` / `IDX_ROOT` stay durable and stay where they are.** They are
  already written at birth (`cmd_workspace.cpp:3216-3217`) and by SAVE
  (`3548-3549`), and already read by LOAD (`3743-3744`, consumed `3974-3979`
  and `4286`). What changes is their MEANING -- from "the session slot when
  this row was written" to "this workspace's declared environment" -- not
  their existence.
- **NO LMDB COLUMN IN `WORKSPACES.dbf`.** Follows directly from 11.1: nothing
  is lost by not recording a location for an artifact you can rebuild, and it
  spares a schema change to a catalog with 269 live rows and a supersede chain.
  The absence stops being a gap and becomes a decision.
- **THE LMDB SLOT IS LIVE-ONLY.** Derived does NOT mean unowned. R131's own
  founding measurement (sec 3) is an LMDB RESOLUTION failure -- MCC's STUDENTS
  answering `openCdx: LMDB env missing: ...SYSTEMS\CASCADE_ERP\LMDB\...`
  because Cascade was opened last. Regenerability does not help there: you
  still have to resolve to the right place to find the env, or you rebuild it
  into a neighbour's tree. So LMDB rides on `Entry` and is swapped by SWITCH
  like the other two, and is simply never written to the catalog.

**ONE ITEM LEFT INSIDE THIS, and it is a wording fix rather than a mechanism.**
The v3 posture DOES carry `LMDBROOT` and the loader prints it as
`(recorded, not applied)` -- observed on every v3 load in the 2026-08-29 suite
run. Under 11.1 that label is wrong in a specific and inviting way: it reads as
*not applied YET*, a wiring gap someone will eventually try to close. It is
actually *not applicable as a source*, permanently, because the thing it names
is regenerable and may legitimately not exist. **Author's recommendation: keep
the line and relabel it.** A posture that records where its owner liked to
build envs is useful, and deleting a field from a format four specs read is a
larger change than a sentence.

### 11.5 Q2 ANSWERS ITSELF: INHERIT

Section 7a treated Q2 as independent. **It is not.** Under 11.2, "start empty"
means a SWITCH into a fresh workspace blanks the global, and 102 call sites --
including SMTP, BBS and drawio, which never opted into workspaces -- resolve
against nothing. Option (b) is not the stricter reading; it is a session-wide
outage triggered by a navigation verb.

**So Q2 is settled by Q3's live shape rather than on its own merits: INHERIT
whatever is current at NEW time.** The recommendation recorded in 7a stands,
and the reason recorded there -- NO STATE WITHOUT AN ANSWER, the AIF-148 floor
-- turns out to be the smaller of the two reasons.

### 11.6 WITHDRAWN: sec 10.4's "two readers disagree about empty"

Section 10.4 recorded that `WRITEBACK` REFUSES an empty `DBF_ROOT`
(`3973-3977`) while `LOAD` silently falls back to the session global (`4286`),
and filed it as the AIF-118 shape sitting inside the field Q3 wants to
repurpose. **That reading is wrong and is withdrawn.**

The two verbs read the same field for OPPOSITE PURPOSES:

- **LOAD reads it as a SOURCE** -- where to find the tables.
- **WRITEBACK reads it as a DESTINATION** -- where to put them.

Falling back to a guess is reasonable for a source and unacceptable for a
destination, because writing files into a guessed directory is not
recoverable. Each behaviour is CORRECT FOR ITS OWN MEANING. This is not one
answer for two states; it is two questions sharing a field.

**AND THAT CLOSES Q3'S LAST OPEN ITEM.** If `DBF_ROOT` becomes "this
workspace's declared environment", it is unambiguously the SOURCE meaning, and
**LOAD needs no change at all.** WRITEBACK's use of it as a default destination
becomes a BORROWING -- which is precisely what `TO <root>` already exists to
make explicit. WRITEBACK keeps defaulting to it as a convenience and should say
that it is doing so.

Recorded as a withdrawal rather than an edit, because the observation was real
and only the reading was wrong, and because it was overturned by the owner
asking what the difference between SAVE and WRITEBACK actually is. The
distinction that answered it: **SAVE writes the DESCRIPTION (the posture --
tables, index choice, tag, cursors, relations; the tables never move);
WRITEBACK writes the DATA (the table bytes, onto a real disk root); and
SAVE ... MINIDB writes BOTH, into a memo.** MINIDB and WRITEBACK both move
bytes and differ only in destination -- into the catalog, versus onto disk as
tables you can `USE`.

### 11.7 NO CHANGE NEEDED: LOAD already places areas correctly

Asked and measured in the same review: does LOAD take contiguous areas, and
land in DEFAULT when DEFAULT is where you are standing? **Yes to both, already,
and it is R130.** `xbase::find_free_area_for_workspace`
(`src/xbase/area_alloc.cpp`) prefers the slot immediately after the
workspace's highest member; an EMPTY workspace has `highest == -1`, skips that
branch, takes the lowest free slot, and correctly reports
`broke_contiguity = false`, because starting a block is not breaking one. LOAD
reaches it through `find_free_area_for_current_workspace`, which passes
`current_handle()`.

This was NOT always true -- LOAD was the last opener in the tree replaying the
posture's recorded numbers as engine addresses, with `workspace_close_all()`
as the precondition that made address replay safe. Demonstrated live in the
2026-08-29 suite run: OPENJOIN's reload filled slots 0 and 1 and the next ADD
landed at 2.

### 11.8 STILL NOT RULED, and still no code

- **Whether the live and durable roots are one thing or two.** 11.2 and 11.4
  settle WHERE each lives; they do not settle whether `Entry`'s roots are
  written through to the catalog on every change, only at SAVE, or never
  automatically. R129's resolution/navigation split argues they are two things
  saved into each other; that remains the author's reading and is not ruled.
- **DEFAULT.** Section 8's item stands: are DEFAULT's roots the INIT slots by
  definition, and what does `SET PATH` do while standing in DEFAULT? Under
  11.2 plus 11.5 there is an easy answer -- DEFAULT is stamped from INIT at
  startup and behaves like any other workspace -- but DEFAULT is also the one
  workspace with no WS_ID, so it should be said rather than assumed.
- **The four-line switch idiom in `open_mcc_and_cascade.dts`**, which this
  ruling is meant to retire and has not yet.
- **NO CODE HAS BEEN WRITTEN FOR SECTIONS 1-7a OR 11.** Section 7b is the only
  implemented part of R131. `src/cli/**` and `src/xbase/**` are engine and want
  an explicit go.

Ships **review-needed** -- the author does not self-approve.
