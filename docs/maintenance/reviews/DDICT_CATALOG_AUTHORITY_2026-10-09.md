# DDICT catalog authority assessment

Date: 2026-10-09 (America/Los_Angeles)
Owner: member.derald
Status: source-evidenced and artifact-measured; proposed integration remains review-needed
Authorization: maintainer asked to proceed with the crosswalk's recommended curation order.

The current DDICT read dataset is the eleven legacy DD* tables in
`dottalkpp/data/datadict`. The six DATA_DICTIONARY_* tables in the same directory
contain additional, differently shaped information. They do not replace the
legacy dataset. Preserve both families while preparing an explicit integration.
This assessment records observed authority; it does not approve a migration,
rewrite historical policy, or promote catalog rows.

## What establishes the current read authority

| Consumer or producer | Observed behavior | Evidence |
| --- | --- | --- |
| CLI | Requests DDOBJECT, DDATTR, DDEDGE, DDEVID, DDSOURCE, DDARTIF by literal name; STATUS/TABLES enumerate eleven legacy names | `src/cli/cmd_ddict.cpp`, `kTables`, `print_fields`, `print_rel`, `print_evidence`, `print_objects` |
| Shared DBF reader | Appends `.dbf` to the supplied uppercase name; no long-name storage selection or logical-column translation | `src/datadict/ddict_dbf_reader.cpp`, `read_dbf_table` |
| GUI | Requests DDOBJECT, DDATTR, DDEDGE, DDEVID, DDSOURCE | `src/gui/wx/main_frame.cpp`, DDICT refresh reads |
| Workspace | Eleven AREA declarations and seven RELATION declarations reference legacy tables/fields | `dottalkpp/data/workspaces/ddbase.dtschema` |
| Alias bridge | Translates six catalog names and DDICT; FIELDS/TAGS expand owner-token matches | `src/datadict/ddict_catalog_resolver.cpp`, `ddict_catalog_bindings`; `cmd_ddict.cpp`, `owner_lookup_candidates` |
| Historical long-name producer | DD096ZD2ZF execution record reports copying candidate files into active paths, pending smoke | Execution record embedded with its source hash in the [inventory](DDICT_CURATION_INVENTORY_2026-10-09.json) |
| Historical follow-up | DD096ZD2ZG identifies old compact-model reads and fields/tags/relation/evidence gaps after the copy | Triage record embedded in the inventory; original path recorded there |
| Redocumentation orchestrator | Discovers source and writes a report; many extraction/reconciliation stages remain PLANNED and promotion is BLOCKED | `tools/datadict/orchestrate/redoc_orchestrator.py`, `STEP_ROWS` and `main` |

There is no evidence here of one currently proven refresh operation that
synchronizes both families. The old execution record establishes a recorded copy,
not a completed semantic migration. All six current long-name DBF SHA-256 hashes
match the source hashes in that copy plan. That links today's bytes to the
historical package; it does not prove current runtime behavior or index health.

## The families describe different information

The repository's shared `tools/fullstack_docs/dbfread.py` read every table with
field-width reconciliation. No deleted records were reported in these tables.
Memo pointers remain unresolved; this review does not claim to have read their
text. The [inventory](DDICT_CURATION_INVENTORY_2026-10-09.json) preserves fields,
widths, live-row counts, actual identifier sets, and object rows.

| Logical family | Legacy table / live rows | Long-name table / live rows | Shared primary identifier values |
| --- | --- | --- | ---: |
| Runs | DDRUN / 1 | DATA_DICTIONARY_RUNS / 2 | 0 |
| Objects | DDOBJECT / 100 | DATA_DICTIONARY_OBJECTS / 10 | 0 |
| Attributes | DDATTR / 423 | DATA_DICTIONARY_OBJECT_ATTRIBUTES / 127 | 0 |
| Edges | DDEDGE / 89 | DATA_DICTIONARY_RELATION_EDGES / 16 | 0 |
| Evidence | DDEVID / 1 | DATA_DICTIONARY_EVIDENCE_RECORDS / 7 | 0 |
| Gates | DDGATE / 6 | DATA_DICTIONARY_GATE_RECORDS / 3 | 0 |

