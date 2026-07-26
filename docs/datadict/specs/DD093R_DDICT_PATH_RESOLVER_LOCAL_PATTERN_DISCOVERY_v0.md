# DD-093R DDICT Path Resolver Local-Pattern Discovery v0

Created UTC: `2026-05-28T20:54:39+00:00`

## Purpose

DD-093R follows DD-093 review. It inspects the actual local path resolver structure after DD-093 could not find a simple `metadata/datadict` literal.

## Boundary

DD-093R is discovery/guarded patch only. It may patch only `src/datadict/ddict_catalog_paths.cpp` when explicitly requested and a safe local pattern is found. It does not edit build files, command registration, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, generated catalog content, or manual rows.
