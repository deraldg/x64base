# DD-013 Workspace / Relation / Tuple Dictionary Source Map v0

Date: 2026-05-27

Status: REPORT_ONLY_SOURCE_MAP

## Purpose

DD-013 organizes the relationship side of the DotTalk++ / x64base data dictionary. It maps source anchors for workspace state, open work areas, relations, tuple projection, relation-aware browsing, and diagram consumers.

This package does not run DotTalk++, does not open tables, does not mutate relation state, and does not promote catalog records. It prepares the next safe proof lane.

## Counts

| Item | Count |
|---|---:|
| Source anchor rows | 670 |
| Lane rows | 7 |
| Relevant usage surface rows | 28 |
| Relevant registry surface rows | 22 |
| State structure rows | 25 |
| Catalog extension rows | 12 |
| Evidence-kind rows | 8 |
| Consumer matrix rows | 8 |
| Trust gate rows | 7 |
| Boundary rows | 5 |

## Main source lanes

- **area_command_surface**: 8 anchors — seed command-to-area/workarea links
- **browser_snapshot_consumer**: 46 anchors — seed DD_BROWSER_SNAPSHOT, DD_BROWSER_COLUMN, DD_RELATION_TREE_VIEW
- **diagram_external_consumer**: 1 anchors — seed DD_DIAGRAM_LINK and optional visualization artifact references
- **relations_join_enumeration**: 22 anchors — seed DD_REL, DD_REL_FIELD, DD_REL_FILE, DD_REL_ENUM, DD_REL_VERIFY
- **supporting_anchor**: 552 anchors — supporting evidence or review candidate
- **tuple_projection_graph**: 22 anchors — seed DD_TUPLE_SPEC, DD_TUPLE_COLUMN, DD_TUPLE_GRAPH_CURSOR, DD_TUPLE_VERIFY
- **workspace_workarea_state**: 19 anchors — seed DD_WORKAREA, DD_WORKSPACE_SNAPSHOT, DD_CURRENT_AREA, DD_WORKSPACE_VERIFY


## Core design decision

The relationship dictionary should separate five different truth levels:

```text
source contract evidence
registry/dispatch evidence
runtime read-only state proof
runtime relation-graph mutation proof
consumer/visualization evidence
```

A relation shown in a browser or diagram is useful, but it is not canonical by itself. A relation declared by source comments is useful, but it is not runtime proof. Canonical promoted relation facts should come from reviewed relation definitions plus runtime proof, with provenance preserved.

## Proposed catalog objects

```text
DD_WORKSPACE_SNAPSHOT
DD_WORKAREA
DD_CURRENT_AREA
DD_REL
DD_REL_FIELD
DD_REL_FILE
DD_REL_VERIFY
DD_TUPLE_SPEC
DD_TUPLE_COLUMN
DD_TUPLE_GRAPH_CURSOR
DD_BROWSER_SNAPSHOT
DD_DIAGRAM_LINK
```

## Notable anchors

Strong anchor families include:

```text
include/workspace/relation_state.hpp
include/workspace/workarea_manager.hpp
src/workspace/*
src/cli/cmd_workspace.cpp
src/cli/workareas.cpp
src/cli/cmd_rel.cpp
src/cli/cmd_relations.cpp
src/cli/cmd_set_relation.cpp
src/cli/set_relations.cpp
src/cli/relations_status.cpp
src/cli/rel_enum_engine.cpp
src/cli/join_engine.cpp
src/cli/cmd_tuple.cpp
src/cli/tuple_builder.cpp
include/tuple/tuple_graph_cursor.hpp
src/tuple/tuple_graph_cursor.cpp
include/browser/browser_relation_adapter.hpp
src/browser/browser_relation_adapter.cpp
src/cli/cmd_ersatz.cpp
src/cli/cmd_rbrowse.cpp
src/cli/cmd_drawio.cpp
```

## Boundary notes

x64base engine mode should not require browser, diagram, LabTalk, case, or student artifacts. DotTalk++ professional mode can expose workspace/relation/tuple commands without visible student content. Educational content can later attach example relations through overlays, but those examples must not become core DD_REL dependencies.

## Result

DD-013 is green as a report-only source map. Next recommended package is DD-014: a guarded workspace/relation transcript proof plan.
