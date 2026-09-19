# Workbench M1 - native menus and modal workflow

Run: CODEX-20260918-UIDEF-M1. Owner authorization: "begin m1".
Status: M1 locally complete on Windows; source/evidence uncommitted.

Preflight: gui/uidef/author_workbench.py, uidef_wx.py, manifest.py,
wx_workbench.cpp, workbench_session.hpp/.cpp, Workbench tests/verification,
WORKBENCH.md, milestone plan and owned run/proof fragments.
Reuse R18 menu Container/item hierarchy and R144 Modal property on form.
Generated modal factories share the existing runtime without replacing its
frame scope. The host owns each dialog until ShowModal returns, then destroys
it; system pickers remain host capabilities. Capture and revalidate workspace
identity, submit once after validation, and leave engine state unchanged on
Cancel. Keep native defaults and existing action wrappers.

Proof plan: generated menu dispatch; repeated modal lifetime; accept/cancel,
Escape/Enter/focus, invalid input, stale target and private root/child/peer
fixtures with paths containing spaces; existing native and window suites.
Build arctictalk_workbench_m1 separately. Record measured results and captures.
Preserve shared dirty work, live databases, CLI, samples and prior previews.
No staging, commit, push, branch change, publication or cleanup authorized.

Additional scoped targets: uidef.py and the Tk/HTML/text entry points explicitly
refuse unsupported modality; CMakeLists.txt registers the M1 design check.

Verification findings as work proceeds:
- The first modal capture timed out: PNG handlers were initialized only in the
  final frame capture. Initialize them at host startup so earlier dialog captures
  cannot open a toolkit error box. The timed-out private smoke was terminated by
  its subprocess timeout; no user session was involved.
- Native OPEN's tokenizer does not honor quoted whitespace paths. The host uses
  the native DBF path slot for the operation and restores it on success/exception;
  it does not alter the shared CLI parser or persist a new default.
- This Python runtime lacks _tkinter. Tk's Modal refusal now occurs before that
  optional import; no Tk rendered-window proof is claimed. HTML/text also refuse
  modality explicitly instead of silently flattening the forms.
- Create standard button IDs at native construction, rather than changing them
  afterward. The first keyboard assertion also tested IsModal too early: wx/MSW
  retains modal data until ShowModal unwinds. Check the EndModal return code in
  the callback, then engine state/focus after return. A direct MSWProcessMessage
  probe also bypassed the wx key-hook path. Forms now route their wx key hook
  explicitly to standard result events, including nested panel controls. Tests
  exercise that hook, never global desktop keystrokes.

## Delivered

Six native menu headings (File, Workspace, Table, View, Tools, Help), generated
from the existing R18 menu hierarchy. Handlers are shared with the buttons.
New/Open/Load/Save forms are authored in WORKBENCH.DBF, with Modal on form,
DialogResult on accept/cancel buttons, captured destination identity, native
defaults, inline validation and system pickers. Enter and Escape follow the same
result/validation path as buttons. The host owns the dialog through ShowModal,
destroys it after return, then restores valid focus. It does not replace the
frame runtime/scope. A request is submitted only after acceptance.

NEW enters its new root or child. OPEN uses the selected directory through native
OPEN dbf without persisting a different default. LOAD uses native schema roots
and cursor behavior. SAVE supports per-operation nested scope, restores the
recursion default, refuses stale workspace identity, existing destinations,
transactions and buffered edits in the saved scope. Peers and their buffers remain
independent. Advanced OPEN index options remain available in the command box.

Executable: D:\code\ccode\build\uidef-native\Release\arctictalk_workbench_m1.exe
SHA-256: e5564f4eca23113c5df48951aabc9a78a7f85dbe66de4bbf3f7245022205da3a

## Verification

- Eight native test programs passed, including directory paths with spaces,
  actual Ada field readback, invalid/missing/incomplete schemas, stale current
  workspace and parent, child activation and duplicate-submit refusal.
- Modal save test proves nested scope with a pending peer buffer, restores the
  recursion default, and writes no output on stale-target refusal. Existing
  save tests retain buffered-edit, transaction and overwrite refusal coverage.
- M1 design check passes directly and as CTest test 9: four modal definitions,
  nested menu hierarchy/mnemonics/keys, malformed-menu refusal and explicit
  Tk/HTML/text modal refusal. The generated document has 209 rows / 208 objects,
  with no author conformance findings or wx generation notes.
- All 16 window modes pass. M1 opens 19 actual generated dialogs: invalid input,
  Cancel, Escape, window close, focus restoration, Enter acceptance, root/child/
  peer creation, Open, Load with spaces/ampersand, and one-/two-table saved images.
  The test proves no mutation after cancellation by observing native state.
- Source WORKSPACES.dbf and WORKSPACES.dtx hashes were unchanged across the full
  verifier. No source data, native defaults, shared CLI parser or samples edited.
- Native menu and four dialog captures inspected. Menu capture includes native
  menu/client content; the desktop compositor does not supply reliable title-bar
  pixels to WindowDC, so it is not evidence about window chrome.

[Full native/window evidence](evidence/AIF120_workbench_m1_20260918.txt).
[Native menus](evidence/AIF120_workbench_20260918_m1-menus.png).
[New](evidence/AIF120_workbench_20260918_m1-modal-NEW.png),
[Open](evidence/AIF120_workbench_20260918_m1-modal-OPEN.png),
[Load](evidence/AIF120_workbench_20260918_m1-modal-LOAD.png),
[Save](evidence/AIF120_workbench_20260918_m1-modal-SAVE.png).
[Housekeeping inventory](evidence/AIF120_workbench_m1_housekeeping_20260918.txt).

Reproduce: .venv312\Scripts\python.exe -B gui\uidef\build_workbench.py
--output-name arctictalk_workbench_m1, then .venv312\Scripts\python.exe -B
gui\uidef\verify_workbench.py --output-name arctictalk_workbench_m1.
The M1 window check requires an interactive desktop, even without captures.

## Limits and handoff

Windows runtime proof only. Modal forms require top-level form rows and wx;
menus attach directly to a form and use container/item nesting. Other GUI
targets explicitly refuse Modal. Keyboard proof drives wx key hooks, not global
OS keystrokes. Ordinary system file/directory pickers use wx host dialogs;
automated tests enter fixture paths directly in the generated forms.
Full nested ownership restoration, richer table navigation, portability and
normal APPGUI launch integration stay in M2-M7. Existing previews and samples
remain intact. No claim of commit, promotion, publication or overall lane closure.

Filed in the AI Portal's owned AIPR-20260917-001 run and M1 proof fragment.
All evidence and source remain local until maintainer staging/commit. Dependencies
are the existing isolated build/uidef-deps and installed VS/CMake/Python; no new
packages, persistent environment settings or permissions. Build/test scratch and
private session catalogs/images are listed in the housekeeping inventory; no
shared cleanup performed. The regression harness remains another owner's scope.

Good-neighbor record for maintainer transcription:
WHAT_CHANGED: M1 generated native menus/modal forms, shared host actions,
workspace identity checks, per-save nested scope and verified window workflows.
WHOSE_AREA: AIF-120 / project.x64base.gui; owner member.derald, steward
member.ai.claude.cowork. Shared generator edits are limited to the named behavior.
AUTHORIZATION: Owner requested "begin m1" after accepting the milestone plan.
VERIFY_OR_UNDO: Use the commands above. Undo only M1 hunks and named new artifacts;
preserve previous Workbench work and all shared dirty files. No git mutation.
