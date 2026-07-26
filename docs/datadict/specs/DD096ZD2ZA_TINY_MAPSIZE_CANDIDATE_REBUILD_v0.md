# DD096Z-D2ZA Tiny Mapsize Candidate Rebuild v0

Created UTC: `2026-05-29T17:09:57+00:00`

## Purpose

DD096Z-D2ZA updates the D2Y candidate rebuild retry to use `BUILDLMDB` mapsize presets.

The runtime usage shows default `BUILDLMDB` mapsize is 128 MiB. For the tiny candidate Data Dictionary proof tables, `TINY` or `SMALL` is more appropriate.

## Boundary

No active catalog replacement, no active DBF writes, no active CDX/LMDB rebuild, no source edits, no build edits, no workspace mutation, no HELP/CMDHELPCHK mutation, no manual mutation.
