# DD096Z-D2Y Open/Close Candidate Rebuild v0

Created UTC: `2026-05-29T16:23:07+00:00`

## Purpose

DD096Z-D2Y corrects the D2W mixed-root failure.

D2X proved that fresh-session areas are empty and that the candidate tables open cleanly from the inactive candidate DBF root. Therefore the next rebuild should open one candidate table, rebuild/verify it, close it, and move to the next table.

## Boundary

No source edits, no build edits, no active catalog replacement, no active DBF writes, no active CDX/LMDB rebuild, no workspace mutation, no HELP/CMDHELPCHK mutation, no manual mutation.
