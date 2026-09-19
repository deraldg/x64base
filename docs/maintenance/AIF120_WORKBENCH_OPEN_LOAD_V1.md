# AIF-120 Workbench Open and Load controls

Run: CODEX-20260918-UIDEF-OPENLOAD. Status: locally verified, uncommitted.
Authorization: owner explicitly requested Open (WORKSPACE OPEN dbf) and Load
(WORKSPACE LOAD .dtschema) buttons alongside New workspace.

Preflight: gui/uidef/author_workbench.py, wx_workbench.cpp, workbench_session.hpp,
workbench_session.cpp, workbench_paths_test.cpp, verify_workbench.py and local
documentation/registry. Open invokes the native OPEN dbf in the current workspace.
Load chooses a .dtschema/.dtschemas file starting at WORKSPACES and calls the same
native LOAD dispatcher; full paths with spaces remain intact. Both publish actual
new table counts and reveal Tables. Preserve native paths, current workspace,
engine load/refusal/index semantics, other open workspaces and Open table copy.
Use a second toolbar row to keep the workspace actions together at smaller widths.

Proof plan: native fixture commands/actions with peer workspaces, real row readback,
schema filenames containing spaces, missing files and incomplete-posture refusal;
generated window button dispatch and layout capture; existing Workbench suite.
Use only fixture data for writes. Build a separately named preview to preserve
the running session. No cmd_area changes, source catalog writes,
staging, branch change, commit, push, publication or shared cleanup.

Owner steering: use the actual zero-based area number in the table list. Replace
Select command, Area ID and Local slot with a single Area column and remove the
internal identity from the current-table header. Keep stable handles internally
for stale-selection checks. The existing navigation smoke verifies numeric cells
and selection of filtered child/peer rows. Menus were discussed as a planned
native cross-platform menu bar plus toolbar and command box; no menu bar is
implemented by this slice.

Window verification exposed missing button names in generated wx output. Extend
gui/uidef/uidef_wx.py to assign a button's OBJID as its native window name, without
changing dispatch scope. This makes button lookup and actual activation tests
possible. Tooltips tolerate absent controls; the smoke requires both buttons and
exercises their generated click handlers.

The owner's supplied WORKDESK/GPS trace confirms global engine numbering:
DEFAULT opens areas 0..12 and ws2 opens 13..55; SWITCH ws2 leaves selected area 0
owned by DEFAULT. The grid uses engine_slot, never a stable identity or a per-
workspace ordinal. Current workspace and selected area's owner stay distinct in
the header. No extra SWITCH/SELECT is introduced by presentation changes.

Subsequent owner ruling: GPS is correct but navigation lacks flow. WORKSPACE NEW
must activate the new workspace; SWITCH must select its first open table. The
owner explicitly agreed that an empty workspace targets an unused area with no
table open. Added preflight: src/cli/cmd_workspace.cpp, shared by the prompt and
Workbench. Choose the lowest open member slot, or lowest unused engine slot when
empty; do not change membership or renumber areas. Refuse an empty destination
when all engine slots are occupied, before birth or cursor/path mutation. Explicit
SELECT remains independent. Tests cover NEW/NEW UNDER, populated/empty SWITCH,
failed transitions, GPS, later OPEN, roots and surviving peer identities.

Next-pass owner direction (2026-09-18): support modal workflow. Plan task-focused
New/Open/Load/Save dialogs with explicit destination workspace, validation, and
Apply/Cancel, sharing the native actions. This is queued work, not implemented or
verified by this slice. The native menu bar remains planned too.

## Good-neighbor note for maintainer transcription

WHAT_CHANGED: AIF-120 generated Open/Load buttons, two-row toolbar, numeric Area
column, stable generated button names, native action wrappers and fixture/window
proofs; native WORKSPACE NEW/SWITCH cursor flow. Save test now identifies orphan
slots if its health assertion fails. Workbench session startup/teardown resets
the compatibility area cache so engine address reuse cannot retain old pointers.
WHOSE_AREA: AIF-120 GUI and AIF-078 workspace command lane; owner member.derald,
steward member.ai.claude.cowork.
AUTHORIZATION: Explicit owner button request and correction of visible area
numbers and explicit NEW/SWITCH flow ruling, under the commissioned Workbench
work. No engine numbering change.
VERIFY_OR_UNDO: From D:\code\ccode run .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py --output-name arctictalk_workbench_openload.
Undo only this slice's named hunks, retaining earlier same-file Workbench work.

