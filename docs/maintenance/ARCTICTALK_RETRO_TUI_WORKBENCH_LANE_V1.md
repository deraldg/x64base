# ArcticTalk Retro TUI Workbench Lane v1

Status: active prototype lane; implementation inventory and runtime proof pending.
Opened: 2026-07-22.
Intake: AIF-049.
Parent project: `project.x64base.runtime`.
Lane id: `arctictalk_tui_workbench`.

## Purpose

Flesh out ArcticTalk as the retro text-user-interface member of the
DotTalk++ Workbench family without creating a second runtime truth or forcing a
terminal interface to imitate a graphical interface.

ArcticTalk is a pet-project workbench with its own retro character. It is also
a real frontend over DotTalk++ state and commands. The lane therefore protects
both experimentation and backend correctness.

## Workbench Family

| Workbench | Role | Primary anchors | Synchronization rule |
| --- | --- | --- | --- |
| wxWidgets | compiled C++ GUI | `src/gui/wx`, `src/gui/core` | Must remain behaviorally synchronized with Python/Tkinter through the open GUI API and shared runtime contracts. |
| Python/Tkinter | Python GUI and visible prototype | `tools/gui_preview` | Must remain behaviorally synchronized with wxWidgets through the open GUI API and shared runtime contracts. |
| ArcticTalk | retro Turbo Vision TUI | `src/tv`, `include/tv` | Reuse runtime truth and shared contracts; adapt or diverge when terminal/Turbo Vision constraints or retro interaction make that appropriate. |

The two graphical workbenches form the required GUI synchronization set.
ArcticTalk is a sibling workbench, not a third pixel-for-pixel parity target.

## Boundary Contract

### Shared truth

All three workbenches must derive these concepts from DotTalk++ / x64base:

- areas and active-area selection;
- table, cursor, record, and deleted state;
- indexes, order, relations, and tuples;
- memo and field behavior;
- command execution and scripts;
- errors, messages, and runtime capabilities.

A frontend may format or navigate this information differently. It must not
invent conflicting runtime semantics.

### Required GUI synchronization

wxWidgets and Python/Tkinter must stay aligned at the behavioral/API level:

- the same operation has the same runtime meaning;
- state snapshots use compatible fields and identities;
- command catalog changes are reflected in both workbenches;
- unsupported behavior is explicit rather than silently different;
- parity is checked with a maintained capability matrix and shared fixtures
  where practical.

This is API and behavior parity, not widget, layout, or toolkit parity.

### Permitted ArcticTalk differences

ArcticTalk may have:

- keyboard-first workflows and Turbo Vision window management;
- terminal-sized layouts, palettes, status lines, and menu conventions;
- retro-only commands, demonstrations, shortcuts, or visual effects;
- reduced or staged presentation of graphically dense information;
- different interaction sequences when they preserve the same runtime result.

Every ArcticTalk capability must be classified as one of:

1. `shared-required` - same backend contract as the GUI synchronization set;
2. `tui-adapted` - same runtime behavior with a terminal-specific interaction;
3. `tui-only` - intentionally unique retro workbench behavior;
4. `deferred-or-unsupported` - visible gap with a reason and next gate.

`tui-only` does not authorize a separate table, cursor, index, relation,
locking, or command truth.

## Naming and Compatibility

- Public workbench name: **ArcticTalk**.
- Primary command: `ARCTICTALK`.
- `FOXTALK` remains a legacy command alias.
- Existing `foxtalk` filenames, namespaces, classes, environment variables,
  and settings paths are compatibility implementation details.
- A wholesale internal rename is outside this lane unless separately planned
  with settings, source, build, and compatibility migration gates.

## Initial Evidence State

The current UI is visibly beyond a mockup: it launches into a Turbo Vision
desktop and exposes menus, command/output/workspace windows, shortcuts, and
workbench actions. The maintainer classifies it as a **semi-functioning
prototype**.

That screenshot-level observation is not runtime proof of each menu item or
command path. Until M0 records a repeatable inventory, individual capabilities
remain `Unverified`.

Current source anchors include:

- `src/tv/cmd_foxtalk.cpp`;
- `src/tv/foxtalk_app.cpp`;
- `src/tv/foxtalk_shell_bridge.cpp`;
- `src/tv/foxtalk_menu.cpp`;
- `include/tv`;
- `src/gui/core`;
- `src/gui/wx`;
- `tools/gui_preview`.

## Milestones

### M0 - inventory and launch proof

- Record exact build and launch commands for ArcticTalk.
- Inventory every menu, window, shortcut, command route, and visible stub.
- Classify each item with the four-way capability vocabulary above.
- Retain a launch transcript and a small screenshot set.

Exit: repeatable launch plus a capability matrix that distinguishes working,
partial, stubbed, blocked, and unverified behavior.

### M1 - open GUI API and parity baseline

- Name the current open GUI API authority across `src/gui/core`, the wx
  frontend, and the Python/Tkinter bridge.
- Create the wx/Python capability-parity matrix.
- Identify direct frontend/runtime shortcuts that bypass the shared contract.
- Add or select shared fixtures for workspace, area, table, index, relation,
  tuple, command, and error-state comparison.

Exit: the two GUI workbenches have an explicit synchronization contract and a
recorded baseline; drift is visible.

