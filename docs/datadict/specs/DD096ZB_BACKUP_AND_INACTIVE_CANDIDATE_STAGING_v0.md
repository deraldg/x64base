# DD096Z-B Backup and Inactive Candidate-Root Staging v0

Created UTC: `2026-05-29T13:50:21+00:00`

## Purpose

DD096Z-B backs up active Data Dictionary roots and stages the x64 proof DBFs/memo/x64 sidecars into an inactive candidate root.

It does not replace the active Data Dictionary catalog.

## Boundary

No active catalog replacement. No active DBF copy/write. No active CDX/LMDB rebuild. No workspace mutation. No source/HELP/manual mutation.

The tool only writes backup and candidate roots when `--execute-staging` is supplied and preconditions are green.
