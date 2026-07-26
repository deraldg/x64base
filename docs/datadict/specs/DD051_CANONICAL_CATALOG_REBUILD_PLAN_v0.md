# DD-051 Canonical Data Dictionary Catalog Rebuild Plan v0

Created UTC: `2026-05-28T02:09:54+00:00`

## Purpose

DD-051 plans the first real Data Dictionary catalog rebuild using the proven canonical lane:

```text
DD-039 DDL definitions
DD-040 projected rows
DotTalk++ CREATE X64
DotTalk++ IMPORT
memo readback
pydottalk verification
promotion gates
```

DD-051 is report-only. It does not create DBFs or import rows.

## Planned target

```text
dottalkpp/data/metadata/datadict_canonical_rebuild_v0/
```

## Boundary

Allowed:

```text
read DD-039/DD-040/DD-049/DD-050 evidence
emit rebuild plan
emit DD-052 execution contract
```

Not allowed:

```text
DBF creation
CSV import
CDX creation
LMDB build
active catalog promotion
C++ source edits
HELP/META/CMDHELPCHK mutation
```
