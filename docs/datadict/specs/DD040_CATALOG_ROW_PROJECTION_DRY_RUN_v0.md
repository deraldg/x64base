# DD-040 Catalog Row Projection Dry-Run v0

Created UTC: `2026-05-27T20:56:30+00:00`

## Purpose

DD-040 projects exact candidate rows for the planned Data Dictionary catalog DBFs without creating or writing DBF files.

This package follows the corrected terminology from DD-039:

```text
DDL definition
catalog definition
DBF layout definition
table definition
field definition
index/tag definition
memo definition
```

It does not use `schema` as a user-facing concept.

## Inputs

Expected inputs include:

```text
docs/datadict/baselines/current_baseline.json
docs/datadict/baselines/DDBASE-stable-v2/dd027_baseline_acceptance_manifest.json
docs/datadict/definitions/dd039_catalog_table_definition_plan_v0.csv
docs/datadict/definitions/dd039_catalog_field_definition_plan_v0.csv
docs/datadict/definitions/dd039_catalog_tag_definition_plan_v0.csv
docs/datadict/definitions/dd039_catalog_definition_gate_ledger_v0.csv
```

## Outputs

```text
dd040_projected_DDRUN.csv
dd040_projected_DDBASE.csv
dd040_projected_DDSOURCE.csv
dd040_projected_DDOBJECT.csv
dd040_projected_DDATTR.csv
dd040_projected_DDEDGE.csv
dd040_projected_DDEVID.csv
dd040_projected_DDGATE.csv
dd040_projected_DDREVIEW.csv
dd040_projected_DDARTIF.csv
dd040_projected_DDPROFILE.csv
dd040_projection_manifest.json
dd040_projection_row_counts.csv
DD040_CATALOG_ROW_PROJECTION_REPORT.md
```

## Boundary

DD-040 is report-only:

```text
no DBF creation
no DBF row writes
no CDX creation
no LMDB writes
no DotTalk++ runtime launch
no HELP/META/CMDHELPCHK mutation
no catalog promotion
```

## Next

DD-041 may create sandbox catalog DBFs and perform readback only after explicit write authorization.
