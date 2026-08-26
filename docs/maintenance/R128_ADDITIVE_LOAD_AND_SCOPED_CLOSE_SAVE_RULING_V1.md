# R128 -- LOAD IS ADDITIVE, AND CLOSE AND SAVE ARE SCOPED TO ONE WORKSPACE

    Ruled   : 2026-08-26 by member.derald.
              "yes additive load and selective close/save"
              "we can also open two dir into two workspaces too"
              "open should be additive or it will kill the other
               workspaces, if a person wants it open by itself then they
               can close all of the other workspaces first like a sane
               person"
    Lane    : AIF-078 (multi-workspace), with AIF-070 (carriers) downstream.
    Status  : review-needed. The author does not self-approve.
              Implemented the same day; see sec 6 and sec 7.
    Basis   : source read at HEAD ad34e9145. Every claim below is marked
              MEASURED (read in the tree, line cited) or NOT MEASURED.
              Nothing here was run: there is no current build on this side,
              so nothing in this document is runtime-proven.
    Records : claude/THREE_LANES_INTEGRATION.md sec 4 and sec 6, which named
              this as the load-bearing decision and did not take it.

## 1. THE RULING

**Opening a workspace no longer closes the one you were in.** LOAD from a
saved posture and OPEN of a directory both stop being replacement-style. Two
directories opened are two workspaces, each holding its own areas.

**CLOSE and SAVE are scoped to ONE workspace by default**, with an explicit
form for everywhere. CLOSE already reads this way; SAVE does not.

**Replace is not deleted, it is COMPOSED**: `WORKSPACE CLOSE ALL` then
`WORKSPACE OPEN <dir>`. No verb keeps a meaning that can silently close
someone else's work. See 4.3 for why the default belongs on this side.

## 2. WHAT THIS ENDS -- F2, AND R110's MISSING REASON

R110 kept the `WorkspacePath` type and STRUCK its stated reason, because F2
had measured that carrier and payload never coexist. F2 held because LOAD
replaced: the state where areas from two workspaces are open at once could
not occur, so an address never needed to name its workspace.

**F2 is now ended by decision, not by measurement.** From this ruling, two
workspaces can be populated at once on both surfaces, and the type R110 left
justified by nothing has its reason back -- from HERE, and not from container
nesting, which was the justification R110 examined and rejected.

This is also the answer to the ambiguity THREE_LANES sec 3 left open. The log
line `Workspace: mcc_db` was either the CATALOG ROW loaded from or a RUNTIME
HANDLE the areas should have joined, and nothing in the tree decided which.
**It is both.** A load names the workspace it loads into.

## 3. WHAT IS ALREADY BUILT -- most of the engine half

MEASURED. The CLI shipped multiple workspaces at AIF-078 stage 3:

- `WORKSPACE NEW / SWITCH / REGISTRY` and, since D10.3 on 2026-08-23,
  `WORKSPACE DESTROY` (`src/cli/cmd_workspace.cpp:4535`, calling
  `xbase::workspace::destroy` at `:4623`).
- Bare `CLOSE` is ALREADY scoped to the current workspace
  (`schema_close_current_workspace`, `:1635`), walking membership via
  `close_workspace_tree` rather than sweeping `MAX_AREA`. `CLOSE ALL` keeps
  the everywhere meaning. **Selective close is done at the CLI.**
- `WORKSPACE ADD` is the additive verb and preserves existing areas
  (`:4825`), stated in the file's own header at `:129`.
- The allocator is already workspace-aware:
  `xbase::find_free_area_for_workspace`, and membership is
  `workspace::join(handle, engine_slot)`.

**And none of it costs a new dependency.** The whole membership API --
`create`, `set_current_handle`, `find_by_name_ci`, `members`, `destroy` -- is
header-only in `include/xbase/workspace_membership.hpp`, and both `dottalkpp`
and the GUI already link `xbase`. So the GUI can reach it without linking the
CLI. **R122 is not touched by this ruling**, and the precedent is the one R124
used for the relation wire record.

