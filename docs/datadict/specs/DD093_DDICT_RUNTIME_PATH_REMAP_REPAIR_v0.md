# DD-093 DDICT Runtime Path Remap Repair v0

Created UTC: `2026-05-28T20:50:18+00:00`

## Purpose

DD-093 repairs DDICT runtime catalog path resolution after the Data Dictionary catalog moved to the first-class root:

```text
dottalkpp/data/datadict
dottalkpp/data/indexes/datadict
dottalkpp/data/lmdb/datadict
```

## Boundary

DD-093 is guarded source-path repair only. It does not edit build files, command registration, active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