The legacy object set contains 11 CATALOG_TABLE, 67 CATALOG_FIELD, and 22
CATALOG_TAG records. The long-name set contains nine COMMAND_SURFACE records and
one COMMAND record. One EVIDENCE command surface carries a schema-proof status;
the other records carry candidate-review status. Those stored status strings are
data, not fresh validation results.

The five remaining legacy tables -- DDBASE, DDSOURCE, DDREVIEW, DDARTIF, DDPROFILE
-- have no corresponding binding in the six-entry long-name map. The split
therefore affects coverage as well as spelling.

## Schema translation is required

| Legacy field | Long-name field | Consumer meaning |
| --- | --- | --- |
| OBJID | CATALOG_OBJECT_ID | Object identity |
| OBJTYPE | CATALOG_OBJECT_TYPE | Object kind |
| NAME | CATALOG_OBJECT_NAME | Display/lookup name |
| OWNER | CATALOG_OWNER_NAME | Owner/parent token |
| STATUS | CATALOG_STATUS_CODE | Stored status |
| PROFILE | CATALOG_PROFILE_CODE | Profile |
| SRCID | SOURCE_ARTIFACT_ID | Source reference; target domain needs reconciliation |
| ATTRID | CATALOG_ATTRIBUTE_ID | Attribute identity |
| ATTRNAME | CATALOG_ATTRIBUTE_NAME | Attribute key |
| ATTRVAL | CATALOG_ATTRIBUTE_VALUE | Inline value |
| ATTRMEMO | CATALOG_ATTRIBUTE_DETAIL | Memo value; requires a memo-aware read |
| EVID | EVIDENCE_RECORD_ID | Evidence identity/reference |
| EDGEID | RELATION_EDGE_ID | Edge identity |
| FROMOBJ / TOOBJ | RELATION_FROM_OBJECT_ID / RELATION_TO_OBJECT_ID | Endpoints; validate allowed kinds |
| EDGETYPE | RELATION_EDGE_TYPE | Relation kind |

This table is a semantic proposal based on measured field names and rows, not
an implemented adapter. For example, a long-name HAS_CATALOG_ATTRIBUTE edge
targets an attribute ID. Treating every endpoint as an object ID would create
false missing-object findings. Source references also need their actual target
domains established before imposing legacy joins.

## Disposition for this curation pass

1. Keep legacy consumer reads and the workspace schema intact. They describe the
   dictionary's table/field/tag structure and cannot be replaced by ten command
   records without losing that view.
2. Classify long-name tables as preserved supplemental schema-promotion and
   command/evidence data. Do not label them obsolete, or silently overwrite them
   with legacy-derived rows.
3. Treat filename aliases as compatibility names, not proof that schemas or
   populations are interchangeable. The command's current source header
   overstates the completed bridge; this is recorded drift.
4. Keep the parent catalog root as the current home. Nested identical copies
   are consolidation candidates, with exact hashes and prerequisites in the
   [plan](DDICT_CONSOLIDATION_PLAN_2026-10-09.md).

## Proposed next implementation

Build a read-only normalized catalog view before any data migration. Preserve
the origin family and original identity on every row, map fields explicitly,
resolve memo values through the established storage API, and validate endpoint
kinds. Compare members and relationships, not just totals. Present errors,
missing data, and valid empty results separately. CLI and GUI should consume
the same result, with the existing legacy views retained during validation.

An eventual canonical write schema and refresh pipeline remain a separate
design decision. A normalized read view can establish the complete content and
compatibility evidence needed for that decision without destroying either input.
The current authorization completed navigation and classification; no catalog
cutover or destructive consolidation has been executed.
