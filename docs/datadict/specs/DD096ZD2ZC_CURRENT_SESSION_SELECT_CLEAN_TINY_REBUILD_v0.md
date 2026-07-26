# DD096Z-D2ZC Current-Session SELECT CLEAN TINY Rebuild v0

Created UTC: `2026-05-29T18:06:27+00:00`

## Purpose

DD096Z-D2ZC corrects the prior candidate rebuild script using the proven syntax:

```text
BUILDLMDB CLEAN TINY YES
```

It also preserves the current-session `SELECT <area>` strategy because the candidate `DATA_DICTIONARY_*` tables are already open in areas 0..5.

## Boundary

No active catalog replacement, no active DBF writes, no active CDX/LMDB rebuild, no source edits, no build edits, no workspace mutation, no HELP/CMDHELPCHK mutation, no manual mutation.
