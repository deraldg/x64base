# DotTalk++ wxWidgets Frontend Plan v1

Status: phase-1 workspace shell started.

## Purpose

`dottalk_wx` is the first proposed real windowed GUI frontend for DotTalk++. It uses wxWidgets for native desktop widgets while keeping all runtime behavior behind `dottalk_gui_core`.

The initial skeleton lives in `src/gui/wx`. It is compiled only when
`DOTTALK_WITH_WX=ON`, and it currently provides a main frame, File/Open menu,
Area menu, persistent area list, browse/structure notebook, command input, log
pane, status bar, and worker-event bridge.

The wx frontend should follow the shared UI principles in
`docs/ui/CORE_UI_PRINCIPLES_V1.md`; it should branch from TUI and Python only
where native desktop widgets provide a clear advantage.

It must also follow:

- `WINDOWED_APP_CONTRACT_V1.md`
- `WORKSPACE_GRAPH_CONTRACT_V1.md`
- `../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `../database/DATABASE_SAFETY_CONTRACT_V1.md`

This frontend should prove the architecture with a small useful shell before adding editors, designers, dashboards, or visual relation tools.

## Build Target

```text
src/gui/wx/
  CMakeLists.txt
  app.cpp
  main_frame.cpp
  main_frame.hpp
  table_grid_model.cpp
  table_grid_model.hpp
  task_bridge.cpp
  task_bridge.hpp
```

Future CMake shape:

```cmake
if (DOTTALK_WITH_WX)
  find_package(wxWidgets CONFIG QUIET)
  if (wxWidgets_FOUND)
    add_executable(dottalk_wx ...)
    target_link_libraries(dottalk_wx PRIVATE dottalk_gui_core ...)
  else()
    message(FATAL_ERROR "DOTTALK_WITH_WX=ON but wxWidgets was not found.")
  endif()
endif()
```

The exact `find_package` form may vary by vcpkg, system package, or wx-config. Resolve that during the dependency phase, not in the planning phase.

## First Window Layout

Use a conventional application layout:

```text
Menu bar
Toolbar
Status bar

Left panel: workspace / open tables
Center: notebook with Browse, Structure, and Workspace Graph views
Bottom: output log
Top toolbar: open, refresh, close area, command input, run
```

Initial menus:

- File: Open Table, Exit
- Workspace: Open Workspace, Save Workspace, Save Workspace As (disabled until
  the workspace graph service is implemented)
- Area: Refresh Snapshot, Close Area
- Run: Run Command, Run DotScript, Cancel Task
- View: Output Log, Workspace Panel
- Help: About, Runtime Status

The first wx view is intentionally still read-only. Browse renders row values
from `TableSnapshot::rows`; Structure renders field metadata from
`TableSnapshot::columns`. Both tabs must be fed from the same immutable snapshot
so the UI never calls table/runtime APIs from paint or selection handlers.

The Structure/Properties direction should become the place where table dialect,
encoding, collation, memo/index status, open mode, and safety warnings are made
visible.

## First User Workflows

### Open Table

1. User chooses File > Open Table.
2. GUI posts `OpenTableRequest`.
3. Worker opens table through `dottalk_gui_core`.
4. Worker posts table metadata.
5. Worker posts initial read-only `TableSnapshot`.
6. UI grid displays rows.

### Open Workspace Graph

Deferred until a GUI-core workspace graph service exists.

Intended flow:

1. User chooses Workspace > Open Workspace.
2. GUI requests a `.dtschema` or `.dtschemas` file.
3. Worker loads and validates areas, relation endpoints, index attachments, and
   browser seeds through the shared runtime facade.
4. UI rebuilds the Workspace Areas panel from the graph result.
5. UI presents structured warnings for missing tables, stale indexes, relation
   mismatches, or unsupported graph features.

### Run Command

1. User types a DotTalk++ command.
2. UI posts `CommandRequest`.
3. Worker runs the command through compatibility runner.
4. UI appends log output and status.
5. Later phases replace common commands with native service calls.

### Refresh Snapshot

1. User requests refresh.
2. Worker builds a new immutable snapshot.
3. UI swaps grid model content on the UI thread.

## Grid Model

Use a model-style adapter between `TableSnapshot` and wx grid/list controls.

The grid adapter must:

- not own `DbArea`,
- not call runtime methods while painting,
- display only immutable snapshot data,
- support large tables through paging later.

Initial version can display the first N rows from `TableSnapshotRequest::max_records`.

## Event Bridge

`task_bridge` should translate GUI-core events to wx events.

Rules:

- Worker thread posts events.
- wx event handler runs on UI thread.
- UI handler updates controls.
- Event payloads are immutable or moved exactly once.

## Dependency Policy

Do not make wxWidgets a required dependency for normal builds.

Acceptable configure modes:

- default: no GUI target, no wx dependency lookup required,
- `DOTTALK_WITH_GUI=ON`: builds `dottalk_gui_core` only,
- `DOTTALK_WITH_WX=ON`: requires wxWidgets and builds `dottalk_wx`.

## First Acceptance Criteria

- `dottalk_wx` starts and shows a main window.
- The main window exposes bootstrap Workspace load/save menu actions for
  first-pass `.dtschema` files.
- The main window exposes a read-only Workspace Graph tab fed by current area
  state.
- The main window can open more than one DBF as separate GUI areas.
- Area selection switches the active snapshot without closing prior areas.
- Browse and Structure tabs render from the active immutable `TableSnapshot`.
- The app can enqueue a background task and receive progress events.
- A real `Open Table` action works through `dottalk_gui_core`.
- Unknown encoding, stale index, read-only mode, and other database safety
  warnings have a structured path into the UI.
- Window chrome, task labels, and status lines render through the GUI
  localization resolver.
- Closing the app cancels or joins outstanding worker tasks cleanly.

## Deferred Features

Do not build these in the first wx phase:

- record editing,
- relation graph visualization,
- schema designer,
- report designer,
- metadata dashboards,
- plugin marketplace,
- custom rendering engine,
- embedded terminal emulator.

These are valuable, but they should wait until the session, task, and snapshot contracts are stable.
