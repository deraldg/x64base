# DD096Z-D2ZS Reviewed Source Patch Apply Harness v0

Created UTC: `2026-05-30T00:29:07+00:00`

## Purpose

DD096Z-D2ZS stages and validates a human-reviewed `cmd_ddict.cpp` source patch for the actual FIELDS/TAGS logic.

It does not synthesize or apply a blind rewrite. It can stage a review copy, validate a candidate source file, and apply only with an explicit `--apply-reviewed-source` flag after validation.

## Boundary

No build edits, no active catalog replacement, no active DBF/CDX/LMDB mutation, no HELP/CMDHELPCHK mutation, and no manual mutation.

Source mutation requires a reviewed candidate source file and `--apply-reviewed-source`.
