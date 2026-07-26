# DD-043 pydottalk / DotTalk++ Runtime Readback Execution v0

Created UTC: `2026-05-27T21:17:34+00:00`

## Purpose

DD-043 executes a read-only runtime readback lane against the sandbox Data Dictionary catalog DBFs.

It verifies:

```text
pydottalk import
sandbox DBF presence
runtime/header readback counts
field count parity
optional DD-042 generated pydottalk probe execution
```

## Authorized scope

Allowed:

```text
import pydottalk
read sandbox DBF/DBT files
capture runtime/introspection evidence
emit reports
```

Not allowed:

```text
DBF writes
REPLACE / APPEND / DELETE
CDX creation
LMDB writes
HELP/META/CMDHELPCHK mutation
active catalog promotion
source edits
```

## Promotion boundary

DD-043 does not promote the sandbox catalog. Active catalog promotion must be a separate package after DD-043 is green.
