# DD-017 Next Actions v0

## DD017B local read-only parser run

Run the parser against a copied DBF data root, not against production data in place if avoidable.

Example:

```powershell
python tools/dd017_dbf_header_parser.py D:\code\ccode\dottalkpp\data\DBF   --out-json dd017_static_dbf_projection.json   --out-tables-csv dd017_tables_projection.csv   --out-fields-csv dd017_fields_projection.csv
```

Expected result: static `DD_TABLE_VERIFY` and `DD_FIELD_PHYSICAL` candidate rows.

## DD-018 comparison plan

Compare DD-017 static parse output against DotTalk++ runtime transcript output:

- `USE <table>`
- `FIELDS`
- `DBAREAS`
- `AREA`
- memo attach/status commands where applicable

## DD-019 sidecar scan plan

Add read-only probes for:

- DBT/FPT/memo sidecars
- CDX sidecars
- LMDB backend presence/status files, if applicable

## Do not promote yet

DD-017 output is static evidence only. It should not be imported into promoted dictionary catalog tables until runtime comparison and review gates are green.