## 4. FOUR THINGS THIS RULING MAKES WRONG THAT ARE NOT WRONG TODAY

### 4.1 SAVE HAS NO WORKSPACE DISCRIMINATOR, AND IT IS LIVE NOW

MEASURED. `schema_save_to_string()` (`cmd_workspace.cpp:1828`) enumerates:

    for (int area0 = 0; area0 < xbase::MAX_AREA; ++area0) {
        xbase::DbArea& A = get_area_0based(area0);
        if (!area_open(A)) continue;

No handle filter appears anywhere in it. It takes every open area in the
process.

**THE COUNT DISCIPLINE, exactly: a number taken from an authority that holds
more than one KIND, with no discriminator applied.** And this is not a future
consequence of the ruling. Stage 3 shipped on 2026-08-24, so a CLI session can
already put areas in two workspaces -- which means `WORKSPACE SAVE mcc_db`
today writes the other workspace's areas into a posture named `mcc_db`. The
ruling does not create this defect. It removes the last reason it was rarely
reached.

**It is one place.** `schema_save_to_string` is the SINGLE serializer -- the
file writer (`schema_save_to_file`, `:2002`), the memo carrier
(`save_to_memo`, `:3036`) and the MINIDB container all pass through it, and
its own comment at `:1817` says so. Scope it once and file, memo and MINIDB
all become scoped together.

NOT MEASURED: whether a scoped save changes any existing green spec. Every
spec in the tree runs in one workspace, where scoped and swept are
byte-identical -- the same argument that let bare CLOSE change without moving
the suite -- but that is an inference, not a run.

### 4.2 THE GUI CANNOT BE IN A WORKSPACE AT ALL

MEASURED. `src/gui` reads `xbase::workspace::current_handle()` in three places
(`session.cpp:511`, `:577`, `:1664`) and calls `workspace::create` and
`set_current_handle` in NONE. There is no create, no switch, no entry.

The engine's model is "an area joins whichever workspace is CURRENT when the
area is OPENED -- SWITCH-then-open, never open-then-assign"
(`cmd_workspace.cpp:138`). On the GUI surface CURRENT has only ever had one
value.

So `WS: DEFAULT` on every area after a load is a TRUE report, as sec 3 of
THREE_LANES established -- but the reason is stronger than that document
knew. It is not that the load forgot to enter a handle. **It is that the GUI
has no way to be anywhere else.**

And there are THREE close-all-and-clear sites, not the two sec 4 cited:

    session.cpp:1797   mirror_workspace_open_directory  (WORKSPACE OPEN <dir>)
    session.cpp:2051   the DTSHEMA posture mirror        (WORKSPACE LOAD)
    session.cpp:2760   the Command box `workspace close`

The third is the one that matters for selective close: it closes every GUI
area unconditionally and reports "All GUI work areas were closed", while the
CLI verb it shadows has been scoped since stage 3. **Two surfaces, one verb
name, two meanings.**

### 4.3 THE ADDITIVE VERB CANNOT TAKE A DIRECTORY -- and OPEN is now the one that must

MEASURED. `WORKSPACE ADD` is additive and single-table by construction. It
refuses the directory case in as many words (`:4851`):

    "WORKSPACE ADD: recursive is not supported for single-table add."

"Open two dirs into two workspaces" needs a directory-shaped additive open,
and no verb spells one today.

**RULED THE SAME DAY, BY THE SAME OWNER:** *"open should be additive or it
will kill the other workspaces, if a person wants it open by itself then they
can close all of the other workspaces first like a sane person."*

**OPEN ITSELF BECOMES ADDITIVE.** Not a new verb, and not `ADD` growing a
directory form. The replace behaviour is not re-spelled anywhere -- it is
COMPOSED out of verbs that already exist:

    WORKSPACE CLOSE ALL
    WORKSPACE OPEN <dir>

**And the reason that is the right trade is that the two mistakes are not
equally recoverable.** An additive open the user wanted to be exclusive costs
one extra command. A replacing open the user wanted to be additive closes
every area in every other workspace without being asked -- and if any of them
was dirty, no command undoes it. When one error is a keystroke and the other
is data, the default belongs on the keystroke side.

**WHAT THIS MAKES `ADD`, and it is not deleted.** `ADD` stays the
single-table additive open. OPEN and ADD stop differing in ADDITIVITY -- both
add -- and differ only in GRANULARITY: OPEN takes a directory, ADD takes one
table. That is a better seam than the one it replaces. A verb pair split on
*does this destroy your session* is a trap; a verb pair split on *how much do
you want* is a menu.

**A CONSEQUENCE THAT IS NEW, and is NOT ruled: the second OPEN of a directory
already open.** Under additive OPEN a directory mints a workspace, and
`WORKSPACE NEW` refuses a duplicate name outright --
`if (xbase::workspace::find_by_name_ci(nm) != 0)` at `:4480`, *"names are the
handle a person uses"*. So the second `OPEN DBF\SALES` would either refuse or
need a uniquified name, and neither is right: refusing makes a harmless act an
error, and uniquifying puts two workspaces on one directory, which is the
ambiguity the refusal exists to prevent.

**It should RE-ENTER the workspace that directory already has.** A second open
of the same place is a navigation, not a creation. What it does with the
CONTENTS is the open question -- files added to the directory since, files
removed, areas the user closed by hand -- and that is a reconcile rule, not a
grammar one. Not ruled here.

### 4.4 TWO SURFACES SAY A NAME CANNOT BE RECLAIMED. IT CAN.

MEASURED, and it is in the USAGE OUTPUT, not only in a comment.

`cmd_workspace.cpp:175-179`, the header block:

    A WORKSPACE NAME CANNOT BE RECLAIMED within a session. CLOSE ALL releases
    every area everywhere, and afterwards the registry STILL lists every
    workspace at members 0; there is no DROP, DELETE or REMOVE verb. A script
    that declares workspaces is therefore idempotent per PROCESS, not per
    session -- run it once, or restart rather than trusting a second pass.

`cmd_workspace.cpp:4310-4311`, what a user reads from `WORKSPACE USAGE`:

    The model is SWITCH-then-open. Names must be unique, and a name cannot be
    reclaimed in a session -- there is no DROP verb.

**Stale at HEAD, both of them.** `WORKSPACE DESTROY` shipped 2026-08-23
(D10.3, `:4535`, calling `xbase::workspace::destroy` at `:4623`), and the
LADDER spec's `WSL_T4` proves reclamation directly: destroy `WSLADR1`, create
it again, and the second WS_ID must be GREATER than the first. It passed
in-suite on 2026-08-24 at 156 -> 157.

**And the correction for the line four rows above it DID land.** `:4307-4308`
reads *"This line said NEW was runtime-only until 2026-08-24; that stopped
being true when D10.1 landed on 08-23."* Someone walked this exact block on
2026-08-24, fixed the NEW claim, and left the DROP claim standing beside it.

This is the third contract drift in the header block that exists to prevent
contract drift, and the block records the previous two in its own text
(MEMO/MINIDB dated 2026-08-12; NEW/SWITCH/REGISTRY/CLOSE ALL dated
2026-08-24). A claim that decays without ever going red -- the shape the R
register's own preamble names, one layer up.

Load-bearing here, not trivia: under additive open a workspace is created per
opened directory, so a long session accumulates handles. Whether closing a
workspace RETIRES it decides whether the second open of the same directory
gets a fresh workspace or silently ADOPTS the first one's identity -- and
adoption inheriting whatever a previous run left behind is the history
dependence the LADDER spec's own promotion note calls "wearing a green suit".
The answer exists (`DESTROY`). Which of close / save / destroy the surfaces
call is not decided here.

**The doc fix is NOT made in this ruling.** Both sites are `src/cli/**`,
which wants an explicit go, and a comment edit is still an engine-file edit.
Named for v7 cleanup, or for the same go that carries sec 5 item 1.

## 5. WHAT THIS RULING DOES NOT DECIDE

Named so they are not settled by drift:

1. ~~The grammar.~~ **RULED the same day -- see 4.3.** OPEN itself is
   additive; replace is composed as `CLOSE ALL` then `OPEN`. What replaced it
   on this list: **what a second OPEN of an already-open directory reconciles.**
2. **What NAMES a workspace on `OPEN <dir>`** -- the directory leaf, the full
   path, or the user. Names must be unique, so a leaf collides across roots.
3. **Whether a per-workspace close also DESTROYS.** (4.4.)
4. **How SAVE spells everywhere.** CLOSE's grammar (bare = scoped, ALL =
   everywhere) argues for `SAVE ... ALL`, and matching it costs nothing.
