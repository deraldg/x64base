# AIF-120: workspace-scoped table navigation

## Preflight - 2026-09-18

Authorization: owner's commissioned Workbench and explicit continuation.
Baseline: development at bbf22e7570f1d9a3c5a0286cdb3cd2333e7dacfe.
Coordination: CODEX-20260918-UIDEF-NAV. No other live session reported.
Targets: gui/uidef/author_workbench.py, wx_workbench.cpp, workbench_session.hpp,
new snapshot navigation helper, existing native session test, CMake wiring,
verifier and owned documentation/evidence/registry. No shared engine changes.

The global area list becomes a Tables browser scoped to the highlighted
workspace, with independent Include nested and All workspaces controls and a
table/workspace name filter. Each row shows its exact SELECT command. Use
visible-row mapping and stable area handles so filtering cannot redirect an
action to a different table. Preserve highlighted area across view changes.
Single-clicking a workspace only browses; double-click uses native SWITCH.
Double-clicking a table uses native SELECT. Typed SWITCH follows its workspace.

Proof plan: native snapshots with same-name tables in parent/child/peer
workspaces, scoped and all-workspace queries, missing/stale views, filtering
without engine mutation, and generated-window SELECT from a filtered row
while another workspace remains current. Check nested-view controls are
independent of the engine's save/close recursion switch. Re-run the Workbench
verifier, inspect window captures, verify source hashes and inventory shared
dirty paths. Preserve samples, APPGUI and all prior Workbench slices.

## Delivered

Live session now has a Tables browser scoped to the highlighted workspace.
Include nested shows descendant tables; All workspaces searches the entire
session. Search matches table or workspace names without case sensitivity and
trims surrounding whitespace. Rows distinguish the exact SELECT command,
stable area ID and workspace-local slot. Duplicate table names remain separate.

Single-clicking a workspace browses its tables without changing the engine.
Double-clicking a workspace sends SWITCH. Double-clicking a table sends SELECT
using its visible-row mapping and stable area handle. A successful workspace
change follows that workspace in the browser. The current workspace and the
selected table's owner remain separately visible, as the engine permits.

The generated layout remains authored in author_workbench.py. Its design table
has 106 rows including the document row, with no conformance findings. The
new workbench_navigation.cpp projects immutable session snapshots; it issues
no engine commands. View nesting does not change save/close recursion. Hidden
row highlights survive filtering; removed area identities are discarded.

## Windows verification

Evidence: evidence/AIF120_workbench_navigation_20260918.txt and the v11 PNG
family. Seven native test programs and twelve generated-window modes passed
(eleven captures and close-during-read). Existing command, table, buffered
editing, image save/export/store and hydration checks remain passing.

- Native parent, child and peer workspaces contain same-name tables. Checks
  cover parent-only and descendant scope, query scope boundaries, case and
  whitespace, all-workspace name matching, empty and missing workspaces, and
  original snapshot indices after filtering. Observing the engine afterwards
  confirms browsing changed neither current workspace nor selected area.
- A synthetic, deliberately unordered grandchild snapshot verifies transitive
  descendant traversal. This is a projection test, not a new native grandchild
  lifecycle proof. The helper's visited set also bounds traversal on cycles.
- The native window creates NavParent, NavChild and NavPeer and opens identical
  205-row PEOPLE tables in each. With engine recursion off, Include nested
  still shows parent and child. Search hides earlier rows, and activation of
  the remaining child row selects the child area while NavPeer stays current.
  All-workspace peer search selects the peer, and workspace double-click then
  switches to NavChild without silently changing SELECT.
- Restoring a previously hidden row restores its highlight. The final capture
  browses NavParent and NavChild while current workspace is NavChild and the
  selected table belongs to NavPeer. The header and scope label show these
  separate states. All six columns and the Live-session footer are visible.
- Visual review caught the smoke test changing the MAIN page without its
  normal page-change event, leaving catalog counts in the footer. The test
  now fires that event and asserts the Live-session footer before capture.
  Rebuild and the full verifier passed after that correction.
- Real-catalog inspection reports 134 retained records, 148 deleted records,
  seven images and no payload errors. Native hydration opens those seven
  images into 97 areas. Input hashes are unchanged.

Source WORKSPACES.dbf SHA-256:
0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e.
Source WORKSPACES.dtx SHA-256:
152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
Tested executable SHA-256:
8c7862430427c8c0ad8bac0f7cd5b1901d49ed5baafdd7a2800e80a87382dbd2.
Shared cmd_area.cpp and cmd_workspace.cpp remain unchanged by this phase:
a055420cbf3714a98d6113e9c1ccf3463d88c12955c142be95335443ba4afa62 and
8e492fb90f518e4ba1c24e32be298b4d4a4b4cdfa6e12ad5db879b8ac2022eac.

## Boundaries

Name search uses byte-oriented case folding; full Unicode case folding is not
claimed. Filtering projects the latest serialized session snapshot. The native
action still validates area identity before SELECT. Search covers names, not
table contents. No full CLI regression run or large-workspace performance
benchmark is claimed. Existing image/storage limits remain as documented in
WORKBENCH.md and prior closeouts. Samples and APPGUI remain unchanged.

## Good-neighbor note for maintainer transcription

WHAT_CHANGED: AIF-120 generated Workbench Tables navigation with workspace and
descendant scope, name search, explicit SELECT commands and filtered-row proofs.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald, steward
member.ai.claude.cowork. No shared engine implementation changes this phase.
AUTHORIZATION: Owner's commissioned Workbench and explicit "good work, continue".
VERIFY_OR_UNDO: From D:\code\ccode run .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py. Undo only this phase's named changes; preserve
earlier Workbench slices and all unrelated dirty files.

## Housekeeping

Whole-tree inventory:
evidence/AIF120_workbench_navigation_housekeeping_20260918.txt. Source and
evidence remain uncommitted and source_defined. No staging, branch changes,
publishing, dependency installs, persistent environment changes or shared
cleanup occurred. The inventory records any Git traversal warnings.

Residue includes generated design/C++ and binaries in build/uidef-native,
navigation-build.log, navigation-native-test.log, evidence/captures and private
temporary fixture tables, memo objects, saved images and session data. Tests
release their RAM mounts; private disk artifacts remain for review. The updated
preview has its own session. Clean clones need the uncommitted files and the
existing Windows toolchain/dependencies.

Final inventory measured 147 owned dirty paths across the Workbench slices,
7,157 shared dirty paths left untouched, no owned staging and 56 retained
phase temporary directories. Git could not traverse the existing .pytest_cache
folder; the inventory records that warning. Branch development and HEAD
bbf22e7570f1d9a3c5a0286cdb3cd2333e7dacfe are unchanged from phase preflight.
The updated preview, process 44384, reported ArcticTalk Workbench and
Responding=True at handoff. Coordination run CODEX-20260918-UIDEF-NAV was
checked out after verification.