## Findings while verifying

Initial Open fixture reused a file already open elsewhere and incorrectly
expected a new area. The revised fixture opens distinct files and checks that
peer identities survive. Initial Load assertion incorrectly expected SET PATH
to change; native cmd_workspace.cpp:2627 explicitly makes posture roots local to
the load. The final assertion checks unchanged SET PATH plus actual data opened
from the posture's different root. Neither mismatch required an engine change.

An initial uidef_save_test run intermittently failed its healthy-desk assertion
after restoring two tables. Added diagnostics identified many unrelated orphan
slots on recurrence (openload-capacity-build.log). WorkAreaSet caches DbArea
pointers using only the engine address; sequential Workbench sessions can reuse
that address while allocating different areas. Added preflight within the owned
workbench_session.cpp: reset the compatibility cache after binding each new
engine and after unbinding it, before destroying the engine. This addresses the
host lifecycle, without changing GPS or the shared workareas header. Verify with
repeated save/reopen runs plus the full Workbench suite. Original failed output
remains in openload-build.log and openload-capacity-build.log.

The first console capacity fixture hit the Windows disk-file limit at 508 open
DBFs (errno=24). Four areas remained unused, so the test's expectation that
empty SWITCH must refuse was wrong. The console test now reproduces the owner's
56-table sequence plus normal refusals; the native session test fills the engine
with RAM tables for the actual all-areas-occupied boundary. The disk-file limit
is a separate observed constraint, unchanged here. Original evidence is retained
under the reported workbench-flow-xdhtcnps temporary directory.

## Final verification and handoff

- Eight native programs and fifteen window modes passed on the final executable.
  Actual source catalog inspection privately hydrated seven images / 97 tables.
- The console reproduction opens areas 0..12 and 13..55, confirms NEW enters an
  empty workspace at area 13, and SWITCH returns to the destination's first table.
  An empty ws3 selects unused area 56. Failed NEW/SWITCH preserve both cursors and
  roots. Run gui/uidef/verify_workspace_flow.py to repeat with isolated fixture copies.
- Native RAM hydration filled all 512 areas; empty NEW/SWITCH refused without a
  birth, cursor, membership or path change. Twelve repeated complete save/reopen
  runs passed after the compatibility cache reset, followed by the full suite.
- Actual Open/Load button dispatch and the four-column table list passed. The
  1000x850 capture was visually reviewed: both buttons fit beside New workspace,
  and the Area column shows 0 and 1. Source WORKSPACES.dbf/.dtx hashes are unchanged.
- Final diff whitespace check and new text ASCII check passed. Owned YAML parses;
  every registered artifact exists. Shared-tree inventory: 206 owned dirty paths
  (including prior Workbench slices), 7158 shared paths left untouched, zero owned
  staged paths. 216 phase fixture/session directories retained and individually
  listed; no cleanup or source data writes.

Proof: docs/maintenance/evidence/AIF120_workbench_openload_20260918.txt.
Inventory: docs/maintenance/evidence/AIF120_workbench_openload_housekeeping_20260918.txt.
Capture: docs/maintenance/evidence/AIF120_workbench_20260918_v14-openload.png.

Opened the new interactive preview on this host from
build/uidef-native/Release/arctictalk_workbench_openload.exe (PID 53004 at launch).
SHA-256: c73ebd74364f453b3fd53a63b7eb9bdf8f78f3faf05aaa2d1e4c68a523603f35.
The console was rebuilt at build/uidef-native/src/Release/dottalkpp.exe and verified
from an isolated copy; no staging to dottalkpp/bin or APPGUI launcher change.
Prior preview executables are preserved. Dependencies and build PATH/VCPKG_ROOT
settings are local; a fresh clone also needs the uncommitted sources/evidence and
the installed Windows toolchain/dependencies. No commit, push or publication.
