# DotTalk++ Open Architecture GUI Plan v1

Status: planning and skeleton boundary.

Related planning artifacts:

- `../ui/CORE_UI_PRINCIPLES_V1.md`
- `../ui/UI_LANE_TRADEOFFS_V1.md`
- `GUI_RUNTIME_FACADE_PLAN_V1.md`
- `GUI_SYNC_DEVELOPMENT_WORKFLOW_V1.md`
- `GUI_THREADING_EVENT_MODEL_V1.md`
- `UNIFIED_GUI_CORE_V1.md`
- `WINDOWED_APP_CONTRACT_V1.md`
- `WX_FRONTEND_PLAN_V1.md`
- `PYTHON_FRONTEND_PLAN_V1.md`
- `GUI_BUILD_AND_RUN_V1.md`
- `../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `../database/DATABASE_SAFETY_CONTRACT_V1.md`

## Intent

DotTalk++ should support real windowed desktop GUIs without making the core runtime depend on a particular GUI toolkit. The first compiled C++ frontend is wxWidgets because it gives a conventional native desktop interface on Windows, Linux, and macOS while remaining compatible with the existing C++ and CMake shape of this repository. A Python desktop frontend is also a valid first-class lane for fast iteration, scripting-oriented workflows, and `pydottalk`-backed tools.

The GUI must be an optional product, not a replacement for the command-line runtime or the Turbo Vision TUI. All UI lanes should share the same work-area, command, snapshot, status, and task concepts, then branch only where the UI medium has a real advantage.

The windowed GUI must also honor the database contracts. It should not treat
locale, encoding, collation, index validity, read-only safety, or mutation
boundaries as later visual polish.

## Top-Down GUI Rule

DotTalk++ has grown database capability bottom-up: xbase records, indexes,
commands, scripts, metadata, and validation first. The windowed GUI should grow
top-down: define the workbench experience first, then attach it to stable
DotTalk++ services as they mature.

This does not mean inventing a separate GUI database. It means the GUI starts
from product concepts users can see:

- a workbench,
- a workspace graph,
- areas,
- browse/list/tuple/projection views,
- command and script lanes,
- diagnostics and task results,
- language, region, encoding, collation, and safety inspectors.

The CLI/runtime remains the authority for database behavior. The GUI openarch
adapts current frontends around that authority:

- wxWidgets is the primary native desktop shell for visible workbench shape,
  menus, grids, dialogs, and OS integration.
- Python/Tkinter is a first-class scripted workbench lane for fast experiments,
  inspection tools, and binding/pydottalk proofs.
- The CLI is the stable command/script service and transcript authority.
- The TUI remains a terminal-first lane with the same concepts where practical.

Therefore, GUI progress can be intentionally top-down while database behavior
continues to be served bottom-up by DotTalk++ runtime services. When a GUI
feature lacks a mature service, the GUI may expose a skeleton or bridge to the
CLI, but it should not fork semantics inside widget code.

## Product Targets

| Target | Role | Dependency boundary |
| --- | --- | --- |
| `dottalkpp` | Existing CLI/runtime executable | No GUI dependency |
| `dottalk_gui_core` | GUI-neutral session, task, and model layer | No wxWidgets, Qt, FLTK, or platform GUI headers |
| `dottalk_wx` | First windowed GUI frontend | May depend on wxWidgets and `dottalk_gui_core` |
| Python GUI | First-class scripted desktop frontend | May depend on Tkinter and `pydottalk`; must remain runtime-contract driven |
| `dottalk_tvui` | Existing Turbo Vision/TUI layer | Separate from windowed GUI |
| `pydottalk` | Python binding surface | Shared runtime bridge for Python GUI and automation |

The shared principles for CLI/TUI/Python/C++ UI behavior live under `docs/ui`.

## Boundaries

- No wxWidgets, Qt, FLTK, Win32, Cocoa, GTK, or X11 types in `xbase`, `memo`, `xindex`, `xexpr`, DotScript execution, or shared command services.
- GUI frontends must call GUI-neutral services instead of reaching into shell globals directly.
- Worker threads must never touch GUI widgets.
- The GUI must be opt-in at configure time.
- The existing CLI build must remain unchanged when GUI options are disabled.
- UI language, display locale, parse locale, table encoding, and index collation
  identity must remain separate concepts.
- The first windowed inspection path should be read-only until edit safety,
  locking, validation, and recovery are explicitly designed.

## Layering

```text
Windowed frontends
  wxWidgets frames, menus, dialogs, grids, status bars
  Python/Tkinter windows, grids, logs, workflow tools

GUI adapter
  Translates toolkit events into GUI-core requests
  Translates GUI-core events into toolkit-safe UI updates

GUI core
  Session manager
  Task queue
  Command/DotScript runner facade
  Table snapshot models
  Progress, log, error, and cancellation contracts

Existing runtime
  xbase / memo / xindex / xexpr
  DotScript and command execution
  import/export, metadata, help, and table services
