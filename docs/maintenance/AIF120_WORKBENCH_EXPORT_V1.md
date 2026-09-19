# AIF-120: export a selected database image

## Preflight - 2026-09-18

Authorization: owner's commissioned Workbench and explicit "keep going".
Baseline: development at b63606ec113edca7b7fc2986074b390cfb645817.
Coordination: CODEX-20260918-UIDEF-EXPORT; no other live session reported.
Targets: gui/uidef/workbench_images.*, workbench_session.*, wx_workbench.cpp,
author_workbench.py, workbench_images_test.cpp, verify_workbench.py and owned
documentation/evidence/registry. No shared engine implementation changes.

Add Export selected image to Database images. Write the inspected node's exact
MINIDB payload to a new standalone file, whether its source was a catalog,
file, live memo field or nested DTX object. Do not rebuild the image from the
current workspace. Share bounded, verified, no-overwrite file export with
the existing Save image path. Keep the image selection and live engine state.

Proof plan: export root and nested payloads, compare exact bytes, reopen and
hydrate an exported child in a fresh session, refuse malformed payloads and
existing/missing destinations, verify no engine/cursor/buffer changes, and
exercise the generated-window export action. Re-run the Workbench verifier
and compare source catalog and shared engine hashes. Preserve samples, APPGUI
and unrelated dirty files. No git mutations, cleanup or publishing.

## Delivered behavior

Database images now has Export selected image. It copies the inspected node's
exact bytes into a standalone MINIDB, including images discovered in live memo
fields. Selecting a child exports that child without its outer carrier; any
nested contents inside the selected image remain intact. Last export and Export
folder identify the destination. Full paths remain in the tooltip and transcript.

Export checks the payload's structure and 128 MiB limit, stages it privately,
copies without replacement, compares a bounded readback byte-for-byte and syncs
the destination. Save image shares this file-writing helper after its existing
native workspace snapshot and admission checks. Export never captures the
current workspace or commits pending edits.

Source pointers: gui/uidef/workbench_images.cpp:105 (verified file export),
workbench_session.cpp:273 (serialized action), wx_workbench.cpp:342 (UI action),
workbench_images_test.cpp:135 (export and preserved-state assertions).

The payload is the inspected snapshot, not a continuously refreshed source.
Reinspect to include later source changes. Export validation is structural;
hydration separately validates member paths and table posture. An I/O failure
can retain staging files or a partial destination and never reports success.
No cross-process transactional snapshot or replacement-write guarantee is added.

## Windows verification

Evidence: evidence/AIF120_workbench_export_20260918.txt and the v9 PNG family.
The generated design has 95 rows including its document row; validation reports
no findings. The active build compiled the generated native window.

- Six native programs and ten generated-window modes passed, including the
  existing scalar edit, save/reopen, memo image and close-during-read checks.
- Root exports retain the exact outer DBF/DTX payload and nested child bytes.
  Memo and file inputs also export without rewriting. Embedded binary data is
  compared exactly, not as a text preview.
- A peer table with an actual pending edit remains buffered, on record 2 and
  selected in its original workspace, after exporting a different image.
- Existing files with different payloads are preserved. Empty, plain-text and
  truncated payloads, empty filenames, existing directories and absent parent
  folders refuse without claiming a verified export.
- A fresh session opens the exported child as one RAM workspace and reads Ada
  and Grace. The surrounding carrier and unrelated pending edits are absent.
- The GUI test selects the nested node, invokes Export selected image, verifies
  the file bytes and unchanged selection, and retains no live tables/mounts.
  Visual review shows the selected child, readable destination and success state.
- Real-catalog hydration and source hash checks still pass. Shared cmd_area.cpp
  and cmd_workspace.cpp are unchanged by this phase.

The first native run caught a test setup error: stopping the first worker did
not destroy its session instance, so constructing another session was refused.
The test now ends that instance's scope before checking fresh-session restore.
No engine lifecycle implementation was changed for the test.

Source WORKSPACES.dbf SHA-256:
0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e.
Source WORKSPACES.dtx SHA-256:
152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
Tested executable SHA-256:
d73b87a20d05b7ba0626493326fdbbddb1816f451f16fed89519518c4feaeeaf.
Shared cmd_area.cpp SHA-256:
a055420cbf3714a98d6113e9c1ccf3463d88c12955c142be95335443ba4afa62.
Shared cmd_workspace.cpp SHA-256:
8e492fb90f518e4ba1c24e32be298b4d4a4b4cdfa6e12ad5db879b8ac2022eac.

## Good-neighbor note for maintainer transcription

WHAT_CHANGED: AIF-120 generated Workbench selected-image export, shared
verified export helper, native roundtrip proof and generated-window test.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald, steward
member.ai.claude.cowork. Shared engine implementation is unchanged this phase.
AUTHORIZATION: Owner's commissioned Workbench and explicit "keep going".
VERIFY_OR_UNDO: From D:\code\ccode run .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py. Undo only this export phase's named changes;
retain all earlier Workbench slices and unrelated dirty work.

## Housekeeping and boundaries

Whole-tree ownership and residue inventory:
evidence/AIF120_workbench_export_housekeeping_20260918.txt. Source/evidence are
uncommitted and source_defined. No staging, branches, publishing, dependency
installation, persistent environment changes or shared cleanup occurred.
The existing .pytest_cache access limitation is retained in the inventory.

Residue: generated design/C++ and native binaries under build/uidef-native,
export-build.log, export-test-build.log, export-native-test.log (initial test
setup failure), evidence/captures and private temporary catalogs, table copies,
staged image files, exports and sessions. Tests release their RAM mounts; disk
artifacts remain for review. The inventory enumerates phase temporary folders.
Clean clones require the uncommitted source and existing Windows dependencies.

This is local Windows verification, not a full CLI regression run. The scalar
editor still does not write memo images, and exported images do not preserve
the original workspace ownership tree. Samples and APPGUI remain unchanged.

Final inventory: 116 owned dirty paths across the Workbench slices, 7,160
shared dirty paths left untouched, no owned staging, and 25 retained phase
temporary directories. At handoff the updated interactive Workbench, process
45508, reported the expected window title and Responding=True. These are
measured handoff observations, not perpetual runtime claims. Coordination run
CODEX-20260918-UIDEF-EXPORT was checked out after verification.
