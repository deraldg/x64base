# AIF-137 -- THE RELATION STORE IS PARTITIONED BY WORKSPACE AND THE RELATION PARENT IS NOT

    AIF     : AIF-137, claimed 2026-08-27T11:03:14Z with
              `session_coordinator.py claim-aif` (atomic O_EXCL, no
              number passed -- the allocator chose). Claim file
              verified present at `coordination/aif/AIF-137.claim`,
              run COWORK-20260827-001, member.ai.claude.cowork.
    Found   : 2026-08-27 by member.ai.claude.cowork, running the R112
              ambiguity ledger under R128 additive OPEN.
    Lane    : AIF-078 (multi-workspace) / AIF-120 (name resolution).
              Related: R112 (name ambiguity), R128 (additive OPEN),
              R129 draft (the workspace cursor).
    Status  : review-needed. The author does not self-approve.
    Evidence: RUNTIME-PROVEN. It ran; sec 2 names what it ran against.
              Source tracing in sec 3 is MEASURED (line cited).
    Severity: the crossing is a READ today. Sec 5 states exactly what
              would make it a write, and does not claim it already is.

## 1. THE FINDING IN ONE SENTENCE

**The relation STORE was partitioned by workspace at AIF-078 I1.2; the relation
PARENT was not** -- so a relation refresh standing in one workspace resolves a
parent name to another workspace's area, **with no relation defined anywhere
and no user command that names a table.**

## 2. WHAT IT RAN AGAINST

Interactive CLI session, `.\datarun.ps1`, 2026-08-27.

**THE BINARY IS IDENTIFIED BEHAVIOURALLY, NOT BY ITS VERSION STRING.** It
reports `dottalk++ v0.6 (2026-08-24, c39d966c dirty) (Aug 26 2026 14:47:54)` --
a date BEFORE R128 landed, so that string cannot identify it. The evidence
that it is an R128 binary is in the transcript: the second `WORKSPACE OPEN`
placed 13 tables at engine slots 13..25 and left the first workspace's 13
standing at 0..12. Under the replacing OPEN the second would have closed the
first. Named here because a stale version string is exactly how a runtime
claim gets attached to the wrong build.

Fixtures, read-only: `dottalkpp\data\dbf\x64` and `...\dbf\x32`, which share
eight table basenames including BUILDING and STUDENTS.

    WORKSPACE REGISTRY                    -> ambiguity 0, DEFAULT, 0 members
    WORKSPACE OPEN ...\dbf\x64 AS WSX64   -> handle 2, WS_ID 208, slots 0..12
    WORKSPACE OPEN ...\dbf\x32 AS WSX32   -> handle 3, WS_ID 209, slots 13..25
    WORKSPACE REGISTRY                    -> ambiguity 2
    REL LIST                              -> "Relations for parent: BUILDING" / "(none)"
    SELECT students                       -> "Selected area 8"
    WORKSPACE REGISTRY                    -> ambiguity 6

The first `REGISTRY` is the guard: without it a non-zero later reading cannot
be attributed to anything.

## 3. WHAT WAS OBSERVED

### 3.1 The ledger fired on OPEN, before any table name was typed

    NAME: 'BUILDING' is open in 2 areas (ws 2 area 0, ws 3 area 13);
          resolved to area 0 [REL refresh parent].
          Qualify the name -- first-wins is a migration step (R112).

**Current handle was 3. It resolved to workspace 2.**

### 3.2 No relation existed

    . rel list
    Relations for parent: BUILDING
      (none)

An EMPTY store whose inferred parent is an area in ANOTHER workspace. **The
crossing requires no `SET RELATION`.**

### 3.3 The path, MEASURED in source

    refresh_relations_if_enabled_safe()      cmd_workspace.cpp:2587, :5266,
                                             :5422, :5480
      -> refresh_for_current_parent()        set_relations.cpp:717
        -> current_parent_name()             set_relations.cpp:709
           override empty
           -> infer_parent_from_workarea()
        -> refresh_from_parent_name(name)
          -> find_open_area_by_name_ci(name, "REL refresh parent")
                                             set_relations.cpp:464

