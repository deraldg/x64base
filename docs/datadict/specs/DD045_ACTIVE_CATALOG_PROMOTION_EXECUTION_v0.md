# DD-045 Active Catalog Promotion Execution v0

Created UTC: `2026-05-27T21:40:09+00:00`

## Purpose

DD-045 executes active Data Dictionary catalog promotion by copying the sandbox catalog DBF/DBT files into the active catalog path after backing up any existing active catalog.

## Authorized mutation

```text
source:
  dottalkpp/data/metadata/datadict_sandbox/

target:
  dottalkpp/data/metadata/datadict/

backup:
  dottalkpp/data/metadata/datadict_backups/<run-id>/
```

## Required execution flag

```text
--execute-promotion
```

Without that flag, DD-045 emits a guard manifest and does not mutate.

## Allowed

```text
create backup directory
backup existing active catalog files
replace active catalog directory
copy sandbox DBF/DBT files to active catalog
validate hashes against DD-044 sandbox inventory
validate active DBF row/field counts
emit rollback script
```

## Not allowed

```text
CDX creation
LMDB writes/builds
HELP/META/CMDHELPCHK mutation
source edits
runtime write operations
```

## Next

DD-046 should perform active catalog post-promotion runtime readback and status closure.
