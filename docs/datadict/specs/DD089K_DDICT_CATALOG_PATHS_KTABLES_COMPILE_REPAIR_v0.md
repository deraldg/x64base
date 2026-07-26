# DD-089K DDICT catalog_paths kTables Compile Repair v0

Created UTC: `2026-05-28T17:26:48+00:00`

## Purpose

DD-089K repairs the next compile failure after DD-089J.

The failure is narrower than the first one:

```text
src/datadict/ddict_catalog_paths.cpp references kTables
kTables was not moved from cmd_ddict.cpp anonymous namespace during extraction
```

## Boundary

DD-089K may edit only:

```text
src/datadict/ddict_catalog_paths.cpp
```

It does not patch `cmd_ddict.cpp`, edit CMake/build files, command registration, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.
