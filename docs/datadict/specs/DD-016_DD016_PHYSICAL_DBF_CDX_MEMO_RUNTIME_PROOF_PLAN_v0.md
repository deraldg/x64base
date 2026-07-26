# DD-016 Physical DBF / CDX / MEMO Runtime Proof Plan v0

## Status

Report-only planning package. No DotTalk++ runtime was launched, no build was run, no DBF/CDX/LMDB/memo data was opened or mutated, and no repo files were changed.

## Purpose

DD-016 defines the guarded proof path for the physical dictionary pillars:

- DBF/x64 table header and field descriptor facts
- field-name policy evidence
- ordinary `USE` open-path proof
- memo backend attach/status/readback proof
- CDX/index/tag/order proof
- LMDB/backend status proof
- runtime transcript evidence suitable for later parser projection

This package follows DD-005 and DD-006. DD-005 mapped source anchors; DD-006 defined the physical dictionary manifest shape. DD-016 defines how runtime proof should be captured later without confusing plan evidence with runtime evidence.

## Static scan counts

- Source anchor rows: **3283**
- Focus anchor rows: **18**
- Transcript command-plan rows: **24**
- Catalog extension rows: **12**
- Boundary rows: **8**
- Evidence ladder rows: **7**
- Trust gates: **7**

## Lane summary

- cdx_index_tag: 459 source-anchor rows
- dbf_header_physical: 422 source-anchor rows
- doc_contract_note: 56 source-anchor rows
- field_descriptor_policy: 584 source-anchor rows
- lmdb_backend: 195 source-anchor rows
- memo_backend: 287 source-anchor rows
- runtime_command_surface: 412 source-anchor rows
- test_smoke_probe: 219 source-anchor rows
- use_open_table: 649 source-anchor rows

## Core dictionary objects reserved

DD-016 reserves or sharpens these catalog objects:

- `DD_TABLE_VERIFY`
- `DD_FIELD_PHYSICAL`
- `DD_FIELD_NAME_POLICY`
- `DD_MEMO_STATUS`
- `DD_MEMO_VERIFY`
- `DD_INDEX`
- `DD_TAG`
- `DD_INDEX_VERIFY`
- `DD_LMDB_STATUS`
- `DD_TRANSCRIPT_RUN`
- `DD_TRANSCRIPT_COMMAND`
- `DD_RUNTIME_PROOF`

## Runtime proof philosophy

The data dictionary must not treat a source-file mention as runtime proof. It must preserve the ladder:

```text
source anchor -> declared schema -> static DBF parse -> runtime open transcript -> runtime validation transcript -> reviewed catalog fact
```

## Mutation boundary

Most commands in the proof plan are non-mutating reads or display/validation commands. Mutation-like operations are isolated:

- `USE` mutates session state by opening an area.
- `SET INDEX` / `SET ORDER` mutate session index/order state.
- `REPLACE <memo_field>` is a real data mutation and is optional only on a disposable copy.
- `BUILDLMDB CLEAN YES` creates or rebuilds backend artifacts and is optional only on a disposable/generated dataset.

No mutation was performed in DD-016.

## Templates included

- `dd016_physical_proof_template.dts`
- `dd016_capture_wrapper.ps1.template`
- `dd016_physical_runtime_proof_v0.schema.json`
- `dd016_sample_plan_manifest_v0.json`

These are templates, not execution artifacts.

## Recommended next step

DD-017 should be a static DBF header parser/projection plan or skeleton that can read DBF files from a provided data-root copy and emit `DD_TABLE_VERIFY` / `DD_FIELD_PHYSICAL` evidence without launching DotTalk++. That would give a low-risk proof lane before runtime transcripts.
