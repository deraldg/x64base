# DotTalk++ Windowed Application Contract v1

Status: draft blocking contract.

Related:

- `OPEN_ARCH_GUI_PLAN_V1.md`
- `UNIFIED_GUI_CORE_V1.md`
- `WORKBENCH_STORY_V1.md`
- `WORKSPACE_GRAPH_CONTRACT_V1.md`
- `GUI_THREADING_EVENT_MODEL_V1.md`
- `../database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `../database/DATABASE_SAFETY_CONTRACT_V1.md`
- `../ui/CORE_UI_PRINCIPLES_V1.md`

## Purpose

DotTalk++ can already show a skeletal native window. The next goal is harder:
make it a good windowed database program.

This contract defines the desktop behavior expected from wxWidgets, Python GUI,
and any later windowed frontend while keeping the UI lanes orthogonal.

## Core Rule

A windowed DotTalk++ app is a workbench, not a command prompt in a window.

A DotTalk++ Workbench opens workspaces. A workspace is a collection of one or
more areas: the realm where DotTalk++ relates tables, attaches indexes, saves
and modifies graph definitions as `.dtschema` or `.dtschemas`, and drives
browsers, lists, and ERSATZ browser presets. Each area owns its own table,
state, snapshot, diagnostics, and event history.

The command lane remains important, but native windows should also expose stable
areas, snapshots, structure, tasks, diagnostics, and safe database workflows.

## Application Concepts

| Concept | Meaning |
| --- | --- |
| Workbench | The windowed DotTalk++ application experience |
| Application | Process-wide menus, preferences, recent files, global task monitor |
| Workspace | User's open graph: areas, relations, indexes, browser seeds, result sets, logs, layout |
| Area | Open table/work slot with stable ID, path, display name, state, warnings |
| Workspace graph | Persistable model behind `.dtschema` / `.dtschemas` workspace files |
| ERSATZ preset | Browser seed file that can reference a workspace and relation path |
| Snapshot | Immutable read model rendered by grids, inspectors, and structure views |
| Task | Queued/running/completed/cancelled/failed background operation |
| Command lane | DotTalk++ command text and compatibility output |
| Service lane | Typed actions such as open, refresh, validate, export, reindex |
| Diagnostics lane | Structured status, warnings, errors, logs, and reports |
| Preferences | UI language, display locale, parse locale, theme, layout, safety defaults |

These concepts should exist in every first-class UI lane even if the controls
look different.

## Orthogonal UI Lanes

Each UI lane should share behavior contracts but branch presentation:

| Lane | Strength |
| --- | --- |
| CLI | scripts, automation, exact command transcript |
| TUI | keyboard-heavy local work, compact panes, terminal deployment |
| Python GUI | fast iteration, scripting, inspection tools, pydottalk experiments |
| C++ wx GUI | packaged native desktop app, strong grids, menus, dialogs, OS integration |

Do not fork database behavior because a toolkit makes it convenient. Fork
navigation, rendering, packaging, and inspection workflows where the medium is
stronger.

## Required Window Shape

The first mature window should converge on:

```text
Menu bar
Toolbar / command strip

Left workspace panel
  Areas
  graph summary later
  recent/pinned workspaces later

Main notebook
  Browse
  Structure
  Properties
  Workspace Graph later
  ERSATZ Browser later
  Results later

Bottom diagnostics panel
  Log
  Task output
  Validation reports later

Status bar
  task state
  active area
  row/record or selection state
