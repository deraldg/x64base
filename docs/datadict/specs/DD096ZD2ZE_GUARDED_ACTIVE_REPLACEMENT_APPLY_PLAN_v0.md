# DD096Z-D2ZE Guarded Active Replacement Apply Plan v0

Created UTC: `2026-05-29T18:28:31+00:00`

## Purpose

DD096Z-D2ZE is the first active-replacement planning lane after D2ZD green.

It creates a guarded apply plan: backup map, candidate-to-active copy map, rollback map, resolver/alias bridge gate, and post-apply smoke requirements.

It does not execute active replacement.

## Boundary

No active catalog replacement, no active DBF writes, no active CDX/LMDB rebuild, no source edits, no build edits, no workspace mutation, no HELP/CMDHELPCHK mutation, no manual mutation.
