# ArcticTalk Workbench milestones

Owner: member.derald. Lane: AIF-120. Author: member.ai.codex.
Recorded: 2026-09-18. Run: CODEX-20260918-UIDEF-MILESTONES.
Authorization: owner accepted the GUI outline and requested milestones, using
the simple house names M1, M2, M3, etc.

This is the maintained sequence for the commissioned generated Workbench.
The working foundation is the baseline, not another numbered milestone.
M1, M2 and M3 are locally complete on Windows; M4 through M7 are planned.
M3's native buffer limits and engine handoff are recorded in its closeout below.
Source and evidence remain uncommitted. [M1 evidence and closeout](AIF120_WORKBENCH_M1_V1.md).
[M1 file-location follow-up](AIF120_WORKBENCH_FILEPATHS_V1.md) removes DO and
workspace-file fallback searching and adds the generated Run script modal.
[M1 schema-location follow-up](AIF120_WORKBENCH_LOAD_ROOTS_V1.md) exposes Load's
table/index directories and checks missing members before accepting the form.
[M2 evidence and closeout](AIF120_WORKBENCH_M2_V1.md) covers the live workspace
tree, keyboard/context actions, search and identity preservation.
[Existing Workbench comparison](AIF120_WORKBENCH_COMPARISON_V1.md) records the
older native/Python feature inventory and the catalog-flow gap found after M2.
The direct catalog-flow prerequisite is now locally complete on Windows:
[Hydrate to RAM and Load definition](AIF120_WORKBENCH_CATALOG_FLOW_V1.md) preserve
the exact selected saved version, expose destination/roots, and explain unavailable
BIRTH or unsupported entries. Nine registered checks and seventeen window modes
pass, including the startup-abort fix.
[M3 evidence and closeout](AIF120_WORKBENCH_M3_V1.md) covers table controls,
record navigation, buffered memo editing and explicit native capability limits.
Buffered append/recall and buffered NULL representation remain engine follow-ups;
M3 refuses those operations while TABLE ON is active. M4 has not started.

## Baseline

The generated native Workbench is locally built and verified: shared command
execution, multiple/nested workspaces, native paths/defaults, Open/Load controls,
zero-based global areas, table/memo inspection, buffered scalar edits, and MINIDB
inspection, hydration, save, export and storage in memo fields. NEW activates the
new workspace; SWITCH selects its first open area or an unused area when empty.

Current behavior and limits: [Workbench guide](../../gui/uidef/WORKBENCH.md).
Latest implementation closeout: [Direct catalog workflow](AIF120_WORKBENCH_CATALOG_FLOW_V1.md).
Local verification does not imply committed, promoted or published work.

| Milestone | Deliverable | Status |
| --- | --- | --- |
| M1 | Native menus and modal workflow | Locally complete (Windows) |
| M2 | Workspace navigator | Locally complete (Windows) |
| M3 | Everyday table operations and editing | Planned |
| M4 | Relationships, indexes and storage views | Planned |
| M5 | Nested database editing round trip | Planned |
| M6 | Preferences and workspace-tree restoration | Planned |
| M7 | Reliability, portability and normal launch integration | Planned |

## M1 - Native menus and modal workflow

Deliver a native menu bar: File, Workspace, Table, View, Tools, Help. Keep common
buttons and the command box. Guide New, Open, Load and Save through modal forms
with an explicit destination workspace, native path defaults, applicable options,
validation, and clear completion/cancellation. Forms and menus belong in UIDEF;
system file/directory pickers remain host capabilities.

Done when:
- Generated menus, buttons and the command box invoke the same engine actions.
- Dialog ownership, results, focus return, Enter/Escape and cancellation work.
- Cancellation changes no workspace/table state; an invalid or stale target is
  explained without acting on a different target or submitting twice.
- Fixture workflows exercise empty/populated and parent/child workspaces, paths
  with spaces, native refusals and buffered edits where relevant.
- The built window is inspected and native/window checks pass with saved evidence.

Reuse the [modal and host-dialog work](AIF120_MODAL_AND_HOST_DIALOG_V1.md) and
[menu hierarchy](AIF120_MENU_NESTING_RULING_V1.md). Recheck their implementation
and open lifetime questions before extending them; do not invent a second model.

## M2 - Workspace navigator

Deliver a navigable tree of workspaces, children and tables, with context menus
and keyboard navigation. Show current workspace, selected table and owning
workspace distinctly; area numbers remain global and zero-based.

Done when:
- Browsing the tree and activating a workspace have clear, consistent behavior.
- Root, child, empty and peer workspaces work with duplicate table names.
- Filtering/refresh preserve valid selection; removed targets cannot receive actions.
- GUI state agrees with WORKDESK/GPS after commands, hydration, switching and close.

## M3 - Everyday table operations and editing

Deliver convenient filter, index/order, seek, record navigation, append, delete
and recall controls. Extend editing to ordinary memo text and explicit NULL where
the native field contract supports them; retain type, key and buffer constraints.
Carry forward the older Workbench's useful Record View layout and keyboard
navigation. Its original fields are read-only; editing must use the current
Workbench's typed-write and buffer controls. Reuse the command catalog's action
vocabulary, converting common prefill shortcuts into guided operations.

