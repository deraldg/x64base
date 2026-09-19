# AIF-120 Workbench: serialized live session

Status: implemented and locally tested; review-needed, uncommitted.
Authorization: owner commissioned the Workbench and said "begin" for the next slice.
Session: CODEX-20260917-UIDEF-LIVE. Lane: AIF-120.

## Source mutation preflight

Targets: gui/uidef/workbench_session.hpp/.cpp and native tests; author_workbench.py,
wx_workbench.cpp, CMakeLists.txt, build_workbench.py, verify_workbench.py and
WORKBENCH.md; this report and owned evidence/registry fragments.
Subsystem: generated frontend and toolkit-neutral session adapter (C2).
Expected behavior: one in-process engine on one serialized worker; live desk
snapshots alongside saved catalog inspection; create root/child workspaces,
switch workspace, open private table copies, select stable area identities,
close the current workspace with the engine's recursion policy.

Reuse cmd_WORKSPACE for durable births, environment switching and close;
reuse workdesk::observe for membership truth. Do not mirror a child CLI or
implement an alternative workspace catalog. No changes to core engine rules.
The private session catalog and table copies are disposable; existing catalog
and table files are inputs only. No index attachment, edits or writeback UI.
All engine/catalog reads share the worker because their underlying state is
process-global. UI consumes values and shutdown joins the worker.

Contracts: same GUI/threading/database/UIDEF contracts listed in the first-slice
report, plus the canonical workspace membership and workdesk observer headers.
The workspace header's old PREV_ID-parent wording is known drift; containment
uses PARENT_ID, while PREV_ID records saved versions.

Proof plan: native build; real WORKSPACE operations in disposable data; durable
birth/parent identities; additive workspaces, separate current workspace/area,
stable area-handle validation, recursive versus scoped close, read-only source
hashes, queued shutdown, actual catalog inspection and generated UI smoke.
Existing samples, APPGUI, unrelated dirty work and repository state are preserved.

Owner steering: dogfood x64base; use SWITCH for workspaces and SELECT 4 /
SELECT students for areas (the owner corrected the earlier AREA [n] wording).
The temporary cmd_AREA change was removed. No core command semantics change.
The generated host resolves SWITCH through ShortcutResolver and calls cmd_SELECT
for selection after validating the UI's stable area handle. The command box also
passes SELECT names, qualified names and numeric slots to this same handler.
Native tests exercise the actual commands, including refusal and name scoping.

## Implementation and measured checks

- Generated WORKBENCH.DBF has 58 rows / 57 widgets. Layout remains DBF-authored.
  Saved catalogs and Live session are separate pages in one native wx window.
- WorkbenchSession owns one engine on one joined worker; a second concurrent
  session is refused. Catalog inspection now uses that same serialized worker.
  Closing drains admitted requests and detaches areas through WORKSPACE CLOSE ALL.
- NEW and NEW UNDER call cmd_WORKSPACE, including actual durable births in the
  private catalog. SWITCH uses ShortcutResolver; SELECT uses cmd_SELECT. There
  is no shadow workspace allocator or subprocess state to reconcile.
- Live values come from workdesk::observe, enriched with canonical area handles,
  local/engine slots and record counts. A stale area handle is refused before
  invoking SELECT. Typed SELECT retains the engine's slot/name/qualified semantics.
- Table families are copied before WORKSPACE ADD NOINDEX. Sources remain inputs;
  existing indexes are not attached. Private session files remain at the displayed
  temporary path, with no automatic recursive cleanup.
- Native tests passed: birth rows and PARENT_ID, stamped roots, duplicate names,
  undurable parent refusal, same table name in three workspaces, SWITCH and SELECT
  by slot/name/qualified name, missing-target refusal, independent workspace/area
  state, scoped and recursive close, stable handle refusal after slot reuse,
  twelve repeated close/reopen cycles, queued shutdown, unchanged source bytes.
- CTest: two native tests passed. Generated UI smoke: saved catalog page, live
  page with four workspaces and two areas, typed SELECT through the command-box
  handler, closing during a read, and valid native screenshots passed.
- Actual catalog read: 134 retained records, 148 deleted excluded, seven MINIDB
  images, zero payload errors. Source DBF/DTX SHA-256 stayed unchanged.

Evidence: evidence/AIF120_workbench_live_20260917.txt and
evidence/AIF120_workbench_20260917_v2.png / AIF120_workbench_20260917_v2-live.png.
The text record includes the tested binary hash and source-catalog hashes.

## Findings during dogfood

The UIDEF table silently truncates character fields: two new container names
exceeded OBJID's declared width and the host could not find them. Names now fit
the schema; the author checks object/parent lengths against uidef.FIELDS before
writing. No general generator vocabulary change was needed.

WORKSPACE's tokenizer is whitespace-based, not quote-aware. Private table names
are safe relative tokens under the engine's DBF slot; a source path with spaces
passes the native test. No new path parser was added to the command.

OutputRouter retains its console streambuf. Per-request temporary capture streams
would leave a dangling pointer. The host now supplies a process-lifetime capture
buffer owned by the single worker protocol; repeated command responses are tested.

The standalone closure links actual identity, close/commit, SQL-transaction and
index dependencies reached by WORKSPACE. No success stubs were introduced. This
does not expose editing or index attachment in the Workbench. Existing root build
and command source remain unchanged; the temporary AREA edit was fully removed.

## Limits and handoff

Session storage is retained for review, but this slice starts fresh on each launch
and cannot resume a retained session yet. Saved catalog IDs and session catalog
IDs must not be equated. Open-copy limit: 256 MiB per family; copy consistency is
size/mtime detection, not a transaction with concurrent writers.

MINIDB hydration, nested memo payload expansion, editable row browsing, explicit
writeback and full command-console dispatch remain later work. New labels retain
English fallbacks. Native Windows was tested; Linux/macOS were not tested here.
The broader AIF-120 lane remains open. No staging, commit, push or publication.

RE: AIF-120 steward -- generated Workbench live-session slice, authorized by the
owner's begin and SWITCH/SELECT/dogfood instructions. Changes: gui/uidef session,
host, document, build and verification; gui/README; owned docs/evidence/registry
fragments. Verify with build_workbench.py and verify_workbench.py. Undo only these
named additions and exact owned hunks, preserving earlier slices and shared work.
