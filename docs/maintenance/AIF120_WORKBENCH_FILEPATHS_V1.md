# Workbench M1 follow-up - deterministic file locations

Run: CODEX-20260918-UIDEF-FILEPATHS.
Owner authorization: remove fallback searching, assign file types to directories,
and start modal pickers in those directories (2026-09-18).
Status: implemented and verified locally on Windows; uncommitted.

Preflight targets: src/cli/shell_api.cpp/.hpp, cmd_dotscript.cpp,
cmd_workspace.cpp; gui/uidef/author_workbench.py, wx_workbench.cpp,
workbench_session.hpp/.cpp, workbench_paths_test.cpp, workbench_m1_test.py,
verify_workbench.py, WORKBENCH.md; this closeout and owned run/proof fragments.

Expected behavior: a top-level bare DO name resolves only in SET PATH SCRIPTS,
defaulting to DATA/scripts. Qualified relative DO paths are DATA-relative;
absolute paths are exact. A subscript resolves relative to its calling script,
with no fallback. WORKSPACE file LOAD/SAVE uses WORKSPACES for bare names,
DATA for qualified relative paths, and exact absolute paths. The established
.dtschema then .dtschemas extension preference stays within that one location.
Do not substitute a file from cwd, tests or a user/public directory.

Add a generated Run script modal, initialized from SCRIPTS and filtered to .dts,
with the full selected path and destination workspace visible before execution.
DBF directories/tables use DBF; workspace definitions and MINIDB files use
WORKSPACES; SCHEMAS remains the separate table-schema location. Existing SET
PATH overrides remain authoritative. No file relocation or data changes.

Proof plan: native duplicate-name and missing-file sentinels, cwd independence,
explicit paths with spaces/ampersand, sibling subscript resolution, stale target
and modal cancellation; actual generated wx dialog dispatch plus existing suite.
Build a separate arctictalk_workbench_filepaths.exe; retain previous previews.
No staging, commit, push, branch change, promotion or cleanup authorized.

Compatibility boundary: this pass changes DO/DOTSCRIPT and WORKSPACE file
loading. ERSATZ's separate user/public/default policy and the regression
runner's explicit script inventory are not redesigned here.
TEST also uses the shared shell script helper and inherits its deterministic
location rule; this pass does not introduce a separate TESTS-directory default.

Measured findings during verification:
- The cli/path_resolver.hpp spelling is an existing compatibility shim, not a
  missing header. The defect was existence-dependent fallback after SCRIPTS.
- The native library and new Workbench executable compiled. The first native
  path assertion compared a mixed-separator fixture string with a canonical
  Windows path. The workspace assertion had the same issue after RESET
  normalized its path state. Both checks now compare canonical paths; the
  failure transcripts already showed the intended file/refusal location.
- Quoting must survive until OUT/OUTPUT parsing. Otherwise a selected filename
  containing " OUT " can be interpreted as a transcript clause. The native
  runner now preserves quoting through that stage; a dedicated fixture verifies
  exact execution as well as ordinary OUT transcript creation.

## Delivered and verified

- DO/DOTSCRIPT now resolves a single file and prints its full path when running
  or missing. No cwd/scripts/tests candidate list remains.
- Native WORKSPACE file LOAD/SAVE follows the file-kind root, with no cwd
  substitution. Existing absolute modal paths retain their meaning.
- Run script is available beside Run command and under Tools (Ctrl+R). Its
  generated modal starts in SCRIPTS, filters .dts, shows the current workspace,
  and submits an exact selected path once after validation. The worker checks
  workspace identity again and invokes the native runner without interpreting
  the filename as command-box macros.
- Eight native programs and the design check pass. Native fixtures cover
  duplicate filenames in scripts/tests/cwd/user/public, no fallback on missing
  files, SET PATH overrides with spaces, DATA-qualified paths, sibling scripts
  and missing siblings, literal ampersand/OUT filenames, transcript output,
  stale modal targets and workspace definition loading with Ada field readback.
- All sixteen native window modes pass. M1 now exercises twenty-three generated
  modal lifetimes, including Run script default-directory, invalid input,
  Cancel/Escape/window close and Enter execution. Existing image hydration,
  editing, save/export/store, navigation and shutdown checks still pass.
- The source WORKSPACES.dbf and WORKSPACES.dtx SHA-256 hashes were unchanged
  across verification. Run modal and native menu captures were inspected.

Executable: D:\code\ccode\build\uidef-native\Release\arctictalk_workbench_filepaths.exe
SHA-256: 45a71f46101c7f715a978230a335c21034d4a9e72b5a26edaeecdd3cd333fd63

[Native/window evidence](evidence/AIF120_workbench_filepaths_20260918.txt).
[Run script modal](evidence/AIF120_workbench_20260918_filepaths-modal-RUN.png).
[Native menus and command row](evidence/AIF120_workbench_20260918_filepaths-menus.png).
[Housekeeping inventory](evidence/AIF120_workbench_filepaths_housekeeping_20260918.txt).

Reproduce from D:\code\ccode with .venv312\Scripts\python.exe -B:
gui\uidef\build_workbench.py --output-name arctictalk_workbench_filepaths,
then gui\uidef\verify_workbench.py --output-name arctictalk_workbench_filepaths.
The window verifier requires an interactive Windows desktop for modal focus.

## Limits and next-session state

This updates shared DotTalk++ source as well as the Workbench. Existing running
programs keep their old code; a normal dottalkpp rebuild includes these source
changes. No existing executable was overwritten or source data moved. Windows
runtime verification only; native file pickers use wx and are entered by the
user, while automated checks set private fixture paths in the generated form.
The broader ERSATZ search policy is explicitly outside this correction.

Filed in the existing owned AI Portal run and a dedicated proof fragment.
Source, documentation and evidence remain uncommitted; no promotion,
publication or lane closure. The isolated build uses existing VS/CMake/Python
and build/uidef-deps; no new packages or persistent environment changes.
Private test directories and build residue are inventoried, not swept.

Good-neighbor record for maintainer transcription:
WHAT_CHANGED: Deterministic native DO and WORKSPACE file locations, literal
quoted script filenames, generated Run script modal and private verification.
WHOSE_AREA: AIF-120 Workbench and shared CLI path resolution; owner member.derald,
steward member.ai.claude.cowork. ERSATZ/common search-root policy untouched.
AUTHORIZATION: Owner requested removal of fallback search and file-kind modal defaults.
VERIFY_OR_UNDO: Use the build/verifier above. Undo only this follow-up's hunks;
the before-file snapshot in build/uidef-native/filepaths-before identifies them.
Do not replace whole dirty files or undo earlier workspace-navigation work.
