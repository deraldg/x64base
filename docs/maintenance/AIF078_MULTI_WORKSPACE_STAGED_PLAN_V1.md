---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-109
  recorded_at_utc: 2026-08-22T19:05:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: c16355c2b
  authorization:
    requested_by: steward (member.derald), in-session 2026-08-22 -- signed off
      D1-D5, then ruled "agreed, no unbounded areas", stated the governing
      shape "multiple workspaces is just a workspace of workspaces of areas",
      required "recursion guards in workspaces like we did databases in memos",
      specified "we need a SET RECURSION ON | OFF -- even with OFF we still
      allow multiple workspaces, just parallel", agreed the semantics, and said
      "begin building".
  report:
    path: docs/maintenance/AIF078_MULTI_WORKSPACE_STAGED_PLAN_V1.md
    kind: plan
---

# AIF-078 -- multiple workspaces, staged. Plan V1.

Status: **plan, review-needed. Stage 1 IMPLEMENTED; stages 2-7 not started.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `c16355c2b`.

Design lane **AIF-078** (multi-workspace addressing and groups); commits land
under AIF-120, which is where the engine work is authorized.

## 1. The governing shape

> **"Multiple workspaces is just a workspace of workspaces of areas."**
> -- steward, 2026-08-22

Recursive containment. A workspace has **members**; a member is either an
**area** (leaf) or another **workspace** (node). Everything below follows.

**This is the tables rule, one level up.** *All tables in the same dir / root
dir for recursion* becomes *all members under the same workspace root,
recursively*. A workspace is the directory, areas are the files,
sub-workspaces are subdirectories.

**Author's correction, recorded.** During the design session I argued the
analogy broke because "areas do not recurse -- there is no second level". That
was wrong: I was analysing contiguity of AREA NUMBERS in a flat index, while
the containment the steward meant is of WORKSPACES. Supply the second level and
it stops being an analogy and becomes the same rule.

## 2. Scope, ruled

**Unbounded areas are OUT.** Steward, 2026-08-22: *"agreed, no unbounded
areas."* `MAX_AREA` stays a configured ceiling; this plan does not touch the
area container.

## 3. Stage-0 census -- measured 2026-08-22, no code changed

**C1. The relation refresh scans the area space, confirmed.**
`find_open_area_by_name_ci` (`src/cli/workarea_util.cpp`) loops
`workareas::count()`, and `WorkAreaSet` is constructed `areas_(xbase::MAX_AREA)`
(`src/cli/workareas.hpp`), so `count()` returns the **configured maximum**, not
the number of open areas. The relation auto-refresh added to
`src/cli/shell_api.cpp` puts that call on every non-suppressed command.
Invisible at 512. **Amendment folded into stage 2** -- the registry hands the
relation layer a handle, so the name scan disappears as a consequence rather
than needing its own detour.

**C2. The area ceiling is structural, three ways.** `constexpr int MAX_AREA` is
an `int`; `std::array<std::unique_ptr<DbArea>, MAX_AREA> _areas`
(`include/xbase.hpp`) is sized at compile time; and the same header records
that the engine *"constructs MAX_AREA areas eagerly"*. `WorkAreaSet` mirrors it
as a second full-size heap vector. **Recorded as fact, not as work**, per
section 2.

**C3. Ownership is barely wired.** One site reads the slot
(`src/cli/workarea_util.cpp`); `gui_workspace_of_area`
(`src/gui/core/gui_runtime_adapter.cpp`) returns `DEFAULT` and says so
honestly; `src/xbase/dbf_file.cpp` assigns the constant handle `1`.

**C4. The GUI presentation is already finished.**
`src/gui/core/gui_workspace_format.cpp` builds the workspace order, prints
`Current:`, counts areas per workspace, and filters tables, indexes and
relations by workspace. `include/gui/core/model.hpp` carries `workspace` on
every row plus `current_workspace` and the workspace list. **The renderer needs
no change** -- it groups by whatever strings it is handed.

