# DD-093B DDICT Index/LMDB Subroot Resolver Repair v1

Created UTC: `2026-05-28T21:24:44+00:00`

## Purpose

DD-093B repairs DDICT CDX/LMDB artifact discovery after the Data Dictionary catalog moved to:

```text
dottalkpp/data/datadict
dottalkpp/data/indexes/datadict
dottalkpp/data/lmdb/datadict
```

## Boundary

DD-093B is guarded source-path repair only. It may patch only `src/datadict/ddict_catalog_paths.cpp` when explicitly requested. It does not edit build files, command registration, active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
