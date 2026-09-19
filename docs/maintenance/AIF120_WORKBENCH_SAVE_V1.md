# AIF-120: portable MINIDB save and reopen in the Workbench

## Preflight - 2026-09-18

Authorization: the owner's Workbench commissioning and explicit continuation.
Coordination: CODEX-20260918-UIDEF-SAVE. Baseline: development at
b63606ec113edca7b7fc2986074b390cfb645817.

Targets: gui/uidef session service, generated document, wx host, native tests,
verifier and owned documentation/registry; src/cli/cmd_workspace.cpp for the
MINIDB collector. cmd_area.cpp and existing samples remain unchanged.

Measured source finding: the save posture uses SaveScope, but
build_minidb_container enumerates every open area and flattens file paths.
The posture can therefore name copy-1/TABLE.dbf while the carrier contains
TABLE.dbf, and peers with the same basename collide. Fix this in the shared
save implementation, preserving the MINIDB 1 format and ordinary flat names
where unambiguous. Failed member reads must refuse before superseding history.

Deliver Save image for the current workspace's committed working set and Open
image for inspection/hydration into a new workspace. Preserve native recursion
scope. Pending edits in that scope and active SQL transactions must refuse.
Export to a new destination only; reopen is explicit, with fresh identities.
This is a database image, not a serialized multi-workspace ownership tree.

Proof plan: private tables with peer and child workspaces, duplicate basenames,
DTX memo carriage, committed edits, pending edit refusal, existing destination
protection, fresh-session restore and RAM resave. Native generated-window
verification plus source catalog hashes. No staging, publishing or cleanup of
unrelated shared work. Source/evidence remain uncommitted and source_defined.

## Delivered behavior

Live session has Save image and Open image file. Saved catalogs also has Open
image file. Save takes the current workspace, honoring recursion, independently
of the selected area. It checks the workspace handle, rejects buffered changes
in scope and active SQL transactions, invokes WORKSPACE SAVE MEMO MINIDB into
the private catalog, and validates the container and table count. Exported bytes
are read back and synced before reporting success. The final copy refuses an
existing destination. Open reads at most 128 MiB on the worker, checks size and
mtime, and invokes the existing nested inspector and native hydration path.

The shared engine collector now uses SaveScope for its files as well as its
posture. It deduplicates repeated physical files, gives basename collisions
per-area paths, and rewrites AREA paths to the exact carried members. Ordinary
unambiguous names remain flat; MINIDB 1 is unchanged. Memos follow their table's
directory. Missing member reads and failed memo flushes refuse. Construction
precedes superseding the old catalog row. This also fixes the regular prompt.

Source: src/cli/cmd_workspace.cpp:3246 (collector), :3844 (construction before
supersession); gui/uidef/workbench_session.cpp:274 (save), :560 (file admission).

## Measured Windows results

Evidence: evidence/AIF120_workbench_save_20260918.txt, the v7 PNG family and
evidence/AIF120_workbench_save_extra_20260918.txt. The save screenshot was
visually reviewed: original and restored workspaces are visible, and the
restored table displays Saved from Workbench with zero buffered records.

- Five native test programs passed. Save tests prove parent-only and recursive
  scope, peer byte exclusion, duplicate table/memo basenames, committed values,
  memo readback, active-index SEEK, independent SELECT/SWITCH state, pending,
  SQL and stale-request refusal, and protection of an existing export file.
- The originating session is destroyed before a fresh session opens the image.
  Parent and child values reopen independently. That RAM working set is saved
  again and opened in a third session with both values and memos intact.
- A native save establishes a snapshot. Renaming its private active index
  makes the next save fail. Readback proves unchanged catalog row count, IDs,
  superseded flags and payloads. The fixture index is restored afterward.
- Resaving a hydrated outer image preserves the exact nested live MINIDB bytes
  inside its carried DTX. Existing hydration, failure recovery, scoped close,
  mount release and unchanged-source checks still pass.
