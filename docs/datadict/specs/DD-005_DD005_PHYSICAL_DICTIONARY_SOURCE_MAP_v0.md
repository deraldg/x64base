# DD-005 Physical Dictionary Source Map v0

Date: 2026-05-27  
Repo package examined: `ccode_homegrown_20260527-055727.zip`  
Mode: report-only organizing / source-map package

## Purpose

DD-005 identifies the C++ source files, headers, command surfaces, validators, and schema helpers that can feed the first physical data dictionary for DotTalk++ / x64base.

This is not a catalog mutation package. It maps where facts should come from.

## Summary

- Source-map candidate rows: 160
- Harvest anchor detail rows: 912
- Physical/source lanes: 12
- Proposed catalog object rows: 14
- Next work-package rows: 6

## Core design decision

The physical dictionary should be sourced from engine/runtime facts first:

```text
DBF/header/runtime open evidence
  -> DD_TABLE
  -> DD_FIELD
  -> DD_MEMO_STATUS
  -> DD_INDEX
  -> DD_WORKAREA
  -> DD_REL
  -> DD_SOURCE
  -> DD_RUNTIME_PROOF
```

Schema files, import inference, and source comments can contribute declared or candidate facts, but they should not overwrite runtime proof.

## Lane summary

| Lane | Source candidates | Anchor rows | Catalog targets |
|---|---:|---:|---|
| `PHYS_TABLE_AREA` | 12 | 72 | DD_TABLE, DD_TABLE_PHYSICAL, DD_WORKAREA |
| `PHYS_FIELD_DESCRIPTOR` | 16 | 85 | DD_FIELD, DD_FIELD_PHYSICAL, DD_FIELD_NAME_POLICY |
| `DBF64_HEADER_VALIDATE` | 12 | 71 | DD_TABLE_VERIFY, DD_FIELD_VERIFY, DD_DIALECT |
| `DBF_CREATE_SCHEMA_WRITE` | 13 | 78 | DD_SCHEMA_WRITE, DD_TABLE_DECLARED, DD_FIELD_DECLARED |
| `MEMO_BACKEND` | 15 | 90 | DD_MEMO_STATUS, DD_FIELD_MEMO, DD_MEMO_VERIFY |
| `CDX_INDEX_LMDB` | 17 | 99 | DD_INDEX, DD_TAG, DD_ORDER_STATE, DD_BACKEND_STATUS |
| `SCHEMA_DECLARATION` | 15 | 74 | DD_SCHEMA, DD_DECLARED_FIELD, DD_SCHEMA_SOURCE |
| `WORKSPACE_RELATIONS` | 16 | 96 | DD_WORKAREA, DD_WORKSPACE_SNAPSHOT, DD_REL, DD_REL_FIELD |
| `RULE_CONSTRAINTS` | 13 | 76 | DD_RULE, DD_RULE_BINDING, DD_FIELD_CONSTRAINT, DD_VALIDATION_RESULT |
| `EXPR_ENGINE` | 13 | 71 | DD_EXPR, DD_INDEX_EXPR, DD_RULE_EXPR, DD_FILTER_EXPR |
| `IMPORT_AUTODBF` | 14 | 82 | DD_IMPORT_PROFILE, DD_INFERRED_FIELD, DD_EXTERNAL_MAPPING, DD_EXPORT_PROFILE |
| `METAFACT_PROVENANCE` | 4 | 18 | DD_FACT, DD_SOURCE, DD_PROVENANCE, DD_RUNTIME_PROOF |

## Most important source anchors

### Physical table / area identity

Primary sources:

```text
include/xbase.hpp
src/xbase/dbf_file.cpp
src/cli/cmd_use.cpp
src/cli/cmd_vuse.cpp
```

These are the first providers for table path/name, open state, area kind, record count, record length, field count, and current runtime area status.

### Field descriptors and name policy

Primary sources:

```text
include/xbase.hpp
include/xbase/fields.hpp
include/xbase/dbf_create.hpp
include/xbase/field_name_policy.hpp
src/xbase/fields_mgr.cpp
src/cli/cmd_fields.cpp
src/cli/cmd_fieldmgr.cpp
```

These provide field names, types, lengths, decimals, descriptor tokens, logical-vs-physical name policy, field count, and field mutation behavior.

### DBF/x64 header validation

Primary sources:

```text
src/cli/dbf64_header_validate.cpp
include/xbase_64.hpp
src/xbase/dbf_create.cpp
src/xbase/dbf_file.cpp
```

This lane should become the first verification provider for x64 dialect marker, header layout, legal field types, field lengths, header length, record length, and field count.

### Memo status

Primary sources:

```text
include/memo/memo_manager.hpp
include/memo/memo_auto.hpp
include/memo/memo_verify.hpp
src/memo/memo_manager.cpp
src/cli/cmd_memo.cpp
src/cli/cmd_use.cpp
```

DD_MEMO_STATUS must distinguish:

```text
memo field exists
memo backend sidecar exists
memo backend attached
memo object readback verified
memo orphan scan status
```

That distinction matters because recent runtime evidence showed normal USE memo attach working while a workspace-open path did not attach the backend.

### CDX / index / LMDB

Primary sources:

```text
include/cdx/cdx.hpp
include/cdx/cdx_meta.hpp
src/cdx/cdx_file.cpp
src/cli/cmd_cdx.cpp
src/cli/cmd_index.cpp
src/cli/cmd_buildlmdb.cpp
src/cli/cmd_lmdb.cpp
```

DD_INDEX should expose CDX/tag facts. LMDB should be cataloged as backend/build/status evidence, not as the ordinary user-facing identity.

### Workspace and relations

Primary sources:

```text
include/workspace/workarea_manager.hpp
include/workspace/relation_state.hpp
src/cli/cmd_workspace.cpp
src/cli/cmd_relations.cpp
src/cli/cmd_set_relation.cpp
```

This lane feeds DD_WORKAREA, DD_WORKSPACE_SNAPSHOT, DD_REL, and relation verification rows.

### MetaFact bridge

Primary sources:

```text
include/dt/meta/metafact.hpp
include/dt/meta/metacollect.hpp
src/meta/metacollect.cpp
src/tools/metacollect_main.cpp
```

The existing `dt::meta::MetaFact` model already includes domains for FieldDictionary and RuntimeProof. DD-005 treats that as the bridge to the data dictionary, not as throwaway code.

## Catalog object direction

The initial physical dictionary should begin with these catalog families:

```text
DD_SOURCE
DD_TABLE
DD_FIELD
DD_FIELD_NAME_POLICY
DD_TABLE_VERIFY
DD_MEMO_STATUS
DD_INDEX
DD_SCHEMA
DD_WORKAREA
DD_REL
DD_RULE
DD_EXPR
DD_IMPORT_PROFILE
DD_RUNTIME_PROOF
```

This does not mean all of them must be implemented at once. It means the source-map now has a place for each major fact family.

## Boundary rules

- No source edits were made.
- No repo files were unpacked into or changed in the repo.
- No build was run.
- No runtime scripts were executed.
- No HELP, META, CMDHELPCHK, DBF, CDX, LMDB, or catalog data was mutated.
- Student/sample artifacts must remain optional overlay evidence unless generalized.
- x64base engine facts must stay usable without LabTalk/student/case/media dependencies.

## Recommended next step

DD-006 should define a concrete manifest schema for the first physical extraction:

```text
dd_source.json
dd_table.json
dd_field.json
dd_memo_status.json
dd_index.json
dd_runtime_proof.json
```

Then DD-007 can create a report-only Python 3.12 extractor skeleton that emits those manifests without touching repo files or runtime DBFs.
