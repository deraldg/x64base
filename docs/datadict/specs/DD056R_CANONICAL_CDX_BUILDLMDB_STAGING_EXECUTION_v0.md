# DD-056R Canonical CDX / ADDTAG / INFO / BUILDLMDB Staging Execution v0

Created UTC: `2026-05-28T03:13:40+00:00`

## Purpose

DD-056R executes the corrected canonical CDX/LMDB workflow against the staged catalog only:

```text
CDX CREATE
CDX ADDTAG <tag>
CDX INFO
CDX TAGS
BUILDLMDB CLEAN YES
SET INDEX TO <table>
SET ORDER TO TAG <tag>
LIST
```

## Boundary

Allowed:

```text
write staging runtime script
manual DotTalk++ CDX/ADDTAG/INFO/BUILDLMDB execution against staged catalog
verify CDX/LMDB artifacts and proof text
```

Not allowed:

```text
active catalog promotion
source edits
HELP/META/CMDHELPCHK mutation
production catalog replacement
```