```

The current wx skeleton is aligned with this by using an Areas panel,
Browse/Structure tabs, command strip, log pane, and status bar.

## Required Native Behaviors

Windowed frontends should provide:

- open/save workspace graph placeholders before full DTSchema support,
- multiple open areas without replacing prior areas,
- switch active area,
- close an area explicitly,
- refresh active snapshot,
- recent files,
- persisted window size and pane layout,
- menus and keyboard shortcuts,
- context menus for grid/area actions,
- copy selected cells/rows,
- visible task progress,
- cooperative cancellation,
- structured error details,
- status bar that is useful without reading the log,
- high-DPI safe layout,
- keyboard navigation and focus order,
- accessibility labels for meaningful controls.

These should be added incrementally, but the architecture must assume them.

## Threading and Responsiveness

Only the UI thread touches widgets.

Database work runs through shared session/task services:

- open table,
- scan/snapshot,
- run DotScript,
- validate,
- import/export,
- reindex,
- load/save workspace graph,
- apply ERSATZ browser preset,
- pack/repair.

Results return as immutable events. The UI applies the latest relevant result
and never reads mutable `DbArea` state directly.

Progress updates should be coalesced so a large scan does not flood the event
loop. Cancellation is cooperative and should be visible on long tasks.

## Grid Contract

A database GUI succeeds or fails on its grid.

The browse grid should grow toward:

- immutable snapshot rendering first,
- virtual/paged rows for large tables,
- stable record identity,
- row labels with record numbers,
- deleted-record visibility policy,
- column resize and reorder,
- copy cell/range/row,
- search within visible snapshot,
- service-backed filter and sort later,
- explicit edit mode later,
- field validation before commit,
- no runtime calls during paint.

Large table support should use paging or virtual grids rather than loading all
records into widgets.

## Structure and Properties Contract

The Structure tab should eventually show:

- field name,
- type,
- width,
- decimals,
- nullable/blank policy,
- display format,
- encoding and collation context,
- index participation,
- validation warnings,
- metadata sidecar hints.

The Properties view should eventually show:

- table path,
- dialect,
- encoding/code page,
- memo file status,
- index/tag status,
- record count,
- open mode,
- lock state,
- safety warnings.

This is where language/region/database correctness becomes visible to users.

## International Window Behavior

Windowed frontends must separate:

- UI language,
- display locale,
- input parse locale,
- table encoding,
- table collation,
- import/export encoding.

Requirements:

- menus/messages use UI language,
- values use display locale,
- typed input uses parse locale or field-specific parsing,
- import/export prompts declare encoding and locale,
- IME text entry remains possible for future editing,
- font fallback avoids blank boxes where practical,
- right-to-left layout is not required in v1 but must not be structurally
  impossible.

## Error UX

Errors should have layers:

- status bar: short current state,
- log: readable detail,
- details dialog/report: paths, codes, operation, recovery advice,
- structured payload: stable codes for program behavior.

Examples:

- unknown encoding,
- stale index,
- memo pointer out of range,
- locked file,
- parse locale mismatch,
- command failed,
- task cancelled.

## Editing Gate

Editing must remain gated until these are designed:

- explicit edit mode,
- dirty state per area,
- validation before commit,
- commit/revert actions,
- close prompt for dirty areas,
- lock conflict reporting,
- index update/rebuild policy,
- memo update policy,
- undo or at least original-record recovery.

The first windowed GUI should keep browse read-only and make that state clear.

## Preferences

Windowed preferences should eventually include:

- UI language,
- display locale,
- default parse locale,
- default open mode: read-only vs edit prompt,
- default encoding behavior for unknown DBF code pages,
- command history policy,
- recent files count,
- layout reset,
- task/log retention.

Preferences must not silently alter table/index semantics without warning.

## Acceptance Criteria

The windowed app contract is minimally honored when:

- wx and Python GUI lanes share area/task/snapshot names,
- a second opened table remains open as a separate area,
- switching areas refreshes the active immutable snapshot,
- Browse and Structure render from the same snapshot,
- long work is queued off the UI thread,
- status/errors are structured before being rendered,
- task labels and status messages carry stable localization codes before being
  rendered,
- language/locale/encoding/collation are represented in the design,
- editing remains disabled until write safety is implemented.

## Near-Term Implementation Tasks

1. Add value/locale/collation metadata to GUI-core open/snapshot results.
2. Add a Properties tab or panel for table context and warnings.
3. Promote the GUI CSV seed into the full shared runtime message catalog.
4. Wire GUI locale selection to persisted startup/session settings.
5. Add task cancellation surface in wx and Python lanes.
6. Add recent files and persisted window layout.
7. Add grid copy and basic find.
8. Add headless tests that assert Python and C++ contract names remain aligned.
9. Add a workspace graph runtime facade for `.dtschema`, `.dtschemas`, and
   `.erz` before enabling GUI load/save controls.
