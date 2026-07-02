# DotTalk++ Workbench Story v1

Status: active direction.

Related:

- `WORKSPACE_GRAPH_CONTRACT_V1.md`
- `WINDOWED_APP_CONTRACT_V1.md`

## Product Sentence

A DotTalk++ Workbench opens workspaces. A workspace is a collection of one or
more areas: the realm where DotTalk++ relates tables, attaches indexes, saves
and modifies graph definitions as `.dtschema` or `.dtschemas`, and drives
browsers, lists, and ERSATZ browser presets.

Each area owns its own table, state, snapshot, diagnostics, and event history.

## Design Direction

The windowed app should feel like a database workbench with a first-class
DotTalk++ command lane, not like a command prompt wrapped in native chrome.

DotTalk++ database behavior was built bottom-up. The workbench should now grow
top-down over that foundation: design the visible workspace/area/projection
experience first, then connect each action to the stable CLI/runtime service
that owns the behavior. A visible wx feature may precede a mature native service,
but it must either use the shared GUI core, use the DotTalk++ command/script
bridge, or identify itself as a skeleton.

The workbench surface should make these ideas visible:

- a workspace is the user's current working set,
- a workspace is a graph of areas, indexes, relations, and browser seeds,
- an area is a stable open table/work slot,
- a table snapshot is the read model shown in Browse and Structure,
- commands remain available as a power lane,
- GUI actions and command actions should converge through the same core
  services,
- diagnostics and task status are part of the workbench, not afterthoughts.

## Initial Window Shape

The first mature shape remains:

- top menus and command strip,
- left Workspace Areas panel,
- central Browse and Structure views,
- bottom diagnostics/command transcript panel,
- status bar with task, active area, and row/record state.

This is intentionally a hybrid:

- FoxPro-style command/output remains important for continuity and power users.
- Modern database UI conventions carry navigation, inspection, multiple open
  areas, and future structure/properties views.
- Cross-platform native behavior stays with wxWidgets for C++ and Tkinter for
  the Python preview lane.

## Naming Rules

Use these names consistently in GUI-facing docs and labels:

| Name | Meaning |
| --- | --- |
| Workbench | The windowed DotTalk++ application experience |
| Workspace | The open working set inside the workbench |
| Area | A stable open table/work slot in the workspace graph |
| Table | The DBF/database object owned by an area |
| Index | Attached order/index resource for an area |
| Relation | Directed link between areas in the workspace graph |
| Snapshot | Immutable read model rendered by views |
| Browser view | Browse/list/relation/ERSATZ view over the workspace graph |
| Command lane | DotTalk++ command entry and transcript/output surface |
| Diagnostics lane | Structured log, task output, warnings, and reports |

Do not rename the stable core event names just to match a widget. The core can
keep `area_selected`, `table_snapshot_ready`, and similar programmatic names
while the UI presents a workbench story.

## Near-Term Consequences

- The application title should present as DotTalk++ Workbench.
- The left area list should be presented as Workspace Areas.
- Opening a table creates or activates an area; it must not implicitly close
  other areas.
- Browse and Structure are views of the selected area's snapshot.
- The command lane should be docked or pane-based, not the whole application.
- Future workspace files should restore area membership, layout, command
  history policy, locale preferences, graph relations, attached indexes,
  browser seeds, and diagnostics retention policy.