5. **Relations.** They are still cleared GLOBALLY on a scoped close --
   `cmd_workspace.cpp:180` records it as a stage-3 limitation. Additive load
   makes a global clear reach across workspaces routinely rather than rarely.
6. **The UI shape.** THREE_LANES sec 5 proposed a tree that keeps the engine
   slot numbers visible and surfaces `broke_contiguity` structurally. This
   ruling makes that state reachable; it does not choose the widget.

## 6. NO CODE WAS WRITTEN -- AND THEN IT WAS

**As ruled, 2026-08-26:** nothing in `src/` changed. `src/cli/**` and
`src/xbase/**` are engine and wanted an explicit go; `src/gui` waited on sec 5
item 1, because the grammar decides what the GUI is mirroring.

**CORRECTED THE SAME DAY.** The owner gave that go -- *"I want you to build
these features we have drafted"* -- and answered the four open grammar
questions before a line was written. Both halves are now implemented and
measured: scoped SAVE and additive OPEN in the CLI, additive OPEN and LOAD and
a scoped close in the GUI, and a registered regression (`ADDOPEN`) that goes
RED against the previous binary.

This paragraph is a correction rather than an edit of the one above it. The
sentence "no code was written" was TRUE of the moment it describes, and a
document that silently retunes its own claims to match what happened later is
the defect this house keeps finding one layer up. Section 7 carries the scope
calibration for the code that followed.

