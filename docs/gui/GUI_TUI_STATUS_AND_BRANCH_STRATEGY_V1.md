# DotTalk++ GUI/TUI Status and Branch Strategy v1

Status: active working note.

## Purpose

DotTalk++ now has three visible UI lanes:

- wxWidgets native windowed workbench,
- Python/Tkinter preview workbench,
- TurboTalk/FoxTalk Turbo Vision TUI.

This document records where the lanes stand and how they should continue
without forking database behavior away from x64base.

## Product Rule

The UI lanes are presentations over DotTalk++/x64base. They are not separate
database engines.

The database runtime owns:

- work areas,
- table open/close state,
- cursor movement,
- indexes and orders,
- relations,
- triggers and polling,
- DotScript and command semantics,
- dirty state and safety decisions,
- value, locale, collation, and encoding rules.

Each UI owns:

- layout,
- menus and command affordances,
- event-loop integration,
- rendering,
- language switching,
- output and status presentation.

When a GUI needs database truth, it should ask the runtime facade or a named
adapter. It should not recreate runtime behavior.

## Current Lanes

### wxWidgets Workbench

Primary files:

- `src/gui/wx/main.cpp`
- `src/gui/wx/main_frame.cpp`
- `src/gui/wx/main_frame.hpp`
- `src/gui/core/session.cpp`
- `src/gui/core/async_session.cpp`
- `src/gui/core/gui_runtime_adapter.cpp`
- `src/gui/core/gui_command_catalog.cpp`

Current strengths:

- Native windowed app builds with wxWidgets.
- Workspace area list is visible.
- Browse, Structure, and Workspace Graph tabs exist.
- Command/output lane exists.
- Language switching exists.
- About dialog exists.
- `WORKSPACE OPEN <dir>` can populate GUI areas and snapshots.
- `WORKSPACE ADD <dbf>` selects existing GUI area instead of duplicating.
- TurboTalk-derived command catalog now drives rich wx menus.

Current limits:

- Some behavior still mirrors CLI output rather than sharing a live CLI process
  runtime.
- Workspace Graph is still textual.
- Browse grid is read-only and not yet a full browser/editor.
- Command execution is still a compatibility bridge in many places.
- Startup/init output is noisy in the log pane.

### Python/Tkinter Preview

Primary files:

- `tools/gui_preview/dottalk_gui_preview.py`
- `tools/gui_preview/dottalk_gui_async.py`
- `tools/gui_preview/dottalk_gui_backend.py`
- `tools/gui_preview/dottalk_gui_command_catalog.py`
- `tools/gui_preview/gui_cli_bridge.py`
- `tools/gui_preview/test_gui_backend.py`

Current strengths:

- First-class Python preview lane still runs.
- Pure-Python DBF preview works when `pydottalk` is unavailable.
- Workspace area list, Browse, Structure, Workspace Graph, command lane,
  language switching, About, SCAN dialog, and lifecycle script seams exist.
- Python mirrors `WORKSPACE OPEN` and `WORKSPACE ADD` duplicate/select behavior.
- Python now has the same TurboTalk-derived command categories as wx:
  Table, Record, Index, Lists, Browse, Rel, Tuple, Cmd.

Current limits:

- It is more of a preview/mirror than a native runtime facade.
- It should eventually use bindings or a structured service instead of pure
  Python DBF fallback for production-like behavior.
- It is valuable for rapid UI proving, but cannot define runtime truth.

### TurboTalk/FoxTalk TUI

Primary files:

- `src/tv/foxtalk_app.cpp`
- `src/tv/foxtalk_shell_bridge.cpp`
- `src/tv/foxtalk_menu.cpp`
- `src/tv/foxtalk_workspace_view.cpp`
- `src/tv/foxtalk_workspace_window.cpp`
- `include/tv/foxtalk_app.hpp`
- `include/tv/foxtalk_shell_bridge.hpp`
- `include/tv/foxtalk_workspace_view.hpp`

Current strengths:

- Mature command desktop concept.
- Uses `shell_execute_line(...)` rather than reimplementing database behavior.
- Has command history, output redirection, workspace status view, layout save and
  restore, and guarded destructive actions.
- Provides the best current menu taxonomy for DotTalk++ workflows.

Current limits:

- TVision widget code should not be copied into wx or Python.
- Some command/menu surfaces remain exploratory.
- Nested TUI apps are intentionally guarded from inside TurboTalk.

## Shared Assets to Promote

These should become shared concepts, not per-frontend inventions:

- command catalog,
- command history,
- shell bridge / command runner,
- output sink,
- workspace snapshot,
- area snapshot,
- table snapshot,
- status and safety messages,
- locale/message context.

The current `gui_command_catalog` and Python mirror are the first step. The next
shared service should be a runtime-backed command runner modeled after
TurboTalk's shell bridge.

## Branch Strategy

Recommendation: continue as an integration lane in the main working tree, not as
a long-lived separate x64base branch.

Reasoning:

- The UI work depends on current x64base contracts and should discover contract
  gaps early.
- Long-lived UI branches will drift from runtime command/workspace behavior.
- The GUI/TUI code is already guarded by build options and separate directories:
  `src/gui`, `tools/gui_preview`, and `src/tv`.
- The safest separation is architectural boundaries and build targets, not a
  disconnected branch.

Use short-lived branches only for risky slices:

- replacing CLI-process bridge with in-process runtime service,
- changing workspace/area ownership,
- introducing editable grid writes,
- changing command dispatch contracts,
- adding production read-only/locking policy.

Merge those slices quickly after they build and pass focused smoke tests.

Do not keep wx, Python, and TUI on separate long-term branches. They should stay
orthogonal frontends over shared contracts.

## Recommended Near-Term Plan

1. Keep wx as the native workbench lane.
2. Keep Python/Tkinter as the rapid preview and contract mirror lane.
3. Keep TurboTalk/FoxTalk as the command taxonomy and shell-bridge reference.
4. Move shared concepts into `include/gui/core` and `src/gui/core` first.
5. Let each frontend render those shared concepts in its own toolkit.
6. Replace temporary mirrors with runtime-backed adapters incrementally.

Use `GUI_SYNC_DEVELOPMENT_WORKFLOW_V1.md` as the operating checklist when a
feature appears in one lane first. A lane may lead, but the shared concept must
be named, mirrored, or explicitly deferred before it becomes accidental
architecture.

## Safety Line

The GUI can be original in presentation. It should not be original in database
semantics.

Original UI ideas are welcome:

- workspace graph,
- browser families,
- command lane,
- area-focused workbench,
- relation/index visualization,
- language and locale testing surfaces.

Database behavior must remain boringly authoritative: x64base owns it.
