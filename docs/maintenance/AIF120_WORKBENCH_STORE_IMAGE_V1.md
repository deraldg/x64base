# AIF-120: store a database image in a live memo field

## Preflight - 2026-09-18

Authorization: owner's commissioned Workbench and explicit "good, keep going".
Baseline: development at b63606ec113edca7b7fc2986074b390cfb645817.
Coordination: CODEX-20260918-UIDEF-STOREIMAGE. No other live session reported.
Targets: gui/uidef/workbench_table.*, workbench_session.*, workbench_images.*,
wx_workbench.cpp, author_workbench.py, native tests, verifier, build wiring and
owned documentation/evidence/registry. No shared engine implementation changes.

Add Store image on a selected live row/memo field. Read a bounded MINIDB file,
validate its structure, allocate a new DTX object and buffer its reference via
the existing field-write funnel. Preserve the previous object so Rollback
restores the original row reference. Native Commit writes the chosen reference.
Use current area/handle/record/field checks and optimistic reference comparison;
refuse pending memo edits, deleted/NULL cells and active SQL transactions.
Other scalar buffers must survive. Support token and fixed x64 memo references.

Proof plan: exact binary payload readback, old-object preservation, rollback,
commit/close/reopen, disk and RAM tables, repeated edits, bad files and stale
targets, current cursor/workspace preservation, generated-window storage and
inspection, existing Workbench regressions and source-family hashes. Record
unreferenced allocated objects retained by rollback/failure as engine residue;
do not reclaim existing memo objects. Preserve samples, APPGUI and shared work.
No git mutations, cleanup, publication or lane closure.

## Delivered behavior

The Table page has Store image beside the existing edit and commit actions.
Select a row and memo field, choose a MINIDB file, then Commit table or Rollback
table. The file dialog identifies the table, record and field. As with scalar
edits, Commit/Rollback resolve all buffered changes in that selected table.
After commit, Inspect image opens the stored database with field provenance.

The worker validates current area, handle, record, field layout, buffer state,
SQL transaction state and field-write gate. The reference observed before the
file dialog is compared again before allocation. File input is bounded to
128 MiB with size/time consistency checks; this reader is also used by Open
image file. The MINIDB structure is checked before allocating anything.

A new DTX object is created, read back byte-for-byte and flushed. The new token
or fixed object ID is validated and passed to xbase::cli::replaceFieldStored
with TABLE buffering enabled. Buffer and unchanged committed-reference readback
must agree before success is reported. Existing memo objects are not updated
or tombstoned, preserving any shared references and the rollback target.

Source pointers: gui/uidef/workbench_table.cpp:83 (target validation), :119
(new object and reference buffering); workbench_images.cpp:105 (bounded file
read); workbench_session.cpp:273 (serialized action); wx_workbench.cpp:491
(Table dispatch), :864 (target/file dialog flow).

## Windows verification

Evidence: evidence/AIF120_workbench_store_image_20260918.txt and v10 PNG family.
The native build regenerated the design table: 96 rows including its document
row, no conformance findings. Seven native test programs and eleven generated
window modes passed. The new native test passed on its first run.

- Token and fixed x64 memo references both accept image files, including empty
  fields. Readback matches the original binary bytes. A fixed memo stores a
  valid image larger than 1 MiB containing embedded NUL bytes without truncation.
- Rollback restores the old reference. Commit followed by close/reopen reads
  the new image. Other fields/records sharing the old object retain its bytes.
- The selected cursor remains on record 2 while record 1 receives a buffered
  image. An existing scalar edit remains buffered and commits alongside it.
- Stale handle/name/reference, an actual intervening memo write, missing record,
  non-memo field, pending memo changes, pending record deletion, wrong selected
  area, SQL transaction, bad/truncated/empty file and absent/directory source
  paths refuse. Refusals before allocation leave the buffer/reference intact.
- The saved carrier contains the stored databases. A fresh session hydrates it
  into a RAM table with its disk DTX, reads the exact stored payload, writes and
  commits another image to that RAM table, then hydrates the first stored image
  as a child workspace. Its second NAME value is Grace.
