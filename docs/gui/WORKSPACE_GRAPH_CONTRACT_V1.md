# DotTalk++ Workspace Graph Contract v1

Status: active direction.

Related:

- `WORKBENCH_STORY_V1.md`
- `WINDOWED_APP_CONTRACT_V1.md`
- `UNIFIED_GUI_CORE_V1.md`

## Core Rule

A workspace is a collection of one or more areas. It is the realm where
DotTalk++ opens tables, attaches indexes, defines relations, and presents those
objects through browsers, lists, and ERSATZ browser presets.

The workspace is therefore a graph, not just a file list.

Runtime command boundary:

- `WORKSPACE OPEN ...` is replacement-style. It resets live area membership
  before opening the requested directory/table set.
- `WORKSPACE ADD <file.dbf>` is additive. It opens one table into the first free
  work area and preserves existing open areas.
- GUI "Open Table" should map to additive area creation semantics.
- GUI "Open Workspace" should map to workspace graph load/replacement
  semantics.

## Graph Objects

| Object | Meaning |
| --- | --- |
| Workspace | Saved/open working graph of areas, relations, indexes, browser seeds, and layout |
| Area | Named open table slot with path, alias/display name, open state, warnings, and active order |
| Table | DBF/database object owned by an area |
| Index | CDX/CNX/INX or backend index attachment used by an area/order |
| Relation | Directed relationship between source and target areas |
| Browser view | Projection/navigation surface over an area or relation path |
| ERSATZ preset | Saved browser seed such as root, path, limit, and selected workspace |
| Snapshot | Immutable read model produced from the graph for a specific view |

## File Family

Current terminology:

- `.dtschema` is a DotTalk++/x64base workspace schema/session file.
- `.dtschemas` is accepted as the plural workspace-schema extension.
- `.erz` is an ERSATZ browser preset file and may reference a workspace through
  `WORKSPACE=...`.

The GUI should treat `.dtschema` and `.dtschemas` as workspace graph files, not
as ordinary single-table opens.

## Workbench Behavior

The Workbench should eventually provide:

- Open Workspace: load a `.dtschema` or `.dtschemas` graph.
- WORKSPACE OPEN Directory: runtime command `workspace open <dir>`, replacement
  style, opens DBFs from a directory through DotTalk++. The GUI may append one
  index/key mode (`CDX`, `CNX`, or `INX`) and optional `FALLBACK`, `recursive`,
  and `TABLE` flags.
- WORKSPACE LOAD Schema: runtime command `workspace load name.dtschemas`,
  replacement style, restores saved areas, relations, paths, and tags through
  DotTalk++.
- Add Table/Area: open a DBF into the current workspace without closing other
  areas.
- Save Workspace: persist area membership, relations, indexes, browser seeds,
  layout hints, locale/session settings, and diagnostics policy.
- Save Workspace As: write the current graph to a new workspace file.
- Open ERSATZ Preset: apply an `.erz` browser seed against a workspace graph.
- Workspace Graph view: inspect areas, relations, attached indexes, and browser
  paths.

The first visible GUI skeleton now provides:

- Workspace menu load/save/save-as actions for first-pass `.dtschema` files,
- additive table/area membership persisted as `table=<path>` lines,
- path-root inspection through the shared `paths` / `setpath` command lane,
- SET DBF and SET INDEX menu skeletons reserved for the future runtime service,
- a read-only Workspace Graph tab that summarizes current areas and marks
  relations, indexes, browsers/lists, ERSATZ presets, and DTSchema load/save as
  service-backed pending work,
- a SCAN...ENDSCAN command dialog that sends multiline scan scripts through the
  DotTalk++ CLI bridge and displays output in a separate results window.

These mark the intended surface without pretending the full graph service is
implemented. The current `.dtschema` format is intentionally minimal and should
be treated as a bootstrap format until the GUI-core workspace service owns
relations, indexes, layouts, browser seeds, and validation.

Script/control command families remain CLI-owned for now. `DO` / `DOTSCRIPT`,
`SCAN` / `ENDSCAN`, `LOOP` / `ENDLOOP`, and `VAR` / `SET VAR` should pass
through the bridge unless a GUI-native command has explicitly claimed them.

## Browser Families

The Workbench should expose several ways to inspect the same graph:

- Browse: table-oriented grid for the selected area.
- Structure: field and table metadata for the selected area.
- List: command-compatible listing/projection output.
- Relation Browser: traversal over active relation paths.
- ERSATZ Browser: preset-driven relation/path browser.
- Workspace Graph: graph inspector for areas, indexes, and relations.

These are views over the workspace graph. They must not own database state or
silently mutate area/index/relation semantics.

## Runtime Boundary

GUI frontends should not parse `.dtschema`, `.dtschemas`, or `.erz` files ad hoc
inside widget code.

The required runtime service shape is:

1. parse/load workspace graph,
2. validate paths, areas, relation endpoints, and index attachments,
3. publish structured warnings and errors,
4. create or update core `Area` and graph models,
5. publish immutable snapshots/views for GUI rendering,
6. save graph changes through one canonical writer.

Until that service exists, GUI load/save controls remain disabled.

## Editing Gate

Changing a workspace graph is distinct from editing table records.

Workspace graph edits may eventually include:

- add/remove area,
- rename alias,
- attach/detach index,
- change active order,
- add/remove relation,
- change browser root/path/limit,
- save ERSATZ preset.

These edits still require validation, dirty-state tracking, save/revert, and
diagnostic reporting. They should not be mixed with record-edit enablement.
