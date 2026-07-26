# DD096Y Stage Candidate Rows into x64 Data Dictionary Proof Schema v0

Created UTC: `2026-05-29T02:35:59+00:00`

## Purpose

DD096Y maps the DD096E-R staged candidate rows into the DD096X parallel x64 Data Dictionary proof schema.

It is still a proof/staging lane. It does not replace the active `dottalkpp/data/datadict` catalog.

## Boundary

Generator/report only unless `--write-runtime-script` writes a runtime DTS under `dottalkpp/data/scripts`.

Runtime precondition:

```text
DO SANDBOX
DO DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF
DO DD096Y_STAGE_CANDIDATE_ROWS_INTO_X64_SCHEMA
```
