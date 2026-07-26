# DD096X Guarded x64 Data Dictionary Schema Proof v0

Created UTC: `2026-05-29T02:24:03+00:00`

## Purpose

DD096X generates a parallel x64 Data Dictionary schema proof using meaningful long table and field identity names.

It uses single-line `CREATE X64` commands because long-name single-line CREATE is currently proven, while multiline CREATE continuation remains a separate red lane.

## Boundary

Generator/report only unless `--write-runtime-script` is used to place the DTS in `dottalkpp/data/scripts`.

Runtime DTS is intended for SANDBOX proof only:

```text
DO SANDBOX
DO DD096X_GUARDED_X64_DATADICT_SCHEMA_PROOF
```

No active `dottalkpp/data/datadict` catalog replacement.
