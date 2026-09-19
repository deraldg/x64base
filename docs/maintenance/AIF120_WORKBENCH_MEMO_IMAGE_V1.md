# AIF-120: open a database image from a live memo field

## Preflight - 2026-09-18

Authorization: the commissioned Workbench and owner's explicit continuation.
Baseline: development at b63606ec113edca7b7fc2986074b390cfb645817.
Coordination: CODEX-20260918-UIDEF-MEMOIMAGE. No other live run reported.
Targets: gui/uidef/workbench_table.*, workbench_session.*, wx_workbench.cpp,
author_workbench.py, native tests, verifier and owned documentation/registry.
No shared engine implementation change is planned.

The Table page can inspect scalar/memo values, but a memo carrying MINIDB bytes
currently appears as a binary preview. Add Inspect image for the selected row
and memo field, using the existing backend reference resolution and nested
image inspector on the serialized worker. Preserve current record and live
selection. Carry precise source provenance into inspection and hydration.
Keep ordinary value-preview limits; image reads get the existing 128 MiB image
budget. Refuse non-memo, missing, invalid and stale selections explicitly.

Proof: native memo-reference and image tests, cursor/selection preservation,
buffered payload handling, wrong type/non-image/stale/cancel refusal, both disk
and RAM source tables, and generated-window field-to-image-to-hydration flow.
Run the existing Workbench verifier and check source catalog hashes. Preserve
samples, APPGUI, cmd_area.cpp, previous Workbench slices and shared dirty work.
No git mutations, cleanup, publishing, proof promotion or lane closure.

## Delivered behavior

Table has Inspect image beside Open value. Select a row and memo field to read
its committed MINIDB payload, inspect nested images, and use the existing
hydration actions. The source table, record and field appear together in a
separate Memo field row; the complete source path is also available as a tooltip.
Hydration retains the full field provenance. It does not replace the source.

The serialized worker checks area handle, record, field name/type and buffer
state, preserves the cursor, and resolves either legacy memo tokens or fixed
x64 object IDs through the existing memo backend. Ordinary memo previews and
image reads share this reference resolver. Its stat-before-read cap remains
1 MiB for previews and is 128 MiB for explicit image inspection. Returned bytes
must match the reported logical length. The nested inspector retains its
existing depth, node and aggregate byte limits.

Pending changes to the selected memo refuse image inspection. Resolve them
through Commit/Rollback before inspecting. Empty, missing/deleted, non-image,
wrong-type and stale selections report reasons. Malformed MINIDB containers
display their scanner error and cannot hydrate. Cancellation is checked before
reading and again by nested inspection. A running backend read is not forcibly
interrupted.

Source: gui/uidef/workbench_table.cpp:57 (shared memo reader), :82 (committed
field read); gui/uidef/workbench_session.cpp:587 (image dispatch);
gui/uidef/wx_workbench.cpp:441 (Table action).

## Windows verification

Evidence: evidence/AIF120_workbench_memo_image_20260918.txt and the v8 PNG family.

- Six native test programs passed, including the new memo-image test. Legacy
  tokens and fixed 8-byte x64 references resolve byte-exact image payloads.
- Reads of record 1 leave current record 2 unchanged. Reading a source area
  while a peer workspace is selected preserves both selected area and workspace.
- Plain text, empty/tombstoned/malformed objects, wrong field type, stale field,
  stale handle, missing record and pre-cancelled requests exercise refusal paths.
- A valid image larger than 1 MiB is read without truncation; ordinary Open value
  still refuses that object under its smaller preview budget.
- Buffered legacy and fixed memo changes refuse. After rollback both original
  image references resolve again. The command engine may allocate a new memo
  object before buffering its row reference; this action does not reclaim those
  private sidecar objects or change the engine's rollback implementation.
- Field payloads hydrate through the native engine. A separate test reads the
  image field of a RAM DBF with a disk DTX, then hydrates its nested database.
- Nine generated-window modes passed. The new mode creates a named workspace,
  opens a private catalog copy as a live table, selects record 1/SNAPSHOT,
  invokes the Table action, selects its nested image, hydrates it as a child,
  and verifies Ada in the resulting two-record table. Source provenance remains
  attached throughout. The screenshot shows the nested image and source field.
- Existing command, scalar edit, save/reopen, catalog, nested-image and
  close-during-read checks pass. The real catalog still hydrates seven images
  into 97 open areas and reports 134 retained rows, 148 deleted, zero payload
  errors. The source catalog family is unchanged.

Source WORKSPACES.dbf SHA-256:
0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e.
Source WORKSPACES.dtx SHA-256:
152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
Final tested executable SHA-256:
e530e1e8df82fd7e25ae3c3c3393adbabbf820d85b4e6429f7079b179316f97e.
cmd_area.cpp and cmd_workspace.cpp were not changed by this phase; their hashes
remain a055420cbf3714a98d6113e9c1ccf3463d88c12955c142be95335443ba4afa62 and
8e492fb90f518e4ba1c24e32be298b4d4a4b4cdfa6e12ad5db879b8ac2022eac respectively.

The first native test exited successfully but its proof marker was captured
inside the still-running session's output sink. It now shuts down before
printing, and the verifier requires that explicit marker as well as exit zero.
Visual review also prompted the separate Memo field row; the initial long path
had clipped the record and field details.

## Good-neighbor note for maintainer transcription

WHAT_CHANGED: gui/uidef live memo image reader, generated Table action, visible
source field, native proof and generated-window field-to-child hydration test.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald, steward
member.ai.claude.cowork. Shared engine implementation is unchanged this phase.
AUTHORIZATION: Owner's commissioned Workbench and explicit continuation.
VERIFY_OR_UNDO: From D:\code\ccode run .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py. Undo only the named memo-image phase's changes;
retain earlier Workbench slices and all unrelated dirty work.

## Housekeeping and boundaries

The whole-tree inventory is
evidence/AIF120_workbench_memo_image_housekeeping_20260918.txt. It labels all
owned paths and shared dirty paths left untouched. Source/evidence remain
uncommitted and source_defined. No staging, branches, publishing, dependency
installation, persistent environment changes or shared cleanup occurred.
The existing .pytest_cache access limitation is recorded in the inventory.

Residue includes generated build files/binaries, memo-image-build.log,
memo-image-test-build.log, memo-image-final-build.log, memo-image-first-test.log,
evidence images and private temporary DBFs, DTXs, catalogs, exports and sessions.
Phase temporary directories are enumerated in the inventory. Tests release
their RAM mounts; private disk artifacts are retained. Clean clones require the
uncommitted source and the existing Windows toolchain/dependency setup.

This phase was tested on Windows with DTX. It does not claim FPT/DBT nested
expansion, memo editing through the scalar dialog, new cross-process snapshot
atomicity, a full CLI regression run or workspace ownership-tree restoration.

The final inventory measured 103 owned paths across the Workbench slices and
7,160 shared dirty paths left untouched. No owned path is staged. The
coordination run was checked out; an updated interactive preview was opened
for the owner. These are handoff observations, not perpetual runtime claims.
