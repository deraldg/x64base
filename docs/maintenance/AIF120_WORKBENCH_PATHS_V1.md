# AIF-120: Workbench paths and defaults

## Preflight - 2026-09-18

Authorization: owner requests SET PATH/defaults in the workflow and
workspaces/WORKSPACES.dbf as the default catalog. Coordination run
CODEX-20260918-UIDEF-PATHS; no other live session reported. Development HEAD
bbf22e7570f1d9a3c5a0286cdb3cd2333e7dacfe.

Targets: gui/uidef session, host, generated layout author, path helper/tests,
CMake and verifier; src/cli/cmd_setpath_command.cpp for RESET root binding;
owned docs/evidence/registry. Preserve samples and cmd_area.cpp.

Normal GUI startup resolves installation DATA, initializes native path slots,
and inspects WORKSPACES/WORKSPACES.dbf. Private test sessions remain explicit.
Expose native slots and default catalog; edits use SET PATH and read back the
engine state. Typed path changes and SWITCH must refresh the displayed paths.
Catalog overrides remain available. Prove defaults, relative paths with spaces,
bare table/directory opening, SWITCH restoration, RESET, IN targeting, startup
from an unrelated working directory, catalog following and override behavior.
Run existing Workbench proofs, hash source catalog and inventory shared state.

## Implementation notes

The owner's CLI output confirms native INIT loads BIN/dottalkpp.ini then
BIN/init.ini. The Workbench now reuses that initializer with its configured
installation BIN, including typed INIT. src/cli/cmd_init.cpp exposes the shared
implementation; its CLI wrapper preserves executable-relative discovery.
No INI file is edited. Init commands retain their normal effects.

Normal native workspace creation and image-import births/payloads now use the
active WORKSPACES catalog. Private Open table copy data and image RAM mounts
remain private. Save image continues to use private export staging. This fixes
the earlier inconsistency where changing WORKSPACES via commands caused image
attachment to look for its birth in the wrong catalog. Tests use a temporary
installation for these writes, with explicit --private-session for old proofs.

The first native path test assumed single-file WORKSPACE OPEN allocated a new
area. It correctly reused the current area. The fixture now uses SELECT 4 before
opening the second file; this follows native area semantics. The design-table
validator also caught an overlong new OBJID before compilation; it was shortened.

## Delivered and verified

The generated Paths and defaults page displays 52 native path slots and their
directory availability. Set selected path invokes the existing SETPATH handler;
typed SET PATH and SWITCH refresh the same values. Reset paths and Run INIT use
the native commands. File pickers start at the native DBF or WORKSPACES path.
Settings apply to this session; no INI files or machine environment are rewritten.

Saved catalogs initially follows WORKSPACES/WORKSPACES.dbf. A chosen or typed
inspection file stays pinned while engine paths change. Use default catalog
resumes following. No singular workspace.dbf copy or alias is created. Inspection
overrides do not retarget native workspace writes. Normal workspace births and
imported image payloads are durable in the active WORKSPACES catalog.

Eight native programs and thirteen window modes passed in
evidence/AIF120_workbench_paths_20260918.txt. The build regenerated 119 design
rows including the document row, with no conformance findings. Native tests
prove system/user INIT order, paths with spaces, OPEN dbf, bare table names,
relative DATA resolution, SWITCH restoration, RESET persistence after switching,
IN targeting, invalid slot/newline/ambiguous IN refusal, and configured-catalog
birth/payload readback for image import. The GUI test proves typed WORKSPACES
changes update default inspection, pinned inspection survives a missing default,
and Reset, INIT and Use default catalog controls work. Its capture shows the
path grid, directory values, availability, default catalog and matching footer.

Separate real-installation startup from the Windows TEMP working directory,
with no --data-root or --catalog override, passed and inspected
D:\code\ccode\dottalkpp\data\workspaces\WORKSPACES.dbf. Evidence is
evidence/AIF120_workbench_defaults_20260918.txt and v12-defaults.png. The first
capture attempt used a hidden Windows window and was correctly rejected as
black; the visible rerun passed. No source change was made for that retry.

The existing tests still hydrate seven real catalog images into 97 areas. The
source catalog has 134 retained and 148 deleted records, with seven MINIDBs and
no payload errors. Source DBF/DTX hashes stayed unchanged through both tests:
0221de4b8752afe43d4dedeb9f49869373f024e115fa3e40a26d4dec0f43a23e
and 152b64988b90cfd467957e561c14cfbde29e034dbd19ca448c9e7209a1b7d722.
Tested executable SHA-256:
e5f4d7592f414baddccd85784294fdbe61797e6ac09c39443bc2d6b2be67ee53.

src/cli/cmd_area.cpp and cmd_workspace.cpp remain unchanged this phase:
a055420cbf3714a98d6113e9c1ccf3463d88c12955c142be95335443ba4afa62
and 8e492fb90f518e4ba1c24e32be298b4d4a4b4cdfa6e12ad5db879b8ac2022eac.
Samples and APPGUI remain unchanged. The standalone/staged CLI executable was
not rebuilt or staged; shared INIT/RESET changes were compiled and exercised
in the Workbench's native command runtime. No full CLI regression is claimed.

## Good-neighbor note for maintainer transcription

WHAT_CHANGED: AIF-120 Workbench installation paths, default workspace catalog,
generated settings page and native path proofs. Shared cmd_init.cpp factors
INIT for configured host BIN; cmd_setpath_command.cpp binds RESET roots so
SWITCH cannot resurrect old current-workspace paths.
WHOSE_AREA: AIF-120 / project.x64base.gui and CLI initialization/path settings;
owner member.derald, steward member.ai.claude.cowork.
AUTHORIZATION: Owner requested path/default workflow and supplied the CLI INIT
and SET PATH sequence to match. No shared catalog or INI content edits.
VERIFY_OR_UNDO: From D:\code\ccode run .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py. Undo only this phase's named changes, preserving
all previous Workbench work and unrelated dirty files.

## Housekeeping

Inventory: evidence/AIF120_workbench_paths_housekeeping_20260918.txt. Source,
proof and evidence are local/uncommitted; proof state remains source_defined.
No staging, commit, branch change, push, publication or shared cleanup occurred.
No dependencies were installed or persistent environment values changed.

Residue includes build/uidef-native generated UI, binaries, paths-build.log,
paths-final-build.log, paths-native-test.log, v12 captures, private session data
and temporary installation fixtures with their own INI files, catalog births,
images, tables and memo sidecars. Test RAM mounts are released; disk fixtures
are retained. Clean clones need the uncommitted files and installed Windows
toolchain/dependencies. The preview owns its independent interactive session.

Final inventory: 169 owned dirty paths across the Workbench slices; 7,157 shared
dirty paths left untouched; no owned staging; 37 retained phase temporary
directories. The existing .pytest_cache traversal permission warning is recorded.
Branch and HEAD match preflight. Preview process 63312 reported ArcticTalk
Workbench and Responding=True. Source DBF/DTX hashes were rechecked after
opening the preview and still match above. CODEX-20260918-UIDEF-PATHS checked
out after verification and closeout.
