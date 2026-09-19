# M2 - Workspace navigator

Owner: member.derald. Lane: AIF-120. Author: member.ai.codex.
Run: CODEX-20260918-UIDEF-M2. Date: 2026-09-18.
Authorization: owner said next after M1 and its file/schema-location corrections.

## Preflight

Replace the generated Live session's indented workspace list with a native tree
of workspace identities, nested workspaces and owned tables. Single click browses;
Enter or double-click explicitly SWITCHes a workspace or SELECTs a table's global
zero-based area. SELECT retains the engine's separate current-workspace cursor.
Search retains matching branches and ancestors, with stable selection and expansion
through refresh. Context menus use captured identities and refuse stale targets.

Targets: gui/uidef/author_workbench.py, wx_workbench.cpp,
workbench_navigation.cpp, workbench_session.hpp, workbench_session_test.cpp,
verify_workbench.py, WORKBENCH.md; the milestone plan, this closeout and owned
AI registry/evidence records. No shared engine behavior changes planned.

Proof: native snapshot tests and real generated window events for root, child,
grandchild, empty and peer workspaces, duplicate table names, search/refresh,
keyboard and context actions, stale identities and slot reuse. Existing native
and window workflows must continue to pass, including hydration and command
changes. Build a distinct arctictalk_workbench_m2.exe; preserve older previews.
Baseline source copies, hashes and full dirty inventory are in
build/uidef-native/m2-before. No git mutation or shared cleanup authorized.

## Delivered

The generated Live session now contains a native workspace/table tree and search.
The host projects the immutable WORKDESK snapshot; no shared CLI behavior changed.
Root, child, grandchild, peer and empty workspaces remain visible. Each table is
under its actual owner with its global zero-based area and optional RAM marker.
Current workspace and selected table have separate bold labels and explicit
markers. Single-click browses; Enter/double-click runs SWITCH or SELECT.
SELECT retains the independent current workspace. NEW, SWITCH and load flows
follow their destination; ordinary refresh preserves the browsed identity.

Right-click provides SWITCH/SELECT, New child, Close tables for the current
workspace, Expand/Collapse branch and Refresh as applicable. These use existing
host/worker actions. Close checks its captured current-workspace identity and
retains the existing nested-close setting. DEFAULT's New child action is disabled
until the existing durable-parent requirement is satisfied.

Search matches workspace/table names without changing the engine. Workspace
matches include their descendants; table matches keep their owner and ancestors.
Hidden selections return when search clears; unfiltered expansion survives search
and refresh. Closed targets are invalidated by stable handles, so area-number reuse
cannot redirect an old menu. Arrow navigation uses the native tree. Ctrl+F focuses
search; Escape clears it, Enter activates, and F5 refreshes.

## Verification

- Build and all nine registered checks passed. Native projection tests cover
  unordered descendants, empty roots, duplicate names, ancestor retention,
  case-insensitive search, unmatched queries and cycle bounds.
- All sixteen native window modes passed with successful process exits.
  Every completed window snapshot checks tree ownership, area labels, current
  workspace and selected table against the real engine, including command loads,
  nested MINIDB hydration, Open/Load, editing and image workflows.
- The navigator smoke completed 27 stages. It drives actual tree selection and
  activation events, Enter/Ctrl+F/Escape handlers and captured context-menu events;
  checks independent cursors, hidden selection restoration and collapsed branch
  refresh; closes a child while retaining its grandchild; refuses an old menu
  before and after reopening the area; and checks native WORKDESK/GPS readback.
- Existing M1 checks retain 23 modal lifetimes. Source catalog DBF/DTX hashes are
  unchanged across the full verification run.
- The first window run exposed a shutdown crash despite a PASS report. The
  verifier rejected the nonzero process exit. wxTreeCtrl destruction notifications
  could refresh already-destroyed sibling controls; shutdown now suppresses those
  callbacks. Three focused live-session lifetimes then passed and exited zero,
  followed by the full successful suite. No failed run was accepted as completion.
- The navigator and command-hydration captures were visually inspected. Tree
  indentation, empty/peer branches, duplicate table names, global areas, distinct
  current/selected labels, search and the scoped table view are visible.

Executable: D:\code\ccode\build\uidef-native\Release\arctictalk_workbench_m2.exe
SHA-256: afda8f778af8e35079f08ee08b8967188e9a314e4931929c69e50b99f9010c39

[Build and registered checks](evidence/AIF120_workbench_m2_build_20260918.txt).
[Native/window proof](evidence/AIF120_workbench_m2_20260918.txt).
[Navigator capture](evidence/AIF120_workbench_20260918_m2-navigation.png).
[Housekeeping inventory](evidence/AIF120_workbench_m2_housekeeping_20260918.txt).

Reproduce from D:\code\ccode using .venv312\Scripts\python.exe -B:
- gui\uidef\build_workbench.py --output-name arctictalk_workbench_m2
- gui\uidef\verify_workbench.py --output-name arctictalk_workbench_m2

Windows runtime proof only. M3-M7 remain planned: this does not restore a saved
workspace hierarchy, add the normal APPGUI launch integration, or claim Linux/macOS
runtime validation. M1/M2 focus checks briefly show real windows even without
captures. Current workspace changes follow the destination; refresh/search retain
valid browsing identities. Source and evidence remain uncommitted.

## Closeout and good-neighbor record

Filed under the existing owned AI Portal run and a dedicated proof fragment.
The full owned/shared dirty inventory and retained build/private-session residue
are measured in the linked housekeeping record. Existing VS/CMake/Python and
build/uidef-deps reused; no packages installed. PATH, VCPKG_ROOT and PYTHONUTF8
are process-local. Native tests require the existing dependencies and interactive
Windows desktop. Previous previews and shared dirty work are preserved.

WHAT_CHANGED: Generated workspace/table tree, snapshot search, stable selection,
context/keyboard actions, shutdown lifetime fix, native/window proofs and M2 records.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald,
steward member.ai.claude.cowork.
AUTHORIZATION: Owner requested milestones and said next after M1 corrections.
VERIFY_OR_UNDO: Use the commands above. Undo only this milestone's hunks and
named artifacts against build/uidef-native/m2-before, preserving earlier work.
No staging, commit, branch change, promotion, publication or lane closure.
