# DD-042 Sandbox Catalog DBF Inspection / x64base Readback Plan v0

Created UTC: `2026-05-27T21:13:45+00:00`

## Purpose

DD-042 inspects the DD-041 sandbox catalog DBFs and prepares readback probe artifacts for a later x64base/DotTalk++ or pydottalk runtime readback lane.

DD-042 itself is read-only.

## Inputs

```text
dottalkpp/data/metadata/datadict_sandbox/
docs/datadict/reports/DD041-sandbox-catalog-dbf-smoke-v0/dd041_table_readback_ledger.csv
```

## Outputs

```text
dd042_sandbox_catalog_inspection_manifest.json
dd042_sandbox_catalog_inspection_ledger.csv
dd042_sample_rows.csv
dd042_no_mutation_boundary_ledger.csv
DD042_SANDBOX_CATALOG_INSPECTION_REPORT.md
dd042_pydottalk_readback_probe.py
dd042_dottalk_readback_probe_template.dts
```

## Boundary

Allowed:

```text
read sandbox DBF/DBT files
emit inspection reports
emit readback probe scripts/templates
```

Not allowed:

```text
write DBFs
create CDX files
write LMDB data
launch DotTalk++
mutate HELP/META/CMDHELPCHK
promote active catalog
edit source
```

## Next

DD-043 may execute pydottalk/DotTalk++ runtime readback only after explicit runtime-read authorization.
