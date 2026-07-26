# DD096Z-C Candidate-Root Readback Validation v0

Created UTC: `2026-05-29T13:57:04+00:00`

## Purpose

DD096Z-C validates the inactive candidate root staged by DD096Z-B.

It checks candidate DBF header record counts and optionally writes a DotTalk++ runtime readback script targeting the candidate paths.

## Boundary

No active catalog replacement. No active DBF copy/write. No CDX/LMDB rebuild. No workspace mutation. No source/HELP/manual mutation.
