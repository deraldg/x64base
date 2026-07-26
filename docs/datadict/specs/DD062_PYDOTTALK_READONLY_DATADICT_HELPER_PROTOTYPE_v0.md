# DD-062 pydottalk Read-Only Data Dictionary Helper Prototype v0

Created UTC: `2026-05-28T03:51:37+00:00`

## Purpose

DD-062 creates a guarded pydottalk read-only helper prototype for the active Data Dictionary catalog.

## Boundary

Allowed:

```text
emit helper as report artifact
optionally install tools/datadict/catalog/datadict_reader.py with --install-helper
run pydottalk read-only smoke
```

Not allowed:

```text
active catalog mutation
append/replace/delete/pack/zap
CDX/LMDB create or rebuild
runtime command registration
HELP/META/CMDHELPCHK mutation
```
