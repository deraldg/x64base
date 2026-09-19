# Existing and generated Workbench comparison

Owner: member.derald. Lane: AIF-120. Author: member.ai.codex.
Run: CODEX-20260918-UIDEF-COMPARISON. Date: 2026-09-18.
Authorization: owner requested the comparison before M3 and said begin.

## Scope and evidence

Compare the existing native DotTalk++ Workbench with the generated ArcticTalk
Workbench, preserving the existing C++/wx and Python frontends. This is an audit
and plan correction, not an implementation pass. No application source edits,
commits, branch changes, staging or publication are authorized by this pass.
The Python frontend is included in the source inventory, with runtime evidence
reported separately from native window inspection.

Inspect actual windows and their command handlers, trace shared services, and
record existing capabilities, gaps and reuse candidates. Do not equate a visible
menu with a verified working command, or a catalog definition with live tables.
Documents, evidence and the existing run registry are the only authored outputs.
Baseline hashes and dirty inventory are in build/uidef-comparison.

The original handoff's sample/product distinction did not replace a workflow
audit. This record supplies the missing comparison before further GUI expansion.

## Finding and recommendation

Continue the generated Workbench on its existing single-engine session, but use
the earlier Workbench as a feature and workflow reference. Preserve both older
frontends. Calling the older window a sample was not a sufficient evaluation of
the useful work already in it.

The immediate omission is a direct action on a saved catalog row. The older app
puts **Open in Workbench** beside the chosen snapshot and displays the command.
The generated app starts with catalog inspection, then requires an image-page
transition before RAM hydration. A saved definition has no corresponding direct
catalog-row load action. Address this flow before expanding M3.

This is an audit recommendation, not an implemented correction or a new owner
ruling. M3 remains planned. The existing M1/M2 proof records remain valid for
their stated scopes; they did not establish feature parity with the earlier app.

## What was actually inspected

- Launched the existing `dottalkpp/bin/dottalk_wb.exe`. Its title identifies
  `17f5deda`; current repository HEAD is
  `bbf22e7570f1d9a3c5a0286cdb3cd2333e7dacfe`. Source findings below describe the
  current files, not a claim that this older executable contains every change.
- Opened its Workspace menu and Memo workspaces window. Selected the superseded
  `wm_regress` row, live `mcc_v3` definition and live `mcc_db` MINIDB. Confirmed
  the enabled/disabled action and command previews. Did not execute their loads.
- Launched the existing `build/uidef-native/Release/arctictalk_workbench_m2.exe`.
  Inspected its Saved catalogs, Live session and Database images pages. The
  catalog default is the real WORKSPACES.dbf; the live session had zero tables.
- Reviewed both native implementations and the parallel Python frontend source.
  Python was not launched. No frontend was rebuilt and no engine regression suite
  was rerun for this document-only audit.

[Live UI observations](evidence/AIF120_workbench_comparison_ui_20260918.txt) are
the runtime evidence for this pass. Some mouse actions did not produce a verified
page transition. Keyboard navigation did work. In particular, the DDict page and
the generated definition-row refusal were not successfully exercised. They are
source-evidenced below, not runtime-proven. This is not a certification of every
menu operation, record edit, index or hydration path.

[Source/executable measurements](evidence/AIF120_workbench_comparison_sources_20260918.txt)
record SHA-256 identities and catalog counts. Existing M2 behavior proofs are
linked from [the M2 closeout](AIF120_WORKBENCH_M2_V1.md); this audit does not claim
to have repeated them.

## Comparison

