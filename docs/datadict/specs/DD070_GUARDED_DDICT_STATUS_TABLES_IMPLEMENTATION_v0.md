# DD-070 Guarded DDICT STATUS / TABLES Implementation v0

Created UTC: `2026-05-28T13:29:20+00:00`

## Purpose

DD-070 implements the first real read-only `DDICT` surfaces:

```text
DDICT STATUS
DDICT TABLES
```

## Boundary

Allowed with explicit `--apply-source-patch`:

```text
edit src/cli/cmd_ddict.cpp
read active catalog file presence/bytes at runtime
preserve HELP/FIELDS/TAGS/OBJECTS/REL/EVIDENCE shell behavior
```

Not allowed:

```text
registry edits
build file edits
active catalog mutation
append/replace/delete/pack/zap
CDX/LMDB create/rebuild
HELP/META/CMDHELPCHK mutation
catalog regeneration
manual row repair
```
