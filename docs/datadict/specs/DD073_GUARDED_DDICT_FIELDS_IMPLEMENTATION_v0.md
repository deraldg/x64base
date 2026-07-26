# DD-073 Guarded DDICT FIELDS Implementation v0

Created UTC: `2026-05-28T13:54:05+00:00`

## Purpose

DD-073 implements the next read-only surface:

```text
DDICT FIELDS <table>
```

It uses the active catalog shape accepted by DD-072:

```text
DDOBJECT: OBJID, OBJTYPE, NAME, OWNER, STATUS, ...
DDATTR:   ATTRID, OBJID, ATTRNAME, ATTRVAL, ...
DDEDGE:   EDGEID, FROMOBJ, TOOBJ, EDGETYPE, EVID
```

## Boundary

Allowed with explicit `--apply-source-patch`:

```text
edit src/cli/cmd_ddict.cpp
read active catalog DBF rows at runtime
list CATALOG_FIELD rows for a requested table
preserve TAGS/REL/EVIDENCE pending behavior
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