| Workflow | Earlier native Workbench | Generated Workbench | Preserve or change |
| --- | --- | --- | --- |
| Saved catalog | List with format, size, saved time and superseded state; direct Open in Workbench | Searchable catalog, deleted-row exclusion, history toggle, identity/member/definition detail | Add a direct action appropriate to the selected payload; retain the newer exact snapshot identity |
| Saved definition | Preview `WORKSPACE LOAD mcc_v3 MEMO`; Open button enabled | File Load modal exists, but catalog-row action is Inspect image, which requires a valid MINIDB | Offer Load definition with explicit roots and destination; do not call a definition an embedded database |
| Saved MINIDB | Preview `WORKSPACE LOAD mcc_db MEMO RAM`; one Open button | Inspect image -> Database images -> choose image -> Hydrate in new workspace / under current workspace -> name | Put Hydrate to RAM beside the selected catalog row; retain the richer nested-image inspection as an optional step |
| Obsolete snapshots | Refuses superseded row because name-based loading would select a different live row | Inspection/hydration uses selected payload bytes | Preserve exact-row semantics; never silently substitute the latest row with the same name |
| Workspace navigation | Area list and text workspace graph | Root/child/table tree, search and explicit SWITCH/SELECT, zero-based global Area | Keep M2 navigation and native identities; do not copy the older display-ID convention |
| Directory/schema load | Directory options and schema file picker; two menu entries invoke the same schema loader | Generated Open/Load modals, native roots, explicit table/index directories and missing-table preflight | Retain new path/validation policy; expose useful index options only after checking native support |
| Records | Read-only Record View form, cursor navigation, command shortcuts | Browse grid, typed scalar edit modal, table Commit/Rollback and memo/image inspection | M3 should add the useful record form and guided operations; the old form is not an editor |
| Indexes | Dedicated container/tag/backend/direction grid and order/seek shortcuts | Some order state in table view; detailed index view still planned | Carry the information and interactions into M3/M4 using live engine state |
| Relations | Dedicated relation grid and text graph; unavailable match counts stay absent | Relationship exploration planned in M4 | Use actual engine traversal/counts; do not recreate matching rules in the UI |
| Data dictionary | Dedicated DDict browser with objects, fields, tags, attributes, evidence, relations and sources | No equivalent page in current generated layout | Add explicit DDict scope to M4 and reuse the catalog reader/resolver |
| Nested images | Memo browser describes a top-level container | Selected/nested image inspection, export, hydration and buffered store-to-memo workflows | Keep the newer image identity, provenance and round-trip direction |
| Command menus | Broad command catalog, with many prefill-only items | Smaller native menu system plus canonical engine command input | Reuse action vocabulary selectively, turning common prefill commands into modal workflows |
| Python frontend | Separate Tk frontend, six pages, corresponding command vocabulary | UIDEF remains the generated layout authority | Preserve Python; source inventory is not a runtime parity claim |

## Source anchors and reuse boundaries

All source paths are relative to D:\code\ccode. Line numbers were checked during
this pass and will move when implementation changes.

1. **Catalog action and identity guard:**
   `src/gui/wx/memo_browser_frame.cpp:133` reads/displays the selected payload;
   `:161` plans MEMO versus MEMO RAM and refuses superseded name-based loads;
   `:199` dispatches the action. The inspected MINIDB was mcc_db, saved ID 18,
   94,200 bytes, with 13 declared tables and 11 index containers. Those are the
   inspected container's values, not universal limits.
2. **Generated catalog gap:** `gui/uidef/author_workbench.py:65` builds the Saved
   catalogs page with Choose, Refresh, Inspect image and Open image file;
   `gui/uidef/wx_workbench.cpp:655` checks `saved.container.ok` before inspection.
   `:696` names the new workspace and submits the selected image payload for
   hydration. No direct catalog-definition load is wired in that action set.
3. **Native menus:** `src/gui/wx/main_frame.cpp:543` constructs fourteen top-level
   menus. `src/gui/core/gui_command_catalog.cpp:15` defines 112 action rows:
   66 run, 45 prefill, one informational. The nine Work-category rows are not
   appended as that category by the native menu builder. These counts are not
   counts of successful operations. `main_frame.cpp:970` distinguishes prefill
   from execution. The Python catalog has the same 112 category/label/command/
   kind tuples, measured by parsing both files.
4. **Record view:** `src/gui/wx/main_frame.cpp:1912` opens the form;
   `:2030` explicitly creates read-only fields. Its layout, field labels, memo
   wrapping and keyboard navigation are reuse candidates. Mutation belongs in
   the generated session's existing typed-write/buffer guards, not this form.
5. **Indexes and relations:** `src/gui/wx/main_frame.cpp:1404` and `:1441` render
   their grids. `src/gui/core/session.cpp:2682` records why GUI match-count
   recomputation was removed. Preserve unavailable values as unavailable until
   the canonical producer supplies them. `main_frame.cpp:2204` uses the text
   workspace graph formatter; it is not a substitute for M2's interactive tree.
6. **Data dictionary:** `src/gui/wx/main_frame.cpp:1473` uses
   `dottalk::datadict::find_catalog_dir()` and reads DDOBJECT, DDATTR, DDEDGE,
   DDEVID and DDSOURCE. Reuse these readers and object resolution, plus the useful
   detail relationships. Render through UIDEF. The current canonical-directory
   source is newer than the inspected native executable, so its deployed behavior
   was not established here.
