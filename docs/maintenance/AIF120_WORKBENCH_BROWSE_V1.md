# AIF-120: native table and memo browsing

## Mutation preflight - 2026-09-18

Owner authorization: commissioned Workbench, command console expansion, then
`continue`. Bounded continuation: read-only table paging and field/memo inspection
in the generated native Workbench, sharing the console's selected live area.

Working tree: D:\code\ccode, development. Baseline HEAD:
b63606ec113edca7b7fc2986074b390cfb645817. Coordination handle:
CODEX-20260918-UIDEF-BROWSE. Existing dirty work is preserved.

Changes: gui/uidef host, session and generated document; minimal prerequisite
widening of Table::overlay_for and its private helper to uint64_t record IDs.
Documentation, owned evidence and registry fragments accompany the change.
No changes to cmd_area.cpp, APPGUI, or either existing sample. No git mutation
or publication is authorized or performed.

Validation planned: native tests for paging, order/filter/deleted policy,
cursor preservation, buffered values, stale identities and memo preview limits;
native GUI command-to-BROWSE and field inspection; existing catalog/session/image
regressions and unchanged source catalog hashes. Local evidence remains
source_defined while the implementation is uncommitted.

## Delivered behavior

BROWSE now opens the generated native Table page in the existing session.
The command is rebound only in this host and restored at shutdown; terminal
BROWSER and the other incompatible frontend owners retain clear refusals.
The ordinary CLI retains its own BROWSE implementation.

The view pages 100 rows through order_stream_display and filter::visible,
preserving the current physical record. The header distinguishes SET FILTER
from deleted-row visibility. Record selection explicitly executes GOTO in the
same area, with slot/handle validation. Switching or closing tables refreshes
the view. No engine pointer crosses to the UI thread.

Field and memo inspection runs on the same serialized worker and opens a
read-only window. Memo cells are lazy placeholders; inspection uses the already
attached engine memo backend, checks object existence/size, and resolves x64
object IDs through MemoStore. Binary previews use hexadecimal. Text and binary
previews are bounded to 64 KiB and 4 KiB respectively; memo objects over 1 MiB
are refused before loading. The window refuses close while a field read runs.

Table-buffer overlays supply pending scalar and memo values. The shared
Table::overlay_for lookup and its private helper now accept uint64_t record
numbers, matching TableBuffer's existing key width. Other legacy int-based Row
and snapshot APIs were not widened; this is not a whole-engine 64-bit claim.

The grid is read-only. Commands still perform edits, commits and rollbacks.
Filter membership and index order follow persisted engine values, then buffered
cell values are overlaid. Paging scans at most 100,000 ordered entries per
request, including skipped entries, and reports an incomplete view if capped.
INX/ISX/CSX traversal retains the engine's materialized-vector fallback.
The guide records all limits and supported host-specific BROWSE forms.

## Measured Windows verification

Evidence: evidence/AIF120_workbench_browse_20260918.txt and the v5 PNG family.

- Four native test executables passed: catalog, session, images and table.
- The 205-row table fixture proves first/second/last pages, GOTO selection,
  preserved cursor, filters, deleted-row visibility and markers, buffered
  scalar/memo values, rollback/commit refresh, CDX/LMDB display order, stale
  field/area refusal and source-family byte preservation. A sparse buffer
  entry at record 0x100000007 proves the widened overlay does not alias record 7;
  this does not require or claim a multi-billion-row DBF fixture.
- Memo checks cover text resolution, binary hex, truncated long text and
  pre-read refusal above the memo limit.
- Six generated-window modes passed: saved catalog, live commands/history/
  buffered-close veto, native BROWSE, image hydration, nested image hydration,
  and close during a catalog read. BROWSE was sent through the command input's
  Enter handler. Next/Previous, Select record and a read-only memo dialog were
  exercised. Final table screenshot visually reviewed with record 7 and all
  three fields visible.
- The real catalog measured 134 retained records, 148 deleted, seven MINIDBs
  and zero payload errors. All seven images hydrated into 97 simultaneously
  open areas; their selected RAM table views were read successfully. Nested
  images were verified by the separate DBF/DTX fixture.
- Source WORKSPACES.dbf SHA-256 stayed
  0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e.
  Source WORKSPACES.dtx SHA-256 stayed
  152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
- Final generated executable SHA-256:
  de0b03ace41a6e6749764ae74947bf63e1acae66d21308b3461b467970786ec3.
- The ordinary dottalkpp executable rebuilt after the shared signature change;
  its --help smoke passed. This is not a full CLI regression-suite claim.
- Scoped diff checks passed. src/cli/cmd_area.cpp still has no diff.

Only Windows was exercised. Tests and local evidence are uncommitted; the
proof registry remains source_defined.

## Engine finding from dogfooding

The native CDX fixture exposed numeric text-key ordering: DESC on NUMBER
(values 1 through 205) starts at 99, not 205. LIST TOP 1 and the grid agree.
Source inspection of src/cli/cmd_buildlmdb.cpp, build_tag_to_lmdb, confirms
that this path obtains area.get(fld), then right-pads to field length for the
LMDB key. It does not encode numeric values for numeric comparison.

This is a measured existing index behavior, not a native-grid sorting rule.
No index writer or comparison policy was changed in this continuation. A future
index fix needs its own numeric-key contract and rebuild/compatibility proof.

## Housekeeping and handoff

The read-only whole-tree inventory is
evidence/AIF120_workbench_browse_housekeeping_20260918.txt: 66 owned dirty paths
(including earlier Workbench slices), 7,160 shared paths left untouched.
All owned paths are unstaged. Git could not enumerate .pytest_cache due to
permissions; the inventory records that limitation. No cleanup was attempted.
Private test/session folders and isolated build logs are retained and listed.
Verifier result-marker folders cleaned themselves. SDK builds and visible
capture used the approved installed Windows toolchain.

RE: AIF-120 and table-buffer owners -- for maintainer transcription

WHAT_CHANGED: generated native table/memo view, host BROWSE binding, serialized
value reads, 64-bit buffer lookup, native/GUI tests, guide and owned evidence.

WHOSE_AREA: AIF-120 generated frontend; shared cli/table_object lookup signature.
Owner member.derald; steward member.ai.claude.cowork.

AUTHORIZATION: commissioned Workbench, engine dogfooding, command expansion and
explicit continuation. The two small sample GUIs remain available.

VERIFY_OR_UNDO: run gui/uidef/build_workbench.py and verify_workbench.py.
Undo only this continuation's named hunks/files, preserving previous Workbench
work and unrelated changes. No whole-file revert, reset or broad staging.
No git mutation, publication, APPGUI replacement or lane closure performed.

Final interactive preview opened from build/uidef-native/Release/arctictalk_workbench.exe
(PID 48760 at handoff). Coordination run CODEX-20260918-UIDEF-BROWSE checked out.
