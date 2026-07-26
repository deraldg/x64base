# DD096Z-D2ZG Post-Apply Smoke Triage v0

Created UTC: `2026-05-29T18:56:47+00:00`

## Purpose

DD096Z-D2ZG classifies the D2ZF post-apply smoke result.

The observed smoke is red at the DDICT reader/resolver layer, not at the physical artifact copy layer. This package captures that distinction and proposes the next source/resolver bridge lane.

## Boundary

No rollback, no active replacement, no active DBF writes, no active CDX/LMDB rebuild, no source edits, no HELP/CMDHELPCHK mutation, and no manual mutation.
