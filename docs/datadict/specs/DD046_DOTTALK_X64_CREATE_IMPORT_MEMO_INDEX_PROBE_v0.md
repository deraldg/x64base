# DD-046 DotTalk++ X64 CREATE / IMPORT / Memo / Index Probe v0

Created UTC: `2026-05-27T22:15:03+00:00`

## Purpose

DD-046 proves the runtime-native x64/v64 catalog construction lane before rebuilding the real Data Dictionary catalog canonically.

Canonical lane under test:

```text
DotTalk++ CREATE X64
DotTalk++ IMPORT
DotTalk++ memo readback
DotTalk++ INDEX / tag creation
pydottalk readback against the DotTalk++-created x64 memo table
```

## Evidence basis

CREATE supports `CREATE X64 <name> (...)`; relative table names resolve through the configured DBF path slot; the created table is opened; and `M` fields trigger automatic memo attach after opening.

IMPORT requires an open table, treats the first CSV row as headers, maps headers to field names case-insensitively, appends blank records, sets mapped fields, and writes each record.

Current pydottalk is a DbArea/Table bridge suitable for readback and row-level mutation probes; it is not yet the canonical CREATE/IMPORT/INDEX driver.

## Probe target

```text
dottalkpp/data/metadata/datadict_create_probe/
```

## Probe table

```text
DDPROBE
  PROBEID C(20)
  TITLE   C(80)
  NOTES   M
```

## Boundary

Allowed:

```text
write only under dottalkpp/data/metadata/datadict_create_probe/
emit reports and probe scripts
read pydottalk/runtime-created probe table
```

Not allowed:

```text
active catalog mutation
datadict_sandbox mutation
HELP/META/CMDHELPCHK mutation
LMDB build
source edits
```

## Next

After DD-046 is green, DD-047 can plan the canonical Data Dictionary catalog rebuild using CREATE X64 + IMPORT.
