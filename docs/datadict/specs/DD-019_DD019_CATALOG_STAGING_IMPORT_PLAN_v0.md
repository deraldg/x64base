# DD-019 Catalog-Staging Import Plan v0

Date: 2026-05-27  
Boundary: REPORT_ONLY  
Inputs inspected: DD-018 sample reconciliation outputs  
Mutation status: none

## Purpose

DD-019 defines how reconciled dictionary projections can later be staged into x64base catalog tables without confusing staging with promotion.

The core rule is:

```text
evidence stack -> staging tables -> conflict/gate review -> promotion queue -> later authorized catalog promotion
```

DD-019 does **not** create DBFs, import rows into x64base, mutate HELP/META/CMDHELPCHK, or promote dictionary facts.

## DD-018 input counts used for this plan

| Item | Count |
|---|---:|
| Projected objects | 17 |
| Projected tables | 3 |
| Projected fields | 14 |
| Evidence stack rows | 17 |
| Conflict rows | 0 |

## Staging catalog shape

The first staging layer should be object/evidence/attribute/edge based:

```text
DD_IMPORT_RUN
DD_SOURCE
DD_OBJECT
DD_ATTRIBUTE
DD_EVIDENCE
DD_EDGE
DD_CONFLICT
DD_GATE
DD_WARNING
DD_PROFILE_SCOPE
DD_PROMOTION_QUEUE
DD_IMPORT_FILE
```

This avoids premature proliferation of one table per evidence type while preserving enough structure to project into specialized catalog tables later.

## Why this is staging, not promotion

A staged row may be:

- declared schema evidence;
- static DBF byte-parse evidence;
- source-contract evidence;
- registry evidence;
- transcript evidence;
- generated report evidence;
- AI/manual proposal evidence.

Those evidence classes have different trust levels. DD-019 keeps them visible instead of flattening them into one final truth row.

## Import order

1. `DD_IMPORT_RUN`
2. `DD_SOURCE`
3. `DD_OBJECT`
4. `DD_EVIDENCE`
5. `DD_ATTRIBUTE`
6. `DD_EDGE`
7. `DD_CONFLICT`
8. `DD_GATE`
9. `DD_WARNING`
10. `DD_PROMOTION_QUEUE`

## Candidate DBF-friendly names

The package includes compact candidates such as:

```text
DDRUN
DDSRC
DDOBJ
DDATTR
DDEVID
DDEDGE
DDCONF
DDGATE
DDWARN
DDPROF
DDPROMO
DDFILE
```

These are staging-table names, not final public command vocabulary.

## Core boundary rules

- Staging import does not equal dictionary promotion.
- Promotion requires a later explicit authorization gate.
- HELP/META/CMDHELPCHK/source/runtime mutations remain forbidden here.
- Engine/professional/educational profile scope must stay visible.
- Declared/sample STUDENTS evidence must not become engine-core proof.
- Static DBF parse evidence must not be mislabeled as runtime proof.

## Generated sample projections

DD-019 includes sample CSV projections derived from DD-018 output:

```text
sample_output/dd019_import_run_v0.csv
sample_output/dd019_sources_v0.csv
sample_output/dd019_objects_v0.csv
sample_output/dd019_evidence_v0.csv
sample_output/dd019_attributes_v0.csv
sample_output/dd019_edges_v0.csv
sample_output/dd019_conflicts_v0.csv
sample_output/dd019_gates_v0.csv
sample_output/dd019_warnings_v0.csv
sample_output/dd019_promotion_queue_v0.csv
```

These are sample stage artifacts only. They should not be imported into a live repo/catalog without a later execution package.

## Result

DD-019 is green as a report-only plan.

No repo mutation, no source edits, no build, no runtime launch, no HELP/META/CMDHELPCHK mutation, and no DBF/CDX/LMDB/catalog mutation occurred.
