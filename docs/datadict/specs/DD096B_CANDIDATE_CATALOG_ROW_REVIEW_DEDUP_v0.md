# DD096B Candidate Catalog-Row Review / Deduplication v0

Created UTC: `2026-05-28T22:48:20+00:00`

## Purpose

DD096B performs a read-only comparison between DD096A candidate catalog rows and active Data Dictionary catalog DBFs.

## Boundary

DD096B is read-only review/deduplication. It does not edit C++ source, edit build files, edit command registration, mutate active catalog DBFs, append/replace/delete/pack/zap DBFs, create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