## 7. SCOPE CALIBRATION AND TASK FIELDS

Added 2026-08-26 after re-onboarding through the upgraded portal. The
professional model's own acceptance test (AIF-132 sec 8) was run against this
record and found it INCOMPLETE: no declared lifecycle, no scope calibration, no
proof registry row. This section closes the calibration; the proof row is a DBF
write and is NOT made here.

The planning subset is filled first because it feeds the superset
(`SCOPE_CALIBRATION_SEED_V1.md`, precedence settled AIF-082 6.5c). The seven
shared fields appear once and agree.

    operating_mode  : production
    change_class    : C3
    build_target    : dottalkpp_runtime AND frontend; xbase_engine touched
                      header-only (workspace_naming.hpp adds no symbol to the
                      library). The template spells one value and this change
                      has three axes -- reported rather than narrowed to fit.
    product_profile : DEVELOPMENT (the maintainer's pro-md default)
    index_profile   : LMDB (the maintainer's pro-md default)
    scope_reason    : an owner ruling changed the observable behaviour of four
                      shipping verbs (OPEN, LOAD, SAVE, CLOSE) across two
                      surfaces, and changed what SAVE writes into a persisted
                      posture. Persistence-affecting and cross-cutting, which
                      the seed says must not be labelled minor to dodge its
                      gates.
    affected_authorities
                    : src/cli (engine), src/gui, include/xbase (new header),
                      the .dtschema/MINIDB posture format's CONTENT (not its
                      grammar), the regression suite registry, R110's struck
                      justification, and the WORKSPACE USAGE text -- which is
                      still stale on a separate count (sec 4.4) and is NOT
                      corrected by this change.
    minimum_gate_set
                    : (a) compile clean on both targets, warnings read;
                      (b) a self-asserting registered regression that goes RED
                      against the previous binary -- ADDOPEN, four
                      discriminating arms, measured both ways;
                      (c) the default suite unmoved, proven by byte-comparing
                      marker output against a baseline binary built from the
                      same tree rather than by reading it;
                      (d) the GUI core's five existing tests still green;
                      (e) the changed spec re-run under the maintainer's
                      product and index profile.
    optional_educational_gates
                    : none. Nothing here was run for teaching value.
    deferred_gates_and_residual_risk
                    : FOUR, named rather than absorbed.
                      1. NO HOST TOOLCHAIN RUN. Everything is g++ 13.3 on
                         Linux. A sandbox green is not a green on MSVC, and
                         this document does not claim one.
                      2. INDEX ATTACHMENT IS NOT EXERCISED. The changed OPEN
                         loop still calls find_index_for_open_area and
                         attach_workspace_index untouched, but the ADDOPEN
                         fixtures carry no index, so the LMDB run proves the
                         build and the areas -- not the attachment. Unchanged
                         BY INSPECTION is not unchanged by measurement.
                         Closing it needs an indexed fixture.
                      3. THE LMDB RUN IS NOT AN A/B. The two-binary comparison
                         was made under LEAN/NONE; under DEVELOPMENT/LMDB only
                         the new binary was run. Green on both, discriminated
                         on one.
                      4. THE QT APPLICATION WAS NEVER LAUNCHED. Every GUI claim
                         is about dottalk_gui_core, its five tests, and the
                         compiler.

    id                : R128 (ruling identity). No task_id: this work has no
                        work-item row, which is the second gap sec 8 found.
    title             : LOAD IS ADDITIVE, AND CLOSE AND SAVE ARE SCOPED TO ONE
                        WORKSPACE
    area              : workspace / work-area lifecycle
    owning_lifecycle  : DotTalk++ SDLC (engine, runtime, command behaviour)
    sdlc_lane         : review
    truth_state       : source-evidenced for the defects named in sec 4;
                        runtime-proven for the two behaviours ADDOPEN asserts
    proof_state       : runtime_observed on the authoring toolchain only, and
                        NOT registered -- there is no proof.* record. The
                        engineering standards seed says a behaviour lane is not
                        done until a self-asserting regression protects it AND
                        a runtime_observed proof exists; the first half is done
                        and the second half is a governed DBF write nobody
                        authorised.
    risk_class        : moderate. It changes what a persisted posture contains,
                        so a posture saved after this change and read before it
                        describes a different set of areas. No format change,
                        no migration, no reader breaks.
    source_path       : src/cli/cmd_workspace.cpp, src/cli/cmd_regression.cpp,
                        include/xbase/workspace_naming.hpp,
                        src/gui/core/session.cpp,
                        src/tests/test_gui_area_membership.cpp,
                        dottalkpp/data/scripts/workspace_additive_open.dts
    website_path      : none produced by this change. A website Alpha treatment
                        of this lane EXISTS -- Codex published it 2026-08-26 and
                        posted the notice to the board -- but it is upstream of
                        nothing here and this change does not update it.
    next_gate         : maintainer review, then commit and a host-toolchain
                        build. Publication ascent is NOT in scope and is a
                        separate authorization domain.
    owner             : member.derald
    steward           : member.ai.claude.cowork, run COWORK-20260826-001
                        (parent COWORK-20260825-001)
    status            : development-only, uncommitted, review-needed

## Good Neighbor

    What changed  : this document and one register row. No source, no data.
    Whose area    : AIF-078 (multi-workspace) primarily; AIF-070 (carriers)
                    inherits 4.1 because the serializer is shared; R110
                    inherits sec 2. Prescribes to none of them beyond the
                    ruling itself.
    Authorization : the owner's ruling of 2026-08-26, quoted verbatim at the
                    head of this file.
    Verify        : sed -n '120,200p' src/cli/cmd_workspace.cpp
                    sed -n '1817,1900p' src/cli/cmd_workspace.cpp
                    sed -n '4825,4870p;5066,5125p' src/cli/cmd_workspace.cpp
                    grep -n 'impl_->areas.clear()' src/gui/core/session.cpp
                    grep -rn 'workspace::create\|set_current_handle' src/gui
    Undo          : delete this file and the register row. Nothing depends on
                    it yet.