Done when:
- Controls and typed commands show the same records, order and cursor state.
- Pending edits are visible; Commit/Rollback affect the intended table.
- Edits are verified by field readback, including commit/reopen and rollback.
- Unsupported edits explain their limits; peers retain their data and buffers.

## M4 - Relationships, indexes and storage views

Deliver useful views of workspace-scoped relations, attached indexes/orders,
workspace roots, and RAM/disk residence. Let users inspect a relation chain and
follow it using the engine's actual traversal behavior.
Include a data dictionary browser for objects, fields, tags, attributes, evidence
and source links. Reuse the existing DDict catalog reader/resolver and its
canonical directory selection; author the new presentation through UIDEF.

Done when:
- Displayed definitions and active state come from the engine.
- DDict entries retain catalog/object identity and distinguish metadata from
  live table state. The older native app's feature inventory is checked against
  the generated view; missing information is explicit.
- Relationship traversal is checked by child field values, not just a drawn edge.
- Multiple workspaces with the same table names remain distinguishable.
- RAM tables and disk memo sidecars are described accurately; missing or inactive
  objects are visible rather than presented as working capabilities.

## M5 - Nested database editing round trip

Complete the guided flow: inspect an embedded MINIDB, hydrate it, edit its tables,
save a resulting image, and explicitly store that image into its containing field.
Keep its source table, record, field and containing image visible throughout.
Workspace children and nested image contents remain distinct concepts.

Done when:
- Root and nested image workflows reopen with the edited data intact.
- The destination reference is revalidated before storage; stale targets refuse.
- Commit/Rollback and existing shared memo references behave correctly.
- Unselected images, peer workspaces and source files remain unchanged unless
  they are the explicit destination of the operation.

## M6 - Preferences and workspace-tree restoration

Remember layout and useful preferences, and add full workspace-tree restoration.
Today a saved image includes child tables but restores them together into one
workspace; preserving that ownership hierarchy is unfinished work.

Done when:
- Restart restores chosen UI preferences and explains unavailable locations.
- A multi-workspace fixture reopens with its root/child ownership, table posture,
  workspace roots, current workspace and selected table mapped correctly.
- Imported/restored identities follow native rules; external catalog IDs are not
  mistaken for live session handles or reused without mapping.
- Missing members and partial failures are explicit. Pending edits/transactions
  have a stated resolve-or-cancel policy; no claim of silently resuming them.

## M7 - Reliability, portability and normal launch integration

Finish progress, cancellation, error presentation, shortcuts and contextual help.
Integrate the production Workbench with the normal build and chosen launch path.
Preserve the existing small wx/C++ and Python samples.

Done when:
- The normal build and launcher demonstrably run the intended fresh executable.
- Realistic workflows, repeated session lifetimes, failure recovery and regression
  checks pass, including non-default starting workspaces.
- Install/startup is checked outside the development directory.
- Each claimed release platform has actual build/runtime evidence. Windows proof
  alone is not Linux or macOS proof; unavailable platforms remain outstanding.
- Remaining limits, data locations and user-facing help are documented.

## Completion and reporting

Each milestone ends with working generated UI, engine behavior checks, actual
data/state assertions, visual inspection where applicable, regression evidence,
and a closeout. Record what changed, what passed, what remains, the executable
path and evidence links. Keep local completion separate from git/publication state.
Do not mark a milestone done from source presence or a screenshot alone.

Use these milestone names in progress and closeout messages. Split work within a
milestone into ordinary tasks, without inventing a second milestone numbering scheme.
The regression-harness isolation finding is a reliability dependency: coordinate
with its owner and reuse the fix/evidence instead of editing that lane in parallel.

## Planning update and good-neighbor record

WHAT_CHANGED: Created this milestone sequence; linked it from the Workbench guide
and registered it in the existing Workbench run. No executable or engine changes.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald,
steward member.ai.claude.cowork.
AUTHORIZATION: Owner accepted the outline and requested simple M1, M2, etc.
VERIFY_OR_UNDO: Check the relative links, milestone table and existing run's YAML
artifact paths. Undo only this document and its named guide/registry references.

Housekeeping inventory:
[planning inventory](evidence/AIF120_workbench_milestones_housekeeping_20260918.txt).
Documentation-only validation: link existence, ASCII, YAML and scoped diff checks.
No application tests rerun for this planning update. No new fixtures, dependencies,
environment settings, commits, staging, push or publication.

Comparison update, CODEX-20260918-UIDEF-COMPARISON:
WHAT_CHANGED: Added the catalog-flow prerequisite before M3, Record View reuse in
M3, DDict scope in M4, and the comparison link. Existing milestone status retained.
WHOSE_AREA: AIF-120; owner member.derald, steward member.ai.claude.cowork.
AUTHORIZATION: Owner requested the comparison and permitted the audit documents
and registry update in D:\code\ccode. This is a plan correction only.
VERIFY_OR_UNDO: See the comparison's source/UI evidence and its housekeeping
record; before-copy is build/uidef-comparison/before/docs/maintenance/
AIF120_WORKBENCH_MILESTONES_V1.md. Preserve all earlier milestone content.