7. **Session architecture:** `src/gui/core/session.cpp:1723` owns the older shell
   bridge. `src/gui/core/gui_shell_runtime.cpp:497` defaults to a persistent child
   process on Windows unless disabled; other platforms use the script bridge.
   This is not simply a fresh subprocess for every Windows command. GUI-owned
   tables and mirrored posture still create a second state boundary. In contrast,
   `gui/uidef/workbench_session.cpp:130` constructs the actual engine on its sole
   worker, binds canonical commands and captures results there. Keep that model.
   Do not link the engine into the old neutral GUI library contrary to its existing
   dependency ruling; adapt the new host's already-owned engine observations.
8. **Python inventory:** `tools/gui_preview/dottalk_gui_preview.py:142` constructs
   menus; `:466` maps six pages; `:522` starts schema loading. Its README describes
   pydottalk with a read-only DBF fallback. Its current layout has no matching
   native DDict or memo-workspace browser. No Python runtime claim is made.

Source cautions to review before borrowing handlers: the older directory opener
at `main_frame.cpp:810` assembles an unquoted directory argument and its default
"No indexes" choice does not emit NOINDEX; two schema-load menu entries share
the same loader. These are source observations, not newly reproduced engine bugs.
Do not import the old lifecycle/path search ladder into the new typed-root policy.

## Immediate flow correction, then the existing milestones

Before M3, add an operation beside each eligible catalog selection:

- **MINIDB:** Hydrate to RAM. Show source catalog and saved ID, destination name
  and parent/current workspace choice. Use that selected payload and reveal the
  resulting live tables when complete. Inspect image remains available separately.
- **DTSHEMA:** Load definition. Make external table/index roots explicit, reusing
  the existing preflight and destination checks. This reopens referenced data; it
  must not imply the definition contains table bytes or is a MINIDB.
- **BIRTH/empty/unsupported payload:** explain what is recorded and why loading
  is unavailable. A workspace catalog entry alone is not a saved database.
- Preserve cancellation, buffered-edit handling and stale-target checks. Never
  resolve a selected historical record by name to another record. Either use the
  exact selected payload or refuse with the reason.

Acceptance requires actual private-fixture readback: selected snapshot contents,
resulting workspace/table ownership, RAM residence for MINIDB, first selected
area, and cancellation preserving existing state. Exercise current and historical
rows, missing definition roots, duplicate names and a nested image. This pass
does not implement or execute those acceptance tests.

M3 then includes the older record-view benefit, guided order/seek/filter/record
operations, ordinary memo editing and explicit NULL where supported. M4 explicitly
includes DDict as well as index, relation and storage views. M5-M7 retain their
existing nested round-trip, restoration and release-integration responsibilities.
Keep native menus, common buttons and the command box; avoid reproducing every
older menu as an unguided command prefix.

## Filing, verification and good-neighbor record

Filed in the maintained [milestone plan](AIF120_WORKBENCH_MILESTONES_V1.md) and
`labtalk/registries/runs.d/AIPR-20260917-001.yaml`, under AIF-120. No new lane or
ruling number was allocated. This audit has mixed runtime/source evidence, not
a new implementation proof. Source/evidence remain local and uncommitted.

[Housekeeping and validation](evidence/AIF120_workbench_comparison_housekeeping_20260918.txt)
lists every current dirty path by ownership, protected hashes, exact audit output
paths and retained session/build residue. No application source edits, staging,
commit, branch change, promotion or publication occurred in this audit.

WHAT_CHANGED: Added this comparison and measured evidence, linked the audit from
the milestone plan, added the catalog-flow prerequisite and explicit Record View/
DDict scope, and registered the artifacts in the existing run fragment.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald,
steward member.ai.claude.cowork.
AUTHORIZATION: Owner said begin for the comparison, then explicitly permitted
D:\code\ccode access for this audit and its documents/registry. Implementation and
git mutation remain outside this pass.
VERIFY_OR_UNDO: Compare the milestone/registry files with their before-copies in
build/uidef-comparison/before; verify the listed source anchors, hashes, links and
UI observations. Revert only this pass's document/registry additions against those
copies, preserving earlier uncommitted work and all shared sources.
