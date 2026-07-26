# DD-039 Data Dictionary Catalog DBF/DDL Definition Plan v0

Created UTC: `2026-05-27T20:51:03+00:00`

## Purpose

DD-039 defines the planned Data Dictionary catalog DBF tables using DDL/table-definition terminology.

This package intentionally avoids using `schema` as the user-facing concept.

Correct terminology:

```text
DDL definition
catalog definition
DBF layout definition
table definition
field definition
index/tag definition
memo definition
```

Terminology boundary:

```text
WORKSPACE
  live/open area/session behavior

DDL
  structural table, field, memo, index/tag definition

Data Dictionary catalog
  metadata DBFs populated from accepted evidence after explicit authorization
```

## Planned sandbox first

First DBF population target, after later authorization:

```text
dottalkpp/data/metadata/datadict_sandbox/
```

Future active catalog target, only after readback and promotion authorization:

```text
dottalkpp/data/metadata/datadict/
```

## Planned catalog DBFs

```text
DDRUN
DDBASE
DDSOURCE
DDOBJECT
DDATTR
DDEDGE
DDEVID
DDGATE
DDREVIEW
DDARTIF
DDPROFILE
```

## Execution boundary

DD-039 is report-only.

It does not:

```text
create DBFs
write DBF rows
create CDX files
write LMDB data
run DotTalk++
run builds
mutate HELP/META/CMDHELPCHK
promote catalog data
```

## Required gates before DBF writes

```text
CATALOG_DEFINITION_REVIEWED
SANDBOX_PATH_CONFIRMED
ROW_PROJECTION_DRY_RUN_GREEN
WRITE_AUTHORIZED
```

## Required gates before active promotion

```text
READBACK_VALIDATED
PROMOTION_AUTHORIZED
```

## Next package

```text
DD-040 Catalog Row Projection Dry-Run
```

DD-040 should convert current accepted baseline/redocumentation artifacts into exact candidate row counts without writing DBFs.
