# DD096Z-D2ZF Guarded Active Replacement Execution v0

Created UTC: `2026-05-29T18:33:16+00:00`

## Purpose

DD096Z-D2ZF is the implementation package after D2ZE green and explicit authorization.

It generates guarded execution scripts for active Data Dictionary replacement. The generator itself does not mutate active catalogs; the PowerShell execution script requires `-ExecuteActiveReplacement`.

## Boundary

The package generator performs no active catalog replacement, no active DBF writes, no active CDX/LMDB rebuild, no source edits, no build edits, no HELP/CMDHELPCHK mutation, and no manual mutation.

The generated execution script, when run with `-ExecuteActiveReplacement`, backs up active artifacts and copies candidate DBF/CDX/LMDB artifacts into active roots.
