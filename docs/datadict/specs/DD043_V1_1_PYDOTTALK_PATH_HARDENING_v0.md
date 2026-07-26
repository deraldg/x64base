# DD-043 v1.1 pydottalk Path Hardening v0

Created UTC: `2026-05-27T21:29:47+00:00`

## Purpose

DD-043 v1.1 hardens the runtime readback tool so it automatically prepends:

```text
<repo-root>\build\python
```

to `sys.path` before importing `pydottalk`.

This removes the need to manually set `PYTHONPATH` for the normal readback command.

## Boundary

Allowed:

```text
read sandbox DBF/DBT files
import pydottalk
capture runtime/introspection evidence
```

Not allowed:

```text
DBF writes
CDX creation
LMDB writes
HELP/META/CMDHELPCHK mutation
active catalog promotion
source edits
```

## Next

After DD-043 v1.1 is green without manual PYTHONPATH, DD-044 can plan active catalog promotion.
