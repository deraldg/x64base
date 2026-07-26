# DD-081 Guarded DDICT EVIDENCE Implementation v0

Created UTC: `2026-05-28T15:00:05+00:00`

## Purpose

DD-081 implements the read-only surface:

```text
DDICT EVIDENCE <object-id-or-name>
```

It uses the DD-080 accepted model:

```text
resolve token to DDOBJECT row
read DDEVID direct evidence rows
read DDATTR object attribute rows
decorate DDEVID with DDSOURCE/DDARTIF where available
bound output
```

## Boundary

Allowed with explicit `--apply-source-patch`:

```text
edit src/cli/cmd_ddict.cpp
read active catalog DBF rows at runtime
preserve STATUS/TABLES/FIELDS/TAGS/REL behavior
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