`find_open_area_by_name_ci()` sweeps every open area, first match wins, lowest
engine slot, **no workspace filter** (`workarea_util.hpp:53`). It has 36 call
sites; the header states 21 depend on first-match-wins.

### 3.4 The asymmetry that is the defect

    THE STORE IS SCOPED:
      relations_store()  ->  relations_store_for(current_handle())
                                             set_relations.cpp:109
      clear_all_relations_for(ws)            set_relations.cpp:691

    THE PARENT IS NOT:
      current_parent_override()   -- ONE global string, all workspaces
      current_parent_name()       -- resolves it unscoped, :710
      refresh_from_parent_name()  -- resolves unscoped, :464

**A scoped store consulting an unscoped lookup.** The partition is real; the
lookup that feeds it is not partitioned.

### 3.5 It was predicted and recorded, and then found by running

`cmd_regression.cpp:513` (the relation-scope spec, 2026-08-23) states:

    RECORDED NOT FIXED: current_parent_override() in set_relations.cpp is
    still ONE global rather than per workspace; it is the REL parent
    shorthand and not the graph, so it does not affect these arms, but it
    is the next workspace-blind piece of relation state and should not be
    found by surprise.

**It was not found by surprise. It was measured.** The one thing that record
got wrong is "it is the REL parent shorthand and not the graph" -- true of the
OVERRIDE, but `current_parent_name()` falls through to
`infer_parent_from_workarea()` when the override is empty, so the unscoped
resolution happens on the DEFAULT path and not only on the shorthand one.

## 4. WHY IT WAS UNREACHABLE UNTIL 2026-08-26

R112's ambiguity ledger has read zero since it was built, and
`cmd_regression.cpp:465` says why: the ledger is

    STRUCTURALLY ZERO -- not untested, unreachable -- until two workspaces
    can be open at once and cross-workspace names may repeat

and calls the ledger line **"a TRIPWIRE for AIF-078 stage 4, not a migration
counter."**

Within ONE workspace `cmd_use.cpp` auto-renames a duplicate stem to
`<stem>2` and announces it, so no collision can form. **R128 landed
2026-08-26 and made two populated workspaces ordinary. The tripwire was armed
for one day before it was read, and it fired on the first attempt.**

## 5. WHAT WAS AND WAS NOT DAMAGED

**STATED RATHER THAN IMPLIED, because the difference is the whole severity.**

With the store empty, `refresh_from_parent_name()` called
`parent->readCurrent()` on WSX64's BUILDING and then returned at the store
lookup. **That is a READ across the boundary. No cursor was moved and no data
was changed.**

It is **one `SET RELATION` away** from the write case: with an edge present,
`goto_first_match(*child, kv, g_scan_limit)` (`set_relations.cpp:477`) drives
the CHILD's cursor from the foreign PARENT's field values, and the `!found`
branch calls `child->top()` and clears the subtree. That is cross-workspace
action-at-a-distance on a live cursor.

**NOT CLAIMED: that this has ever happened in the field.** Not measured. The
arrangement that reaches it -- two populated workspaces with a relation --
became possible on 2026-08-26.

## 6. A SECOND FINDING: THE INSTRUMENT DOES NOT SEE THE OTHER CROSSING

Read the site tag on the STUDENTS row:

    name STUDENTS  site REL refresh parent  chose area 8  hits 2
                   candidates ws2:a8 ws3:a21

**`REL refresh parent`, not a SELECT site.** `SELECT students` DID cross --
it selected area 8, which is WSX64's table, while the current handle was 3 and
WSX32's own STUDENTS sat at area 21. But `cmd_select.cpp` runs its own scan
(`:200`) and does not call `find_open_area_by_name_ci()`, so it records
nothing. The row exists only because the refresh that followed happened to
resolve the same name.

**Had SELECT crossed on a name the refresh did not touch, the counter would
have read zero while a crossing occurred.**

