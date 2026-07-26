# DD096Z-D2X Candidate Area Identity Guard v0

Created UTC: `2026-05-29T16:14:47+00:00`

## Purpose

DD096Z-D2X corrects the DD096Z-D2W failure mode.

D2W correctly used `SELECT`, but selected hardcoded areas that contained active legacy `DD*` tables, not inactive candidate `DATA_DICTIONARY_*` tables.

## Boundary

Identity guard only. No CDX CREATE, no BUILDLMDB, no source edits, no build edits, no active catalog replacement, no active DBF writes, no active CDX/LMDB rebuild, no workspace mutation, no HELP/CMDHELPCHK mutation, no manual mutation.
