# DD096Z-D2Z Candidate LMDB Space Recovery v0

Created UTC: `2026-05-29T16:36:30+00:00`

## Purpose

DD096Z-D2Z addresses the D2Y runtime blocker:

```text
BUILDLMDB: mdb_env_open failed: 112 (There is not enough space on the disk.)
```

D2Y proved candidate table identity and candidate CDX/tag creation. This package does not rewrite D2Y. It diagnoses candidate LMDB space usage and stages candidate-only cleanup scripts.

## Boundary

No cleanup by default. No active catalog replacement, no active DBF writes, no active CDX/LMDB rebuild, no source edits, no build edits, no workspace mutation, no HELP/CMDHELPCHK mutation, no manual mutation.