## 4. Available art -- what already exists (dogfood before inventing)

House principle, steward: *the system reuses all available art instead of
reinventing.* Applied here, most of the registry already exists.

**A1. The registry is a TABLE.** `src/cli/cmd_workspace.cpp` creates catalog v2
(owner design session 2026-08-11) with, among others: `WS_ID` *"unique
auto-id"* -- the handle allocator; `WS_NAME` *"THE key: the human handle you
load by"*, single-key, no composite keys by owner ruling; `FMT` *"'DTSHEMA 2'
now, 'MINIDB n' later"*; `PAYLOAD_SHA` *"integrity + cycle-detection material
(chartered)"*; `DEPTH` *"MANDATORY recursion declaration: 0 = leaf posture"*;
`SELF_REF` *"payload references a workspace catalog (T/F)"*; `MAX_AREAS`
*"areas the posture opens ... admission input"*; `PREV_ID` lineage. The header
over them names the intent: *"DEPTH/SELF_REF as the recursion guard's
declaration half"*.

**A2. The lookup is a SEEK, not a scan.** `WS_NAME` is single-key by owner
ruling, so a CDX tag answers handle <-> name in O(log n) through the product's
own index. The database indexes its own workspace registry.

**A3. The child list is the posture's `AREA` lines**, already the enumeration
authority `WORKSPACE WRITEBACK` was corrected to use, and already counted at
save time to populate `MAX_AREAS`.

