# AIF-120 Workbench: shared command console and Enter-to-run

Status: locally built and verified on Windows; source and evidence uncommitted.
Run: CODEX-20260917-UIDEF-LIST. Owner: member.derald.

The owner's screenshot shows `list` rejected by the frontend's three-command
allowlist, with DEFAULT holding zero areas. The commissioned Workbench needs
the actual LIST behavior: no-table feedback in this state, real row output after
selection. The owner subsequently clarified: "most command should be wired to
work". That widens this continuation to the canonical shared command executor,
with terminal/UI-owner exceptions. The three-command allowlist is removed.

Mutation preflight: gui/uidef/workbench_session.cpp, wx_workbench.cpp,
workbench_session_test.cpp, CMakeLists.txt, WORKBENCH.md, and owned
evidence/registry/closeout fragments. Additional authorized prerequisites:
root CMakeLists.txt, cmake/AddUidefWorkbench.cmake, shell_api.hpp,
shell_engine.cpp, shell.cpp, command_registry.hpp/.cpp, author_workbench.py,
build_workbench.py and verify_workbench.py. The root command target's source
inventory and libraries are reused in an object runtime; prompt and host bind
their existing engine to the same command adapters. The registry's optional
execution guard defaults to unset for the CLI. Host Enter uses Run command's
action. cmd_area.cpp, APPGUI and the parallel samples remain unchanged.

Proof plan: lowercase LIST with no table, usage with no table, actual field
values, TOP limit, FOR filtering and malformed-predicate refusal, retained
workspace/area identity, unchanged sources, and generated-window Enter event
through to real LIST output; representative reads, writes, queries, expressions,
script replay and exit on private fixtures. Re-run MINIDB and session checks,
build the regular CLI to verify the extracted engine binding. All are local.

## Delivered behavior

The command allowlist is removed. Action::Command calls shell_execute_line on
the same engine that owns the displayed workspaces, areas and hydrated RAM files.
The root's DEVELOPMENT/LMDB command inventory supplies the runtime. Object
linking preserves units with static registration; the measured registry contains
310 command/function names, including aliases. This is wiring coverage, not a
claim that every command's semantics were exhaustively tested.

The host installs the normal builtins, loop executor and relation engine binding.
stdout and stderr are captured on the worker. Console reads receive EOF. An
optional registry guard refuses terminal browsers, other frontend owners, host
shell `!`, console CLEAR and blocking BBS SERVE. The guard runs on actual
dispatch, including macro and script expansion. It is unset for the regular CLI.
HIER and PSHELL are admitted: source inspection established that these are
hierarchy operations and reference output, respectively, not terminal owners.

Enter and Run command share the same action. Up/Down recalls 200 commands.
Monospaced output scrolls horizontally, is captured up to 4 MiB, and displays
up to 5,000 lines with explicit truncation notices. QUIT/EXIT request ordinary
window shutdown. The window and exit commands refuse closure with buffered
edits; COMMIT or ROLLBACK resolves them. A running command finishes before close.

Catalog inspection and Open table copy retain their copy behavior. Commands
such as USE operate on the paths the user chooses and edits are real; the old
global source-unchanged label was removed. Interactive multiline block capture
is not exposed; complete DOTSCRIPT files use the existing interpreter.

## Measured verification

Evidence: evidence/AIF120_workbench_console_20260917.txt and the v4 PNG family.

- Catalog, live-session and MINIDB native tests passed (3/3).
- Commands exercised: LIST empty/usage/rows/TOP/FOR/malformed predicate,
  SWITCH and SELECT number/name/qualified name, WORKDESK, expressions,
  SET VAR/macros, COUNT, GO/SKIP/DISPLAY, persistent filters, SQLSEL, TABLE,
  buffered REPLACE, dirty QUIT refusal, ROLLBACK, COMMIT, APPEND, DELETE ALL,
  RECALL ALL, DOTSCRIPT, unknown-command feedback, HIER/PSHELL usage and QUIT
  request lifecycle. Script and macro BROWSE refusals were verified.
- Generated-window checks passed for Enter-to-LIST, history key events, dirty
  close veto, rollback, saved catalog, image hydration, nested image selection,
  and close during a read. The final live screenshot was visually reviewed.
- The actual catalog retained 134 records, excluded 148 deleted records and
  contained seven valid images. All seven hydrated into 97 simultaneously open
  tables. No nested objects were present in that catalog; the native DBF/DTX
  fixture and generated window proved live nested-image behavior separately.
- Original WORKSPACES.dbf and WORKSPACES.dtx SHA-256 values stayed unchanged.
  The tested generated executable SHA-256 is
  023228b34021c216c322ce113915660d68df9465e65fe988f5abf38e049cc211.
- The regular dottalkpp target built from the same root configuration and its
  --help smoke passed. This is not a full CLI regression-suite claim.
- Shared source diff checks passed; src/cli/cmd_area.cpp has no diff.

Windows was tested; Linux/macOS were not. External tools and existing engine
command prerequisites still apply. Terminal BROWSE is not a native grid yet.
The next useful increment is table/memo browsing alongside this console.

## Housekeeping and handoff

Builds are isolated in build/uidef-native; old build/uidef-workbench is retained.
Dependencies are in build/uidef-deps. nlohmann-json and SQLite were restored from
the existing vcpkg cache for the full runtime. No package was added to the shared
build/vcpkg_installed tree. Private session copies, fixture residue and build logs
are inventoried in evidence/AIF120_workbench_console_housekeeping_20260917.txt.
Temporary verifier marker directories were removed by that verifier itself.

The branch remains development at b63606ec113edca7b7fc2986074b390cfb645817.
The inventory lists every dirty path as owned (including previous Workbench
slices) or shared and untouched; shared authors are not inferred. All source,
evidence and registration remain uncommitted. No staging, git mutation,
publication, APPGUI replacement or lane closure was performed. Existing sample
frontends remain available. Build/visible-capture runs used approved SDK access;
only the existing VCPKG_ROOT locator is needed beyond installed build tools.

RE: AIF-120 and runtime/build owners -- for maintainer transcription

WHAT_CHANGED: generated Workbench command host, input/output and tests; optional
root build composition; non-owning shell engine binding and optional command
registry admission callback; guide, owned evidence and registration fragments.

WHOSE_AREA: AIF-120 generated frontend and shared CLI/build integration; owner
member.derald, steward member.ai.claude.cowork.

AUTHORIZATION: Owner commissioned and continued the Workbench, requested engine
dogfooding, and explicitly directed that most commands should be wired to work.

VERIFY_OR_UNDO: Run gui/uidef/build_workbench.py then verify_workbench.py with
the documented Python/toolchain. The regular prompt build is
cmake --build build/uidef-native --config Release --target dottalkpp.
Undo only this continuation's named paths/hunks, preserving previous Workbench
work and the unrelated dirty tree. No reset or whole-file revert of shared work.

Final interactive preview opened from build/uidef-native/Release/arctictalk_workbench.exe
(PID 19804 at handoff). Coordination run CODEX-20260917-UIDEF-LIST checked out.