R112 sec 6a makes that counter the gate: first-wins-plus-warning is admissible
only as an instrumented phase "whose counter has to reach a measured zero."
**A counter blind to one of its own crossing paths cannot retire anything, and
its zero would mean "not instrumented" while looking like "clean".** That is
the AIF-118 shape, reappearing one level inside the instrument whose
print-even-at-zero rule exists to prevent it.

## 7. COUNTS

`ambiguity_count()` increments per resolution; the ledger latches per
(name, site). Both readings agree:

    after two OPENs   : 2 resolutions   BUILDING hits 2
    after one SELECT  : 6 resolutions   BUILDING hits 4, STUDENTS hits 2

**One `SELECT` caused four cross-workspace resolutions.** Per sec 6 that four
is a FLOOR, not a measurement.

## 8. WHAT THIS DOES NOT SETTLE

- **The fix direction is answered and the ROOT CAUSE is sharper than "add a
  filter".** Grok, `ANSWERS_TO_CLAUDE_2026-08-27.md` Q1: P6 governs every
  unqualified `name -> area` lookup including engine refresh; do not patch 36
  sites in one shot -- split `find_open_area_by_name_ci` into scoped /
  given-handle / explicit-cross; and **"if you already have the work area, do
  not lower it to a string and search the process."**

  **THAT LAST CLAUSE IS THIS DEFECT'S ROOT CAUSE, AND IT IS MEASURED.**
  `infer_parent_from_workarea()` (`set_relations.cpp:157-165`) holds the
  `DbArea*` and returns `A->logicalName()`. `refresh_from_parent_name()` then
  takes that string and searches every slot to find the area back -- and finds
  a different one. **The round trip loses identity: area -> name -> search ->
  a different area.** On this path the fix is not a filter at all; it is not
  lowering. A filter would make the wrong answer scoped rather than making the
  right answer reachable.

  The grain for the split already exists: `find_open_areas_by_name_ci()`
  (plural, `workarea_util.hpp:68`) returns every candidate and deliberately
  does NOT record ambiguity, "so the caller can see them."

  NOT RULED: which of the 36 sites are scoped, which take a handle, and which
  are legitimately cross-workspace.
- **Whether `current_parent_override()` becomes per-workspace or is removed.**
  Per-workspace matches the store; removal is possible if
  `infer_parent_from_workarea()` is always correct, which is not measured.
- **What an unqualified name means**, which is ruled elsewhere:
  `WORKSPACE_IDENTITY_AND_CATALOG_PRECEPTS_V1.md` P6 (member.derald + xAI
  Grok, owner-accepted 2026-08-27) says the current workspace's member only.
  **This finding is the evidence that P6 must reach the ENGINE's own
  resolutions and not only names a user types** -- nothing was typed here.
- **The area cursor**, which is R129's subject and not this one.

## 9. NO CODE WAS WRITTEN

`src/cli/**` and `src/xbase/**` are engine and want an explicit go. Nothing was
changed. The run was read-only on the tables.

**RESIDUE, stated:** the two `WORKSPACE OPEN`s minted WS_ID 208 and 209 under
D10.1; `WORKSPACE DESTROY` retired both by supersession, so the names are free,
handles 2 and 3 are not reused, and two superseded rows remain in
`WORKSPACES.dbf` as history (D10.3). Precept P3 proposes ending that mint.

**GOOD NEIGHBOR**

- **What changed:** nothing in the tree except this document and the AIF-137
  claim file the allocator wrote.
- **Whose area:** AIF-078 / AIF-120. A fix would touch
  `src/cli/set_relations.cpp` and possibly `src/cli/workarea_util.cpp`, both
  engine-adjacent, plus `src/cli/cmd_select.cpp` for the sec 6 tagging.
- **What authorization:** the owner authorized the measurement run and the AIF
  claim on 2026-08-27. No fix is authorized.
- **How to verify:** re-run sec 2 against any R128-or-later binary. It fired
  on the first attempt with no tuning.
- **How to undo:** delete this file and release AIF-137 with
  `session_coordinator.py release-aif`.