### M2 - ArcticTalk shared-runtime spine

- Reconcile ArcticTalk command execution and state snapshots with shared
  runtime services where practical.
- Preserve TUI interaction while removing accidental semantic forks.
- Make unsupported nested or graphical behaviors explicit.

Exit: shared-required features have backend-equivalent outcomes or a documented
blocker.

### M3 - flesh out the workbench

- Complete the essential command, output, workspace, record, table, index,
  relation, tuple, browse, and help paths appropriate to a retro TUI.
- Replace misleading stubs with working actions or clear deferred messages.
- Keep destructive actions guarded and visible.

Exit: the core daily-use path is coherent and repeatable without claiming full
GUI parity.

### M4 - intentional retro features

- Curate palettes, keyboard navigation, menus, status/message lines, window
  layouts, demonstrations, and other Turbo Vision-native behavior.
- Mark each addition `tui-adapted` or `tui-only`.
- Keep the Arctic fox identity as presentation/mascot material, not runtime
  authority.

Exit: ArcticTalk has a deliberate identity rather than a collection of
unclassified differences.

### M5 - proof and maintenance gate

- Run scoped build and runtime checks for all three workbenches.
- Verify wx/Python API parity separately from ArcticTalk TUI acceptance.
- Register repeatable smoke/regression entry points.
- Update this lane, the AI Friendly dashboard Session Log, and any affected
  workbench documentation.

Exit: the lane can report exact proven, partial, TUI-only, and unverified
surfaces without collapsing them into one generic GUI status.

## Change Rule

For future workbench changes:

1. Decide whether the change affects shared runtime truth, the synchronized GUI
   API, or presentation only.
2. If it affects the synchronized GUI API, update or explicitly disposition
   both wxWidgets and Python/Tkinter.
3. For ArcticTalk, classify the corresponding behavior as shared-required,
   tui-adapted, tui-only, or deferred-or-unsupported.
4. Record proof per workbench; one frontend launching does not prove another.

## Non-Goals

- no forced visual parity between wxWidgets and Python/Tkinter;
- no forced feature parity between graphical and terminal workbenches;
- no separate ArcticTalk engine semantics;
- no claim that the current prototype is complete;
- no automatic publication or promotion;
- no implementation mutation merely to make documentation appear synchronized.

## Delivered Slice: Regression and Environment Menu

Date: 2026-07-22.
Status: source-defined, Release-build-proven, command-path smoke-proven;
interactive menu-selection proof pending.

ArcticTalk now exposes **Sys -> Environment / Tests**:

- Load x64 Environment (`x64.dts`) -> `DO X64`;
- Load x32 Environment (`x32.dts`) -> `DO X32`;
- List Regression Tests -> `REGRESSION LIST`;
- Run Regression Test... -> prefills `REGRESSION RUN `;
- Run All Regression Tests... -> prefills `REGRESSION ALL`.

The selected and full regression actions require explicit Enter/Run
confirmation because regression scripts may mutate session state, data, or
files. The menu uses the canonical shell executor and existing DotScript /
REGRESSION surfaces; it adds no TUI-specific runner.

Proof:

- `cmake --build D:\code\ccode\build --target dottalk_tvui --config Release`
  passed;
- `cmake --build D:\code\ccode\build --target dottalkpp --config Release`
  passed;
- a non-destructive CLI smoke confirmed `REGRESSION LIST`, `DO X64`, and
  `DO X32` on the rebuilt executable.

Observed boundary: `x32.dts` sets DBF and INDEXES to x32 but does not set LMDB;
after switching from x64, LMDB remains on the x64 path. This lane records the
existing script behavior and does not silently rewrite the environment
contract. Review that behavior separately if a fully isolated x32 LMDB profile
is desired.

## Delivered Slice: Integrated Turbo Vision Grid Browser

Date: 2026-07-22.
Status: source-defined and Release-build-proven; interactive visual acceptance
pending.
Classification: `tui-adapted`.

ArcticTalk now admits the existing `BROWSETV` implementation as an in-desktop
child window instead of rejecting it as a nested TVision application.

The corrected grid:

- opens from `BROWSETV`, Browse -> Browse Current Table, or Browse -> Turbo
  Vision Grid (All Records);
- displays record number, deletion state, and every table field;
- scrolls wide schemas horizontally with Left/Right;
- navigates visible records with Up/Down, Page Up/Page Down, Home, and End;
- visibly highlights the selected row and keeps the shared work-area cursor on
  that record;
- opens the existing read-only record window with Enter;
- toggles deleted records with `A`, reloads with `R`, and closes with Esc.

The slice repairs the pre-existing browser's missing navigation refresh and
row-highlight behavior. It does not add table editing or create a second data
access path.

Proof:

- `cmake --build D:\code\ccode\build --target dottalk_tvui --config Release`
  passed;
- `cmake --build D:\code\ccode\build --target dottalkpp --config Release`
  passed;
- scoped route inspection confirms `BROWSETV` is no longer nested-blocked and
  both Browse menu actions reach `BROWSETV` / `BROWSETV ALL`;
- scoped `git diff --check` passed.

## First Next Gate

Perform M0 as a read-first ArcticTalk audit, then build the M1 wx/Python parity
baseline before choosing implementation work. This lane charter does not itself
authorize broad source rewrites or internal renaming.
