# DD-089L DDICT kTables Shape Compile Repair v0

Created UTC: `2026-05-28T17:30:40+00:00`

## Purpose

DD-089L repairs the next compile failure after DD-089K.

DD-089K restored `kTables`, but as `const char*[]`. The moved code still expects `t.name`, so DD-089L restores the earlier table-info shape.

## Boundary

DD-089L may edit only:

```text
src/datadict/ddict_catalog_paths.cpp
```

It does not patch `cmd_ddict.cpp`, edit CMake/build files, command registration, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.
