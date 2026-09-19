# AIF-120 Workbench command-load visibility V1

Status: implemented locally; final verification and housekeeping below. Uncommitted.
Run: CODEX-20260918-UIDEF-LOADVIEW.

Authorization: the maintainer commissioned the Workbench, authorized continued
implementation, and reported that command-box directory loads and MINIDB
hydration leave the Database images page blank.

Preflight: change gui/uidef session, generated design, native host and verification
code; add include/cli/workspace_image_event.hpp and a bounded notification in
src/cli/cmd_workspace.cpp. Native commands retain loading authority. Record exact
MINIDB payload and actual newly opened area handles after materialization; do not
infer success from printed output or workspace_last_loaded_file(). Directory loads
show Live session / Tables. Command MINIDB loads populate Database images. The
page gets entry controls, live-table access, and truthful empty-state guidance.
Remove the saved-record panel's unconditional "Not performed" assertion.

Proof plan: native command tests for DO x64 / WORKSPACE OPEN dbf, command MINIDB
loads and refusal; native window tests for both views, refresh and navigation;
existing Workbench regression suite. Use isolated fixture data and compare source
catalog hashes. Preserve the running Workbench process; build a separately named
preview. Do not modify cmd_area.cpp, source catalog data, INI files, APPGUI or
samples. No git mutations, staging, commit, push or cleanup.

## Result

src/cli/cmd_workspace.cpp emits an optional, engine-thread notification after
native MINIDB materialization. It includes the exact payload, catalog, workspace,
RAM root and actual newly opened stable area handles. No observer is required by
the CLI. The Workbench worker subscribes and inspects command-origin payloads,
including commands run through DO. Observer exceptions do not relabel a completed
engine mutation as a loader failure. Existing loading authority stays in the CLI.

gui/uidef/workbench_session.cpp publishes command image trees and measured new
table counts. gui/uidef/wx_workbench.cpp routes new tables to Live session / Tables
and MINIDB notifications to Database images. It preserves the inspected payload
across subsequent refresh and tab navigation. The page names images readably,
retains source provenance, reports the current open-table count, and exposes
Choose saved image, Open image file, and View live tables without a selection.
The saved catalog no longer claims "Hydration: Not performed" unconditionally.

The image view represents the inspected saved payload, not a continually resaved
copy of live edits. Its command-load count is explicitly historical; View live
tables observes current engine state. Native commands retain VDISK/path behavior.
Command notifications do not acquire ownership of user-mounted RAM disks. GUI
Hydrate keeps its existing private-mount ownership and recovery logic. In a
script with several loads, all emitted images from that command are displayed.
An image materialized with no successfully opened DBF reports zero opened tables.

The new executable is build/uidef-native/Release/arctictalk_workbench_loadview.exe.
build_workbench.py and verify_workbench.py accept --output-name for side-by-side
builds. The older executable and its live process are preserved.

## Good-neighbor note for maintainer transcription

WHAT_CHANGED: AIF-120 generated Workbench command-load visibility, direct image
entry controls, truthful state text, native observation interface and tests.
WHOSE_AREA: AIF-120 / project.x64base.gui and CLI workspace loading;
owner member.derald, steward member.ai.claude.cowork.
AUTHORIZATION: Ongoing owner commission and specific command-load/blank-tab
defect report; no source catalog edits or reinterpretation of loading commands.
VERIFY_OR_UNDO: From D:\code\ccode run .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py --output-name arctictalk_workbench_loadview.
Undo only the notification, load-view and corresponding test/doc changes named
here; preserve prior same-file Workbench work and unrelated dirty paths.

## Verification and handoff

Runtime proof: evidence/AIF120_workbench_loadview_20260918.txt. Eight native
programs and fourteen window modes pass. The final design contains 123 rows
including the document; generator conformance has no findings. New proof covers
the exact DO x64 / WORKSPACE OPEN dbf sequence, direct and scripted MINIDB loads,
nested DTX payload observation, actual open RAM records, unmounted/missing-image
refusals, no stale event on refresh, and zero opened tables for an invalid DBF
whose image bytes materialized. Window proof exercises command-box dispatch,
automatic Tables/image navigation, empty-state controls, tab round trips,
refresh retention, and refusal without erasing the inspected image. Existing
catalog, browsing/editing, save/reopen, memo, export, storage and workspace-scope
checks pass. Every MINIDB in the source catalog was hydrated privately: seven
images, 97 tables. No full standalone CLI regression is claimed.

The final v13-loadview.png capture was visually checked: PathImage is readable,
source provenance is retained, its STUDENTS.dbf member is displayed, load-time
count is one, and the current open-table count is two. The native tests also
prove nested expansion and the zero-open-table failure case. Evidence and
sources are uncommitted; the proof registry remains source_defined.

Final preview SHA-256:
0d6908ce99d181e33f47e72a30663b0b63273f3d56fbad99cccd3cb9120f9ced.
The previous arctictalk_workbench.exe remains byte-identical:
e5f4d7592f414baddccd85784294fdbe61797e6ac09c39443bc2d6b2be67ee53.
Updated preview process 46920 started at 2026-09-18 10:07 local and reported
ArcticTalk Workbench / Responding=True. The previous process was never closed
or killed by this work; it was no longer present at final inventory.

Source WORKSPACES.dbf and WORKSPACES.dtx remain unchanged after preview startup:
0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e and
152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
cmd_area.cpp, installation INI files, sample GUIs and APPGUI were not changed.

## Housekeeping

Measured inventory: evidence/AIF120_workbench_loadview_housekeeping_20260918.txt.
187 owned dirty paths include prior Workbench slices; 7,158 shared dirty paths
were left untouched. No owned staging. The shared TIER0_STATE.md became dirty
since the prior inventory; its authorship is not inferred. The pre-existing
.pytest_cache traversal permission warning remains recorded. Branch development
and HEAD bbf22e7570f1d9a3c5a0286cdb3cd2333e7dacfe match preflight.

Seventy-nine temporary fixture/session directories remain and are listed by
exact path. Build residue includes generated UI, libraries, both executables,
four phase build/verification logs and the preview PID marker. Temporary data
includes private catalogs, DBF copies, exported images and memo sidecars. Test
processes have exited; the preview owns an independent live engine session.
No shared cleanup, staging, commit, branch operation, push or publication.
Build PATH/VCPKG_ROOT changes were subprocess-local; dependencies pre-existed.
A clean clone needs the uncommitted sources/evidence and Windows dependencies.
Registry YAML and all registered artifact paths were validated.
CODEX-20260918-UIDEF-LOADVIEW checked out after final verification; final
inventory retained the same path counts and source hashes.