**A4. The admission-gate pattern exists and is the model for the recursion
guard.** `src/cli/cmd_workspace.cpp` hydration: *"Scan the whole container
BEFORE writing any of it ... there was no instant at which the cost was known
and not yet paid, so hydration admission could not be implemented at all."*
Three moves -- pure scan (`include/dottalk/minidb.hpp`, *"the same one the GUI
uses to browse a container without hydrating it"*), decide while the cost is
known and unpaid, then materialize -- with the policy declared elsewhere
(`include/cli/vdisk_config.hpp`, `OnFull{Warn,Spill,Fail}`, absent block means
no opinion) rather than invented at the gate, and `spill` announcing that it
has no implementation instead of *"treating spill as silent permission"*.

**A5. Guarded recursive traversal exists.** `src/cli/set_relations.cpp` walks
with a `seen` set (`if (!seen.insert(key).second) return;`) and a depth cap of
**24**, hardcoded in two functions, plus a `recursive` / `max_depth` public
API pair.

**A6. The live catalog state, read 2026-08-22.** 106 rows, none deleted.
`FMT`: DTSHEMA 2 x13, DTSHEMA 3 x56, MINIDB 1 x37. `MAX_AREAS` populated
(1/13/15/43). **`DEPTH` = 0 on all 106. `SELF_REF` = F on all 106.
`PAYLOAD_SHA`, `EST_HYD_B` and `VERIFIED_AT` populated on none.** The last row
is named `cycle_from_ram` and declares `DEPTH 0 / SELF_REF F`.
(`dottalkpp/data/workspaces/WORKSPACES.dbf`) <!-- cite-check:ignore -->

## 5. Design decisions

**D1. Both directions are materialized. Neither is derived.** The handle
answers *area -> workspace* in O(1); each workspace holds its **child list**
-- heterogeneous, areas and sub-workspaces -- answering *workspace -> members*
in O(n_ws).

**D2. Local numbering at every level.** Each workspace numbers its members
`1..n`. This is what makes contiguity work **without an exception**: a member
added mid-session, every `USE AGAIN` instance included, is simply `n+1`. No
hole, because no claim is made on the global area space.

**D3. No NEW code loops the area space.** As a rule on code this plan writes,
absolute. As a claim about the engine today, false (C2), and out of scope.

**D4. The engine slot and the workspace-local slot are different numbers.**
IMPLEMENTED, stage 1.

**D5. Widths follow identity, not habit.** The handle is 64-bit because it
names a WORKSPACE and workspace identity is `WS_ID`, an `N(10)` column that
overflows int32. The slots are 32-bit because they index AREAS, bounded by
`MAX_AREA`. **Amended from "the pair goes 64-bit"** after section 2 removed the
capacity argument for the slots.

**D6. A workspace may not contain itself, directly or transitively.**
Two jobs, both modelled on A4:
- **Declaration half, strengthen.** `SELF_REF` is computed today as
  `posture.find("WORKSPACES") != npos` -- a substring search of the CARRIER's
  own posture text, structurally blind to a length-prefixed binary payload.
  Compute it from the scanner's member list instead, and populate
  `PAYLOAD_SHA` as the ancestor-identity token it is already labelled to be.
- **Enforcement half, add.** At the same instant the byte-budget gate uses --
  cost known, nothing written -- refuse a payload whose identity appears among
  its ancestors. The comment already names the seam: *"Declaration only --
  enforcement is the hydration stack."*

**D7. `SET RECURSION ON | OFF`. Steward, 2026-08-22.**
Multiple workspaces and NESTED workspaces are separate capabilities.
- **OFF is the default and still allows multiple workspaces, in parallel.**
  The implicit root holds N workspaces; each holds areas. Invariant, and it is
  exactly today's measured state (A6): **every catalog row keeps `DEPTH 0` and
  `SELF_REF F`.**
- **OFF's guard is cheap.** Scan the payload; if any member resolves to a
  workspace or container, refuse. No hashing, no ancestor walk, no lineage --
  `PAYLOAD_SHA` is not needed until `ON`.
- **OFF refuses a nested container LOUDLY. It never flattens it silently.**
  Silent flattening is the defect class this house keeps finding.
- **Toggling applies to subsequent opens and never retroactively closes
  anything** -- the `SET INDEXTXN` precedent (env-driven or runtime; the script
  does not force the flag).
- **Both semantics go in the `@dottalk.usage` block**, because HELP is mined
  from it and a behaviour stated only in a plan is not published.
- **Refusals and caps must ANNOUNCE themselves.** A5's depth cap and seen-set
  both `return` silently. Three hundred lines above them in the same file sits
  the counter-example: the scan limit sets `note_scan_truncated()` and prints.
  Copy the loud one. The depth cap should also stop being a hardcoded 24 and
  join the scan limit as declared, settable, reported policy.

## 6. What R110 concluded, and when it expires

R110 measured *"at rest, exactly one level"* and *"at runtime it is
succession"*, concluding **"no address ever needs two workspace segments."**
That was measured **under succession**, which stage 4 removes. **The conclusion
expires there.** `WorkspacePath` -- kept by R110 as *"the only written record
that depth > 1 is unresolved"* -- becomes required rather than vestigial, and
`WS.#n.TABLE` (level 4, recorded as *"a type, not a feature -- zero `src/cli`
consumers"*) gets its first consumer.

R110 also measured that of 37 containers, 623 members and 196 memo objects,
**zero are a container or a posture**. A MINIDB container has never carried
another container. The format can -- length-prefixed and payload-agnostic --
but nothing has. That is stage 7, behind `SET RECURSION ON`.

## 7. Stages

Stages 1-3 leave behaviour identical: one workspace named DEFAULT. Nothing
user-visible changes until stage 4.

**Stage 0 -- census. DONE (section 3).** Open: whether I1.2's blocker
(composite-verb coverage gap, DTSHEMA v4) sits in this path or beside it.

**Stage 1 -- engine slot vs workspace-local slot. IMPLEMENTED.**
`_ws_slot` was documented as both. Split into `_engine_slot` (array position,
stamped once) and `_ws_local_slot` (1..n inside the workspace, chartered and
unset until stage 2). Two call sites. D5 amended and stated in the header.
*Verify:* full rebuild (`include/xbase.hpp` touched), `REGRESSION ALL` +
explicit-run specs. Nothing moves.

**Stage 2 -- use the registry that already exists. Still one workspace.**
Read and write catalog v2 (A1) instead of inventing a structure: `WS_ID` is the
handle, `WS_NAME` the name, a CDX tag on `WS_NAME` the lookup (A2), the
posture's `AREA` lines the child list (A3). `src/xbase/dbf_file.cpp` asks the
registry instead of assigning `1`; `close()` deregisters; `_ws_local_slot` gets
assigned. **C1's amendment lands here:** the relation layer takes a handle
instead of resolving by name.
*Verify:* nothing moves. Plus an explicit-run spec asserting **child list
contents** -- it must be able to go red.

**Stage 3 -- scoped, recursive close.**
`schema_close_all()` becomes `close_workspace(handle)`: post-order walk of the
subtree, children before parent -- succession's own ordering, scoped instead of
applied to the universe. The `0..max_areas` form is deleted, not left beside it.

**Stage 4 -- break succession. FIRST user-visible change. `SET RECURSION OFF`.**
Two or more workspaces open, in parallel. Gated on **R112's ruling** --
qualification required behind an instrumented first-wins migration **whose
recorded count must read zero** -- and on D7's OFF-mode guard.
*Verify:* a two-workspace spec. Same table name in two workspaces, unqualified
reference refused, scoped close leaves the sibling intact, a nested container
refused loudly, and `DEPTH 0 / SELF_REF F` still true of every catalog row.

**Stage 5 -- the GUI lights up. Little new code.**
`gui_workspace_of_area` resolves through the registry. It takes an `AreaId` it
deliberately ignores; its caller already holds the `DbArea&`, so it can read
the handle directly. The renderer is untouched (C4).

**Stage 6 -- addressing and scoped save.**
`WorkspacePath` / `WS.#n.TABLE` get consumers. `workspace save` serializes ONE
workspace from its child list -- the `WORKSPACE WRITEBACK` precedent, whose
first cut asked the session instead of a declaration and *"silently wrote 15 of
27 files while reporting cheerful success"*, with the note *"a count is a fact
about a loop until something declares what it SHOULD be."*

**Stage 7 -- `SET RECURSION ON`. Nesting, behind the switch.**
D6's full guard: seen-set and depth cap copied from A5 with the silence fixed,
`PAYLOAD_SHA` populated and compared against ancestors. A MINIDB container
carries another container for the first time; `DEPTH` and `SELF_REF` stop
reading zero. `FMT`'s *"MINIDB n later"* is cashed.

## 8. Out of scope, stated

- **Unbounded areas** -- ruled out.
- **Workspace-scoped relations.** Engine-global today; a relation can span two
  workspaces' areas. `WorkspaceRelationInfo` carries the field so the column
  can show what the runtime cannot yet separate. Own ruling, own work.
- **Renumbering or compaction.** Nothing renumbers.
- **`EST_HYD_B`.** Empty on all 106 rows, so the catalog cannot make an
  admission decision without opening the payload. Named, not fixed.

## 9. Decisions owed

1. **D6 and D7 sign-off in the record.** Both were given in-session; this
   document is where they become reviewable.
2. **When the R112 migration instrumentation runs and who reads the count.**
   Stage 4 cannot land until it reads zero.

## 10. Good Neighbor note

**What changed.** This document only; it is a plan, not an implementation.
Stage 1's code lands in its own commit.

**Whose area.** AIF-078 design, AIF-120 implementation. `src/cli/**`,
`src/xbase/**` and `include/**` are engine and want the explicit go the steward
gave on 2026-08-22.

**How to verify.** Each stage carries its own verification line in section 7.
The plan itself is verified by reading it against sections 3, 4 and 6, every
claim in which was measured on `c16355c2b` rather than recalled.

**How to undo.** Delete this file; no code depends on it.