- The GUI uses the Table action to buffer, roll back, buffer again, commit and
  inspect the stored payload. The capture shows SHELF / record 1 / IMAGE with
  the expected MINIDB member. The Table capture confirms Store image fits beside
  the existing controls.
- Existing command, table, scalar-edit, export, save/reopen, memo inspection,
  nested-image, real-catalog and close-during-read checks pass. The real catalog
  hydrates seven images into 97 areas; its DBF and DTX hashes are unchanged.

Source WORKSPACES.dbf SHA-256:
0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e.
Source WORKSPACES.dtx SHA-256:
152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
Tested executable SHA-256:
f5f811cecf97ef4ab9da46b3900064ec7444134be40e60516376dfb365a22c1a.
Shared cmd_area.cpp and cmd_workspace.cpp remain unchanged by this phase:
a055420cbf3714a98d6113e9c1ccf3463d88c12955c142be95335443ba4afa62 and
8e492fb90f518e4ba1c24e32be298b4d4a4b4cdfa6e12ad5db879b8ac2022eac.

## Limits and retained state

DTX only, using fixed x64 or 16-byte token memo fields. NULL, unsupported layout
and unavailable-backend refusal branches are source-checked; no new NULL/FPT
runtime fixture is claimed. The 128 MiB cap is enforced in source; no oversized
physical test file was created. File reads and reference comparison do not
establish a cross-process snapshot or hold a lock while the dialog is open.
This phase does not add crash-atomic DBF/DTX transaction semantics.

The reference is buffered, but memo allocation happens immediately. Rollback,
a failed post-allocation validation, or a later failed commit may leave live
unreferenced objects. These are deliberately retained. The existing nested
inspector follows live DTX objects, including such retained objects; it does not
infer DBF row reachability. No garbage collection or old-object erasure occurs.

Image validation here is structural; hydration retains separate path/posture
admission. The scalar editor still does not edit arbitrary memo text. Complete
workspace ownership-tree restoration and a full CLI regression run are not
claimed. Samples, APPGUI and shared engine implementation remain unchanged.

## Good-neighbor note for maintainer transcription

WHAT_CHANGED: AIF-120 generated Workbench Store image action, DTX reference
buffering, shared bounded image-file reader and native/GUI roundtrip proofs.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald, steward
member.ai.claude.cowork. No shared engine implementation changes this phase.
AUTHORIZATION: Owner's commissioned Workbench and explicit "good, keep going".
VERIFY_OR_UNDO: From D:\code\ccode run .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py. Undo only this phase's named changes; preserve
earlier Workbench slices and all unrelated dirty files.

## Housekeeping

Whole-tree inventory:
evidence/AIF120_workbench_store_image_housekeeping_20260918.txt. Source/evidence
remain uncommitted and source_defined. No staging, branch changes, publishing,
dependency installs, persistent environment changes or shared cleanup occurred.
The existing .pytest_cache access limitation is recorded in the inventory.

Residue includes generated design/C++ and binaries in build/uidef-native,
store-image-build.log, store-image-native-test.log, evidence/captures, and
private temporary fixture tables, DTX objects, carriers and session data.
Tests release their RAM mounts; private disk artifacts remain for review.
The inventory enumerates phase temporary directories. Clean clones require the
uncommitted source and the existing Windows toolchain/dependencies.

Final inventory measured 131 owned dirty paths across the Workbench slices,
7,157 shared dirty paths left untouched, no owned staging and 30 retained
phase temporary directories. The updated preview, process 49568, reported
ArcticTalk Workbench and Responding=True at handoff. Coordination run
CODEX-20260918-UIDEF-STOREIMAGE was checked out after verification.

Concurrent repository activity: HEAD advanced to
bbf22e7570f1d9a3c5a0286cdb3cd2333e7dacfe during closeout. That DDict commit
contains src/datadict/ddict_catalog_paths.cpp, src/tests/CMakeLists.txt,
src/tests/test_ddict_catalog_dir.cpp and labtalk/ai_portal/TIER0_STATE.md.
The three source/test paths were already dirty before this phase and are now
committed; their last-write times predate this build. This phase did not edit,
stage or commit them. This accounts for the shared inventory falling by three
from the previous phase, without cleanup by this run.
