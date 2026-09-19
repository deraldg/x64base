# AIF-120: buffered field editing in the native Workbench

## Preflight - 2026-09-18

Authorization: the commissioned Workbench and owner's explicit continuation.
Scope: Edit value for ordinary scalar fields; table-specific Commit and Rollback
actions; buffer visibility; native tests and generated-window dogfooding.
Files: gui/uidef/workbench_table.*, workbench_session.*, wx_workbench.cpp,
author_workbench.py, verification scripts/tests and owned documentation/registry.
No shared engine implementation change is planned.

Use the existing field validators, currency normalization, constraint/write
funnel and TABLE/COMMIT/ROLLBACK handlers. Values from the editor are literal
text, never shell input. Buffer readback must prove staging, and reopen/readback
must prove commit. Selected area/record/field and original value are rechecked
before mutation. Memo, binary, truncated and NULL previews remain inspect-only
in this scalar editor.

Baseline: development at b63606ec113edca7b7fc2986074b390cfb645817.
Coordination: CODEX-20260918-UIDEF-EDIT. The current target pointer is older
than the active owner commissioning; it declares no single controlling lane.
Existing Workbench and unrelated dirty work are preserved. No staging, git
mutation, publication, sample replacement or source-catalog edits.

Proof plan: literals and invalid types, pending/committed readback, rollback,
cursor/selection preservation, stale edit refusal, per-area isolation, primary
key gate, SQL transaction guard, native modal UI; existing catalog/session/
table/image checks and original catalog hashes. Evidence remains source_defined
while source and artifacts are uncommitted.

## Delivered behavior

The Table page has Edit value, Commit table and Rollback table actions. The
editor displays the full scalar value and stages on Buffer value; inspection
and double-click remain read-only. The header counts distinct buffered records.

The worker checks current area, area handle, record, field name and original
value. It uses the existing currency and field validators, native constraint
gate, TABLE handler and xbase::cli::replaceFieldStored. A successful edit is
read back from the actual TableBuffer. The current record is restored. Literal
quotes, ampersands, command words and newlines do not enter the shell parser.

Commit/Rollback call their native command handlers for the selected area and
check that its buffer and dirty state cleared. They include prior command-box
edits to that table. Other tables retain their pending work. Active SQL
transactions refuse these native actions; the SQL transaction must be resolved
through the command console. Partial/failed operations retain the engine's
feedback in Engine response and report remaining buffered changes.

Supported editor types are C, N, F, I, B, Y, D, T and L. Memo, NULL, binary,
truncated, deleted-record and primary-key values are inspect-only in this
editor, with a reason. Text wider than its field is refused rather than silently
truncated. The limit is 64 KiB per value, with no NUL bytes. The GUI also refuses
editing text it cannot display. This scalar editor does not allocate memo
objects or duplicate the engine's validation rules.

The old-value comparison is an optimistic check at staging, not a record lock
held across the modal dialog or until commit. Commit uses the engine's existing
record locking, index and durability behavior; no new atomicity/power-loss
guarantee is claimed. TABLE buffering stays enabled after resolving changes.

## Measured Windows verification

Evidence: evidence/AIF120_workbench_edit_20260918.txt and the v6 PNG family.

- Four native test programs passed, including the extended table test.
- Literal text containing a quote, macro spelling, command word and newline
  was read back from the buffer, committed, closed and reopened byte-for-value.
  Numeric 42.75 survived the same reopen. Staging left the physical copy's DBF
  bytes unchanged; rollback restored original values without a DBF write.
- Invalid numeric/logical input and overwidth text refused. Date normalization,
  primary-key refusal, stale original-value refusal and SQL transaction guards
  passed. Record 1 was edited while the current record remained at 2.
- A second workspace held a separate buffered edit. Stale Commit targeting
  the first table refused until SELECT restored that area. Committing it left
  the peer edit intact, and the peer's later rollback cleared only that buffer.
- Seven generated-window modes passed: saved catalog, live commands, browse,
  native edit, image hydration, nested image hydration and close during read.
  The edit mode exercised the actual modal editor twice, rollback, commit,
  close and reopen. The reviewed screenshot shows the reopened committed value,
  all fields and zero buffered records.
- The real catalog still measured 134 retained records, 148 deleted, seven
  MINIDBs and no payload errors. Seven images hydrated into 97 open areas.
  Nested-image behavior passed against the private DBF/DTX fixture.
- Source WORKSPACES.dbf SHA-256 unchanged:
  0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e.
  Source WORKSPACES.dtx SHA-256 unchanged:
  152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
- Tested generated executable SHA-256:
  ffcfcc90c64988678c604f1a40980f71c7ade87083c3e1edef6eede0cacd8ab5.

Only Windows was tested. The existing engine implementation was reused without
changes; this continuation does not claim a new CLI regression-suite run.

## Test corrections and existing boundaries

The first transaction test used SQLSEL BEGIN in native mode, which correctly
refused to begin. The corrected test enters SQL mode, begins, verifies both
editor and Commit refusals, rolls back, and restores native mode.

The first reopen check used a quoted absolute path with USE and did not reopen
the file. The test now asserts that the reopened table has rows before reading
them, then uses USE's supported unquoted path form on the private path (which
contains no spaces). GUI and native reopen readbacks passed. No quoted-path
support or path-with-spaces support is claimed for USE; Open table copy retains
its independently tested file-dialog support for source paths with spaces.

The numeric CDX ordering finding recorded in AIF120_WORKBENCH_BROWSE_V1.md is
unchanged. Index encoding and session persistence remain separate work.

## Housekeeping and good-neighbor handoff

Whole-tree inventory and retained build/session/fixture paths are recorded in
evidence/AIF120_workbench_edit_housekeeping_20260918.txt: 76 owned dirty paths
including earlier slices, and 7,160 shared paths left untouched. All owned
paths remain unstaged. Git could not enumerate .pytest_cache due to permissions;
the inventory records that limit. Existing samples,
APPGUI, cmd_area.cpp and unrelated dirty files are preserved. No git mutation,
publication, cleanup or lane closure. Owned source and proof artifacts remain
uncommitted, with proof state source_defined.

RE: AIF-120 -- for maintainer transcription

WHAT_CHANGED: native scalar editor and selected-table Commit/Rollback controls;
worker identity/value checks and buffer readback; generated UI/native tests;
guide, evidence and owned registration.

WHOSE_AREA: AIF-120 Workbench, owner member.derald, steward member.ai.claude.cowork.
Existing AIF-156 write/constraint and AIF-159 transaction guards are reused.

AUTHORIZATION: owner commissioned the Workbench and explicitly continued it.

VERIFY_OR_UNDO: run gui/uidef/build_workbench.py and verify_workbench.py.
Undo only this continuation's named hunks and new artifacts; preserve prior
Workbench slices and unrelated work. No whole-file reverts or broad staging.

Final interactive preview launched from build/uidef-native/Release/arctictalk_workbench.exe
(PID 37372 at handoff). Coordination run CODEX-20260918-UIDEF-EDIT checked out.
