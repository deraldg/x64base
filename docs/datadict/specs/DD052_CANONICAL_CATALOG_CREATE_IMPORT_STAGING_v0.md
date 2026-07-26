# DD-052 Canonical Catalog CREATE X64 / IMPORT Staging v0

Created UTC: `2026-05-28T02:13:38+00:00`

## Purpose

DD-052 is the first guarded staging package for the real Data Dictionary catalog rebuild.

It uses DD-051's approved plan, validates projection CSV candidates, stages import-ready CSVs, and emits a DotTalk++ script that performs:

```text
SETPATH DBF metadata\datadict_canonical_rebuild_v0
CREATE X64 <catalog table>
IMPORT <staged CSV>
COUNT
```

## Target

```text
dottalkpp/data/metadata/datadict_canonical_rebuild_v0/
```

## Boundary

Allowed with explicit staging flag:

```text
create/replace only the canonical rebuild staging path
stage import CSVs
generate DotTalk++ CREATE/IMPORT script
```

Not allowed:

```text
active catalog promotion
HELP/META/CMDHELPCHK mutation
LMDB build
source edits
CDX/index creation
```
