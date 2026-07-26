# DD-063 DotTalk++ DDICT Command Contract Plan v0

Created UTC: `2026-05-28T03:55:01+00:00`

## Purpose

DD-063 defines the report-only command contract for a future DotTalk++ `DDICT` read-only command family.

## Planned commands

```text
DDICT STATUS
DDICT TABLES
DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]
DDICT FIELDS <table>
DDICT TAGS <table>
DDICT REL <object-id-or-name> [IN|OUT|BOTH]
DDICT EVIDENCE <object-id-or-name>
DDICT HELP
```

## Boundary

Allowed:

```text
read DD-061/DD-062 reports
emit command contract reports
emit candidate usage contracts
emit runtime test plan
```

Not allowed:

```text
C++ source edits
runtime command registration
active catalog mutation
append/replace/delete/pack/zap
CDX/LMDB create/rebuild
HELP/META/CMDHELPCHK mutation
catalog regeneration
manual row repair
```
