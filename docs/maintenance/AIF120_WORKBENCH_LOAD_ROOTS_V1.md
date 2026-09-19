# Workbench M1 follow-up - schema table locations

Run: CODEX-20260918-UIDEF-LOADROOTS.
Authorization: owner reports mcc.dtschema and help.dtschemas fail to load.
Status: implemented and verified locally on Windows; uncommitted.

Measured: both are DTSHEMA 2 definitions containing bare DBF filenames and no
DBFROOT/IDXROOT. The native loader correctly uses current DBF/INDEXES settings
for such definitions; the screenshots show DBF resolving to workspaces. The
Load modal hid those settings. MCC has multiple real table families; its
mcc.erz preset names x32. All ten help tables exist under data/help. Do not
guess another directory, silently choose x32/x64, or rewrite these definitions.

Preflight targets: src/cli/cmd_workspace.cpp; new
include/cli/workspace_definition.hpp; gui/uidef/workbench_session.hpp/.cpp,
author_workbench.py, wx_workbench.cpp, workbench_paths_test.cpp and verification
scripts; guide, milestone pointer and owned run/proof/evidence records.

Behavior: Load shows the table and index directories, initialized from the
native path slots, with explicit directory pickers. Saved roots in a definition
keep native precedence. A shared native preflight checks all declared tables
before the form accepts. Missing-table errors stay in the form. The worker
rechecks on execution and applies chosen defaults for this load only, restoring
native path settings on every exit. Existing v3 and MINIDB behavior is retained.

Proof: private V2 fixture with duplicate table names and wrong/right roots,
preflight with no mutation, missing-member refusal, v3 saved-root precedence,
restored defaults, actual table readback; load private copies of the owner's MCC
and Help families using the actual schema bytes; generated modal validation and
existing window suite. Preserve source schemas/data and previous previews.
No git mutation, publication, branch change or shared cleanup authorized.

## Delivered

Load has explicit Table directory and Index directory fields and separate
directory pickers. Missing-table errors remain inside the modal so the user can
correct the location and retry; the form does not close or submit a load.
The check runs on the existing engine worker through a read-only native API,
sharing the loader's version parser and member resolver. The loader repeats its
normal preflight at execution. Saved roots override the chosen defaults.

The worker independently checks the request and scopes DBF/INDEXES changes to
one load, restoring native path state on success or exception. This does not
rewrite schemas, move tables, or add a directory search. Command-box LOAD
continues to use its explicit native SET PATH settings.

For the original mcc.dtschema (CNX), the measured existing mcc.erz preset chooses
x32: tables in DATA/dbf/x32, indexes in DATA/indexes/x32. For help.dtschemas,
all ten tables are in DATA/help and the definition declares no indexes.
Other families must be chosen explicitly; x32/x64 is not guessed from existence.

## Verification

- CMake build and all nine registered tests passed. The focused V2 fixture
  proves wrong-root refusal without mutations, correction to a chosen root,
  exact Ada field readback, v3 saved-root priority and restoration of defaults.
- The actual source schema bytes were used with private copies of their table
  families. MCC loaded 12 of 12 tables; native output also reports all 15
  relations restored and CNX tags read. Help loaded 10 of 10 tables. The test
  selects and reads rows from every loaded table (22 tables with rows read).
- Source schemas and every copied source-family file were hashed before and
  after, unchanged. Source files were never opened by the native load test.
- The design check and all sixteen native window modes pass. The Load modal
  exercises a missing member, retains the form/error, corrects its table root,
  accepts Enter, and reads the loaded value. The run retains the other M1
  cancellation and focus cases (23 modal lifetimes).
- Full verification leaves WORKSPACES.dbf and WORKSPACES.dtx hashes unchanged.
  The captured Load form was inspected; fields, Browse controls and the missing
  member message are visible without overlap.
- One proof-harness error was corrected: its success text was printed before
  the Workbench released its captured output stream, producing no external
  marker. It now prints after shutdown. The verifier rejected the empty output;
  it was not accepted as proof.

Executable: D:\code\ccode\build\uidef-native\Release\arctictalk_workbench_loadroots.exe
SHA-256: 54f84e1e053050775cc2d811595738aeb66abad40207ad4be4e26cbb54cc8756

[Real MCC/Help proof and source hashes](evidence/AIF120_workbench_loadroots_real_20260918.txt).
[Native/window suite](evidence/AIF120_workbench_loadroots_20260918.txt).
[Load modal](evidence/AIF120_workbench_20260918_loadroots-modal-LOAD.png).
[Housekeeping inventory](evidence/AIF120_workbench_loadroots_housekeeping_20260918.txt).

Reproduce from D:\code\ccode, using .venv312\Scripts\python.exe -B:
- gui\uidef\build_workbench.py --output-name arctictalk_workbench_loadroots
- gui\uidef\verify_workspace_schema_load.py
- gui\uidef\verify_workbench.py --output-name arctictalk_workbench_loadroots

The real-schema proof needs the local MCC x32/CNX and Help families. Window
proof requires an interactive Windows desktop. Cross-platform runtime proof,
full relationship navigation and normal APPGUI integration remain outside this
M1 correction. Shared native source is changed; existing binaries need rebuilding.

## Closeout and good-neighbor record

Filed under the existing owned AI Portal run and a dedicated proof fragment.
Source and evidence are uncommitted; no promotion, publication or lane closure.
The isolated VS/CMake/Python build reuses build/uidef-deps. No packages installed
or persistent settings changed. Previous previews remain available. Retained
private session directories and build residue are inventoried; no shared cleanup.

WHAT_CHANGED: Read-only native schema preflight, generated Load directory
controls and validation, scoped per-load defaults, fixture and real-schema proof.
WHOSE_AREA: AIF-120 Workbench and shared CLI workspace loading; owner
member.derald, steward member.ai.claude.cowork.
AUTHORIZATION: Owner reported failed MCC and Help schema loads and requested correction.
VERIFY_OR_UNDO: Run the commands above. Undo only this follow-up's hunks and
new artifacts; build/uidef-native/loadroots-before records the starting files.
Preserve earlier native navigation/path work and concurrent dirty files.
