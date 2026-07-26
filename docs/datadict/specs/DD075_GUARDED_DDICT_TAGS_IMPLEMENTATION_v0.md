# DD-075 Guarded DDICT TAGS Implementation v0

Created UTC: `2026-05-28T14:20:23+00:00`

## Purpose

DD-075 implements the read-only surface:

```text
DDICT TAGS <table>
```

It uses the DD-074 accepted model:

```text
active catalog path
table DBF presence
CDX artifact presence
LMDB mirror presence
CATALOG_TAG rows from DDOBJECT
```

## Boundary

Allowed with explicit `--apply-source-patch`:

```text
edit src/cli/cmd_ddict.cpp
read active catalog DBF rows at runtime
read file/directory presence for existing CDX/LMDB artifacts
preserve STATUS/TABLES/FIELDS behavior
preserve REL/EVIDENCE pending behavior
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
