# M3 - Everyday table operations and editing

Owner: member.derald. Lane: AIF-120. Author: member.ai.codex.
Run: CODEX-20260918-UIDEF-M3. Date: 2026-09-18.
State: M3 GUI locally complete and verified on Windows, within the native limits
below. Source and evidence remain local and uncommitted; no published proof claim.

## Delivered behavior

- Record menu and table buttons: first/previous/next/last record, Go to,
  Filter, index file/tag/direction, Seek, deleted visibility, append, delete,
  recall and explicit field NULL. Generated OP_FORM supplies modal input,
  cancellation, target identity and validation.
- Page controls are labelled as pages; record controls move the native cursor
  and follow its page. Record fields retain selection. Ctrl+Left/Right changes
  record, Ctrl+Home/End goes first/last, and F2 opens the existing typed editor.
- Ordinary DTX memo text supports the same Edit value, Commit table and
  Rollback table workflow as scalar fields. Both token and fixed x64 memo
  references are supported. Stale fields, deleted rows, protected keys,
  SQL transactions, binary/truncated content and MINIDB text editing refuse.
- Pending deletion is labelled explicitly. TABLE ON/OFF and pending record
  counts are visible beside the current order, filter and cursor.

## Buffer contract and native limits

TABLE ON means supported buffered operations. The GUI never silently turns it
off. Scalar/memo edits and record deletion are buffered. Commit/Rollback target
the identified selected table; peer buffers are preserved.

Append and recall controls refuse under TABLE ON. The Workbench command guard
also refuses APPEND, APPEND_BLANK, RECALL and UNDELETE under TABLE ON, including
script dispatch. With an explicitly selected TABLE OFF mode and no pending
changes, their modal says Write now. This does not implement native buffered
append or recall. The native command implementations are separate follow-up work.

NULL uses the existing nullable-field write funnel. That funnel refuses TABLE
buffering and fields without null bits. The GUI does the same; TABLE OFF NULL
is explicitly labelled immediate. No string marker is substituted for NULL.

Memo text editing follows the established Store image implementation: allocate
a fresh DTX object and buffer its reference. The committed DBF reference and
shared original object remain unchanged before Commit. Rollback restores the
original reference, but newly allocated, unreferenced DTX objects remain. This
is not a claim of zero sidecar allocation or automatic reclamation.

Native SEEK tokenization does not preserve quoted keys containing spaces.
The guided control refuses them with a Filter alternative. Single-token keys
use the native SEEK path; the GUI does not create another search implementation.

## Prior art and engine handoff

The existing comparison is [filed here](AIF120_WORKBENCH_COMPARISON_V1.md).
The older Record View at `src/gui/wx/main_frame.cpp:1912` and its keyboard
handler at line 2095 informed the field view/navigation. These original
read-only sample controls and the Python sample are preserved.

Native implementation pointers for the maintainer's proposed Claude handoff:

- `src/cli/append_support.cpp:610`: append-blank core takes a table lock,
  appends through DbArea, then finalizes keys/indexes.
- `src/cli/cmd_delete.cpp:290`: current-record delete already branches into
  the table buffer. Reuse this established path.
- `src/cli/cmd_recall.cpp:216`: recall clears the physical deletion flag and
  updates indexes; it needs a buffered counterpart before enabling it here.
- `src/cli/xbase_cli_write.cpp:200`: native NULL explicitly refuses buffering.
- `src/cli/cmd_seek.cpp:448`: whitespace tokenization precedes value parsing.

For buffered append, settle pending row identity before UI changes: how a new
row is addressed before Commit, how it appears in browse/filter/order, when
automatic/primary keys are assigned, how Commit maps it to a physical record,
and how Rollback discards it. Verify multiple pending appends, intervening
writers, key refusal, failure/retry, journals and peer isolation. These are
acceptance questions, not a new storage design imposed by the GUI.

No message was sent to another agent. Core buffer/append/recall/parser sources
were not modified in this pass.

## Verification and delivery

All nine registered checks pass on the final build. The broader window suite
passed seventeen generated-window modes plus close-during-read. A final layout
correction moved the field view beside the table; after that correction the nine
checks and the complete eighteen-step M3 window workflow passed again. The final
capture was inspected and both record/table panes are visible at normal size.

- [Final build](evidence/AIF120_workbench_m3_build_20260918.txt)
- [Nine final checks](evidence/AIF120_workbench_m3_tests_20260918.txt)
- [Broader window suite](evidence/AIF120_workbench_m3_windows_20260918.txt)
- [Final M3 window workflow and executable hash](evidence/AIF120_workbench_m3_release_20260918.txt)
- [Final window](evidence/AIF120_workbench_m3_20260918.png)
- [Housekeeping and protected-file hashes](evidence/AIF120_workbench_m3_housekeeping_20260918.txt)

Native tests cover order/filter/seek/cursor agreement, stale targets, buffered
delete/rollback, TABLE ON refusals, explicit TABLE OFF append/recall, token/fixed
memo readback, repeated edits, shared references, rollback, commit/reopen, empty
memo, peer isolation and native nullable-field writes/refusal under TABLE ON.
The window test exercises modal cancellation/validation, record paging and
keyboard navigation, filter clearing, memo editing/commit/rollback, visible
buffered deletion and the TABLE ON append refusal.

Original WORKSPACES DBF/DTX and protected older GUI/core sources match their
before-pass hashes. Tests used private copies. Early failed seek/test-setup
runs are retained under build/uidef-m3 and superseded by the passing evidence.

Build output: `D:\code\ccode\build\uidef-native\Release\arctictalk_workbench_m3.exe`.
SHA256: `ad641d7bc55601fb0c0bcd30f97cd177fe3ab1c80c9a6e4c4556f5d148ccb926`.
The earlier catalog-flow executable and the user's open session are preserved.
No commit, push, promotion or publication is part of this pass.

WHAT_CHANGED: generated Workbench design, host actions, table/session services,
native and generated-window checks, and this closeout.
WHOSE_AREA: AIF-120, owner member.derald, steward member.ai.claude.cowork.
AUTHORIZATION: owner requested M3 and explicitly asked to wrap M3 with a good build.
VERIFY_OR_UNDO: build/test logs and per-file before-copies are retained under
`build/uidef-m3`; compare only these owned changes, preserving prior dirty work.