```

## Service Maturity Ladder

Every visible GUI feature should identify which service level currently owns it:

| Level | Owner | GUI behavior |
| --- | --- | --- |
| Product shell | Frontend adapter | Menus, panes, layout, keyboard focus, result windows |
| GUI core model | `dottalk_gui_core` / Python mirror | Areas, snapshots, tasks, events, status messages |
| Compatibility bridge | DotTalk++ CLI process | `DO`, `DOTSCRIPT`, `SCAN`, `LOOP`, `VAR`, command transcript |
| Native runtime service | DotTalk++ runtime facade | Structured workspace, relation, index, projection, validation actions |
| Durable database authority | xbase/memo/xindex/xexpr and metadata contracts | Record/index/value/locale/safety truth |

The current wx executable is allowed to be more visible than the underlying
native GUI services. That is useful. The constraint is that visible shell code
must either call the shared GUI core, call the CLI bridge, or mark the action as
a skeleton. It must not silently create a wx-only version of DotTalk++ behavior.

## Threading Contract

The GUI architecture uses one UI thread and one or more worker threads.

- UI thread owns all widgets and processes toolkit events.
- Worker threads run long operations: opening tables, scanning records, running DotScript, indexing, importing, exporting, metadata checks, and report generation.
- Workers communicate by posting immutable events back to the GUI adapter.
- Cancellation is cooperative. Long operations receive a cancellation token and must check it at reasonable boundaries.
- Progress is structured, not scraped from console text.

Core event types should include:

- `TaskStarted`
- `Progress`
- `LogLine`
- `TableSnapshotReady`
- `CommandFinished`
- `Error`
- `TaskCancelled`

## Initial UX Scope

The first useful GUI should be small but real:

- Main window with menu, toolbar, status bar, and split panels.
- Workspace/table browser panel with visible GUI work areas.
- Command input panel.
- Output/log panel.
- Open DBF action.
- Run command or DotScript action.
- Background task progress and cancel.
- Read-only table grid snapshot.

Current wx skeleton behavior: opening a table creates a new GUI work area instead
of replacing the previous one. The left Areas panel lets the user switch between
open tables and refresh the grid for the selected area.

Editing, relation visualization, schema designers, help browsers, and metadata dashboards should come after the read-only shell is stable.

## Build Plan

Add opt-in build switches:

```cmake
option(DOTTALK_WITH_GUI "Build GUI-neutral application services" OFF)
option(DOTTALK_WITH_WX "Build wxWidgets windowed GUI frontend" OFF)
```

The first implementation phase should create only `dottalk_gui_core`. It must compile without wxWidgets. A later phase can add `dottalk_wx` after dependency discovery and packaging rules are agreed.

## Phase Plan

### Phase 1: Boundary and Skeleton

- Add this plan.
- Add `src/gui/core` with toolkit-neutral session/task/result types.
- Wire `dottalk_gui_core` behind `DOTTALK_WITH_GUI`.
- Do not add wxWidgets yet.
- Do not modify CLI behavior.

### Phase 2: Runtime Facade

- Add a GUI-safe session facade around table open, command execution, and table snapshot generation.
- Avoid stdout/stderr capture as the primary data contract.
- Add structured results and errors.

### Phase 3: wxWidgets Frontend

- Add `src/gui/wx`.
- Build `dottalk_wx` only when `DOTTALK_WITH_WX` is enabled and wxWidgets is found.
- Prove the app opens, starts a background task, posts progress, and displays a read-only table snapshot.

### Phase 4: Python Frontend

- Promote `tools/gui_preview` from preview into a maintained Python GUI lane.
- Prefer `pydottalk` for runtime access, with pure-Python read-only fallback for bootstrap visibility.
- Keep Python GUI workflows aligned with the same session/event/snapshot contracts used by C++ frontends.

### Phase 5: Top-Down Workbench Growth

- Keep wx as the visible workbench shell while the runtime facade matures.
- Add menus and panes for workspace, areas, projections, scripts, diagnostics,
  and inspectors before every action has native implementation.
- Route mature actions through GUI core services.
- Route command/script families through the CLI bridge.
- Keep skeleton actions explicit and named as pending service work.

### Phase 6: Broader GUI Features

- Table editing through explicit service calls.
- DotScript run history.
- Metadata and help panels.
- Relation/browser visualization.
- Import/export workflows.

## First Technical Risks

- Existing command execution has CLI globals and stream-oriented behavior. The GUI should introduce structured service calls rather than depend on console capture.
- Database area ownership must be explicit. The GUI core should not expose raw mutable `DbArea` pointers across threads.
- Locale-sensitive values and indexes need explicit context. The GUI should
  surface unknown encoding and stale/incompatible collation/index state instead
  of hiding it behind grid text.
- Write workflows need explicit safety boundaries. The presence of a grid must
  not imply editing is safe.
- Long-running operations need cancellation points before they are safe in a desktop app.
- The build currently globs most of `src`; `src/gui` must stay excluded from the CLI glob just like `src/tv`.
