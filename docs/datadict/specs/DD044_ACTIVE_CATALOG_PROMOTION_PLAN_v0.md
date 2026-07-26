# DD-044 Active Catalog Promotion Plan v0

Created UTC: `2026-05-27T21:34:03+00:00`

## Purpose

DD-044 defines the authority gate and execution plan for promoting the sandbox Data Dictionary catalog to the active catalog location.

DD-044 is plan-only. It does not promote.

## Source sandbox

```text
dottalkpp/data/metadata/datadict_sandbox/
```

## Future active catalog target

```text
dottalkpp/data/metadata/datadict/
```

## Future backup root

```text
dottalkpp/data/metadata/datadict_backups/
```

## Required preconditions

```text
DD-041 sandbox DBF creation/readback green
DD-042 sandbox DBF inspection green
DD-043 v1.1 pydottalk runtime readback green
DotTalk++ direct USE/COUNT/TUP readback evidence acknowledged
Sandbox DBF inventory complete
Explicit promotion execution authorization for DD-045
```

## DD-044 boundary

DD-044 does not:

```text
copy sandbox DBFs to active catalog
replace active catalog
create backup
write DBFs
create CDX files
write LMDB data
mutate HELP/META/CMDHELPCHK
edit source
promote dictionary facts
```

## Next

DD-045 may execute active catalog promotion only after explicit promotion execution authorization.