- Eight generated-window modes passed: catalog, live commands, browse, edit,
  save/open, image, nested image and close during read. Save/open uses the real
  handlers after supplying its private filename; file-picker interaction is
  not automated. It edits, exports, opens, hydrates and browses the saved value.
- The real catalog measured 134 retained rows, 148 deleted, seven MINIDBs and
  zero payload errors. Seven images hydrated into 97 simultaneous open areas.
- The regular dottalkpp executable was rebuilt. The full CLI regression suite
  was not rerun; the shared command is exercised by the native tests above.

SHA-256 measurements:

- Source WORKSPACES.dbf, unchanged:
  0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e.
- Source WORKSPACES.dtx, unchanged:
  152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
- Tested generated executable:
  b00f6f86a21fc07bc8e3ccc1664d55e2aadb7683ad53e2b7fefec34b61341cdd.
- src/cli/cmd_area.cpp, unchanged:
  a055420cbf3714a98d6113e9c1ccf3463d88c12955c142be95335443ba4afa62.
- src/cli/cmd_workspace.cpp before this phase (previously clean):
  7c38c2c98fba1020d4c35960c9cca1945d02f2c5cb3778b6a8621dc2a2b0a302.
- src/cli/cmd_workspace.cpp after this phase:
  8e492fb90f518e4ba1c24e32be298b4d4a4b4cdfa6e12ad5db879b8ac2022eac.

## Limits and residue

Image restore places included child tables in one new workspace; it does not
reconstruct the ownership tree, command history or buffers. This is committed
database-image persistence, not an atomic snapshot across external writers.
There is no new cross-file crash-atomicity guarantee for the native catalog/memo
pair. Existing image admission and private catalog inspection limits apply.

An export failure can leave a private native snapshot, staged image or partial
destination. Failure is reported and the destination is not claimed verified.
Private snapshot history grows within the existing inspector limits.

The first build caught an overwidth design-table object ID; it was shortened
and regenerated. An initial negative-input test expected a tree-level error;
invalid container syntax is reported on its image node. The corrected test
checks the node's failed scan. Final verification passed.

## Good-neighbor note for maintainer transcription

WHAT_CHANGED: Scoped MINIDB carriage and portable member paths in
src/cli/cmd_workspace.cpp, with duplicate basename handling and construction
before history supersession; generated Workbench save/open and native tests.
WHOSE_AREA: AIF-120 / project.x64base.gui; shared WORKSPACE command also used by
AIF-078. Owner member.derald; steward member.ai.claude.cowork.
AUTHORIZATION: Owner commissioned Workbench development and repeated continuation.
VERIFY_OR_UNDO: From D:\code\ccode run .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py. Inspect git diff -- src/cli/cmd_workspace.cpp;
undo only this phase's named hunks, preserving earlier slices and shared work.

## Housekeeping

evidence/AIF120_workbench_save_housekeeping_20260918.txt labels all owned
Workbench paths and shared dirty paths left untouched. Source and evidence are
uncommitted; no staging, branch change, push, publication, lane closure or proof
promotion occurred. Git could not read the pre-existing .pytest_cache directory;
the inventory records this limitation. No unrelated files were cleaned.

Residue includes build/uidef-native binaries, generated design DBF/FPT/C++,
save-build.log, save-extra-build.log, save-first-test.log, save-index-test.log,
save-nested-test.log, the v7 evidence images and private temporary sessions,
fixtures, catalogs and images. Phase temp directories are listed in the
housekeeping evidence. Tests release RAM mounts; disk residue is retained.

No dependencies were installed and no persistent environment settings changed.
The build uses existing Windows VS/CMake, .venv312 and build/uidef-deps.
Clean clones require those dependencies and the currently uncommitted source.

The final inventory measured 90 owned paths and 7,160 shared dirty paths left
untouched. The coordination run was checked out. An updated interactive preview
was launched as PID 30344 for handoff; this is a launch observation, not a
promise that the process remains running after handoff.
