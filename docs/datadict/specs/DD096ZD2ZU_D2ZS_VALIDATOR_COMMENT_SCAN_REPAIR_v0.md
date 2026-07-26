# DD096Z-D2ZU D2ZS Validator Comment Scan Repair v0

Created UTC: `2026-05-30T00:51:21+00:00`

## Purpose

DD096Z-D2ZU repairs the D2ZS validator so safety terms inside comments do not fail the executable mutation scan.

D2ZT correctly placed the top usage contract. That contract may mention forbidden operations as safety boundaries. The validator should ignore comments when checking for destructive executable mutation terms.

## Boundary

No `cmd_ddict.cpp` runtime logic rewrite, no build edits, no active catalog replacement, no active DBF/CDX/LMDB mutation, no HELP/CMDHELPCHK mutation, and no manual mutation.

This package only patches `tools/datadict/catalog/reviewed_source_patch_apply_harness.py`.
