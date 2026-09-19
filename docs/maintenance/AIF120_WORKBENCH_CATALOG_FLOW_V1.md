# ArcticTalk Workbench - direct saved catalog workflow

Owner: member.derald. Lane: AIF-120. Author: member.ai.codex.
Run: CODEX-20260918-UIDEF-CATALOGFLOW. Date: 2026-09-18.
Development baseline: bbf22e7570f1d9a3c5a0286cdb3cd2333e7dacfe.

Status: locally built and verified on Windows. Source and evidence uncommitted.
This implements the catalog-flow prerequisite from the
[Workbench comparison](AIF120_WORKBENCH_COMPARISON_V1.md), before M3.

## User flow

Saved catalogs now has two direct actions alongside an explanation of the
selected record. A MINIDB offers **Hydrate to RAM...**. Its generated modal shows
the catalog path, saved ID, name and historical-version status. Enter a new
workspace name and optionally choose **Create under the current workspace**.
The current parent is named in the dialog. Success enters that workspace,
shows its tables and populates Database images from the same selected payload.
Tables and indexes are RAM files; DTX memo sidecars remain on disk.

A DTSHEMA 2/3 entry offers **Load definition...**. The existing generated Load
modal shows the exact saved identity as a non-editable source and names the
current destination workspace. Table and index defaults are explicit. Missing
tables keep the modal open for correction; locations recorded inside a V3
definition retain native priority. A definition reopens referenced files and
does not carry their saved contents. Create/SWITCH workspace first when a
different destination is wanted.

BIRTH, empty, corrupt and unsupported entries explain their unavailable action.
Inspect image remains available independently. Current and superseded entries
use their captured payload bytes, without resolving a reused workspace name.
Escape, Cancel and window close abandon the modal without submitting a load.
The worker rechecks the destination, parent, missing members and buffered edits.

## Implementation boundaries

- `gui/uidef/author_workbench.py`: generated catalog actions and RAM modal.
- `gui/uidef/wx_workbench.cpp`: selected-version dispatch, modal validation,
  completion navigation, image inspection and real generated-dialog proof.
- `gui/uidef/workbench_catalog.hpp/.cpp`: payload action classification and
  unavailable-state explanations.
- `gui/uidef/workbench_session.hpp/.cpp`: exact definition bytes staged under
  the private session home, shared native preflight/load, parent and edit checks.
- `gui/uidef/workbench_paths_test.cpp`, `workbench_m1_test.py` and
  `verify_workbench.py`: native and generated-window verification.

Source anchors: `gui/uidef/workbench_catalog.cpp:74` classifies saved payloads;
`gui/uidef/workbench_session.cpp:294` stages exact definition bytes;
`gui/uidef/wx_workbench.cpp:525` supplies modal validation;
`gui/uidef/wx_workbench.cpp:629` dispatches the selected catalog record;
`gui/uidef/wx_workbench.cpp:1362` exercises the generated catalog dialogs;
`gui/uidef/wx_workbench.cpp:2075` presents available actions.

The core WORKSPACE parser is reused without source changes in this pass.
Native and Python sample GUIs and APPGUI are preserved. Hydration still creates
a native birth identity in the configured destination catalog; it does not
overwrite the selected saved version. The catalog used for inspection may be
different from that destination catalog. Tests use private fixtures.

## Verification and local state

The final build passed all nine registered checks. The verifier passed all
seventeen window modes, including five direct catalog-flow stages, 23 existing
M1 modal lifetimes and 27 M2 navigator stages. The new native proof reads Ada
from disk and RAM, checks historical alias/parent/current area, and preserves
the source catalog bytes. The generated-button proof checks modal Enter/Escape,
invalid name, missing-root correction, cancellation, peer preservation and
Database images population. Existing nested-image workflows also pass; full
workspace-tree restoration remains M6.

- [Build and nine checks](evidence/AIF120_workbench_catalog_flow_build_20260918.txt)
- [Native and seventeen window modes](evidence/AIF120_workbench_catalog_flow_20260918.txt)
- [Fresh default-launch UI observation](evidence/AIF120_workbench_catalog_flow_ui_20260918.txt)
- [Catalog view](evidence/AIF120_workbench_catalog_flow_20260918.png)
- [Historical selected version](evidence/AIF120_workbench_catalog_flow_history_20260918.png)
- [RAM modal](evidence/AIF120_workbench_catalog_flow_hydrate_20260918.png)
- [Definition modal](evidence/AIF120_workbench_catalog_flow_load_20260918.png)
- [Measured housekeeping](evidence/AIF120_workbench_catalog_flow_housekeeping_20260918.txt)

The modal captures retain the inline validation messages deliberately exercised
by the tests before accepting corrected values. A separate fresh launch was
visually inspected using the installed catalog; its window remains open.
No load or hydration was submitted by the verification agent in that window.
During final filing, a later passive observation showed `mcc_db_ram` with 13 RAM
tables, areas 0-12, and BUILDING selected at area 0 displaying Science Hall.
The catalog then measured 137 live records / 9 images, up from 136 / 8 during
the private tests. Those later live-session writes are preserved and recorded
separately in the UI and housekeeping evidence.

Executable: `D:\code\ccode\build\uidef-native\Release\arctictalk_workbench_catalogflow.exe`.
SHA-256: `500fe7043df327d467b9fb74deb06e431435b76c6b436acc2e95a871db66b264`.
Run `gui/uidef/build_workbench.py --output-name arctictalk_workbench_catalogflow`
then `gui/uidef/verify_workbench.py --output-name arctictalk_workbench_catalogflow`
with `.venv312/Scripts/python.exe -B` from the development root.

At completion of the automated private-data tests, WORKSPACES.dbf SHA-256 was
`0e2a1ca9d95eb325f1a4f1c536b858950f8fce91975d2d6a4d961b585586e824`;
WORKSPACES.dtx was
`146e7905f832f3077521f3091f18b6422b66014c443609ba8204160705fb8016`.
Both matched their pre-test hashes. These are test-boundary hashes; subsequent
live hydration changed the catalog family as described above.

The first build attempt could not read the Windows SDK under the restricted
compiler environment. Building with approved SDK access proceeded; the design
validator then caught an overlong form-control ID, corrected before regeneration.
The first window test caught a startup abort: the catalog controls were passed
to a lookup helper that searched only children of a named panel. Direct controls
now match before the child search. The maintainer reported the abort and asked
for the fix. Failed runs are retained, and no successful GUI proof is inferred
from the earlier native-only pass.

Before-copies and failed build logs are in `build/uidef-catalogflow/`. Staged
definition files remain inside the named private session directories for review.
No dependency installation, persistent environment change, branch operation,
staging, commit, promotion or publication is part of this pass.
The continuation checked out of the coordinator after verification. M3 is next;
the AIF-120 lane remains open.

WHAT_CHANGED: Added direct catalog load/RAM hydration with exact selected-version
identity, generated modal controls, destination/root checks and field readback tests.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald,
steward member.ai.claude.cowork.
AUTHORIZATION: Owner's continue request following the completed comparison and
its bounded catalog-flow prerequisite, within the commissioned Workbench work.
VERIFY_OR_UNDO: Build and verify using the Workbench scripts; compare only the
named files against build/uidef-catalogflow/before, preserving prior/shared work.
