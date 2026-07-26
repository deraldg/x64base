# DD-041 Sandbox Catalog DBF Creation and Readback Smoke v0

Created UTC: `2026-05-27T21:00:28+00:00`

## Purpose

DD-041 creates and populates sandbox Data Dictionary catalog DBFs from the DD-040 projected rows, then validates readback counts.

This package is authorized only for the sandbox path:

```text
dottalkpp/data/metadata/datadict_sandbox/
```

## Allowed mutation

```text
create/write DBF and DBT files under dottalkpp/data/metadata/datadict_sandbox/
```

## Not allowed

```text
active catalog promotion
HELP mutation
META mutation
CMDHELPCHK mutation
source edits
runtime launch
CDX creation
LMDB writes
writes outside the sandbox path
```

## Inputs

```text
DD-039 catalog DBF/DDL definition CSVs
DD-040 projected row CSVs
```

## Outputs

```text
dottalkpp/data/metadata/datadict_sandbox/*.dbf
dottalkpp/data/metadata/datadict_sandbox/*.dbt for tables with memo fields
dd041_sandbox_catalog_dbf_smoke_manifest.json
dd041_table_readback_ledger.csv
dd041_no_mutation_boundary_ledger.csv
DD041_SANDBOX_CATALOG_DBF_READBACK_REPORT.md
```

## Important

This package does not create CDX tags yet. CDX creation and x64base runtime readback should be a separate gated step after this first sandbox DBF smoke succeeds.
