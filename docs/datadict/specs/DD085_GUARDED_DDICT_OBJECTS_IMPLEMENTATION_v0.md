# DD-085 Guarded DDICT OBJECTS Implementation v0

Created UTC: `2026-05-28T15:15:17+00:00`

## Purpose

DD-085 implements the read-only surface:

```text
DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]
```

It uses the DD-084 accepted model:

```text
read DDOBJECT rows
read DDATTR rows for attribute counts
show bounded object browsing output
support TYPE and PROFILE filters
preserve STATUS/TABLES/FIELDS/TAGS/REL/EVIDENCE behavior
```

## Boundary

Allowed with explicit `--apply-source-patch`:

```text
edit src/cli/cmd_ddict.cpp
read active catalog DBF rows at runtime
preserve existing DDICT read surfaces
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
