# DD-078 Guarded DDICT REL Implementation v0

Created UTC: `2026-05-28T14:45:06+00:00`

## Purpose

DD-078 implements the read-only surface:

```text
DDICT REL <object-id-or-name> [IN|OUT|BOTH]
```

It uses the DD-077 accepted model:

```text
resolve token to DDOBJECT row
read DDEDGE rows
decorate edges with DDOBJECT metadata
show incoming/outgoing relationships with bounded output
```

## Boundary

Allowed with explicit `--apply-source-patch`:

```text
edit src/cli/cmd_ddict.cpp
read active catalog DBF rows at runtime
preserve STATUS/TABLES/FIELDS/TAGS behavior
preserve EVIDENCE pending behavior
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
