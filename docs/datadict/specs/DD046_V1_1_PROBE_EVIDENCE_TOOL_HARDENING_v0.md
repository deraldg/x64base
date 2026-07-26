# DD-046 v1.1 Probe Evidence Tool Hardening v0

Created UTC: `2026-05-28T01:27:46+00:00`

## Purpose

DD-046 v1.1 fixes the evidence tool, not the runtime.

It addresses two observed issues after DD-048 runtime proof:

```text
1. pydottalk readback crashed while writing JSON because MemoKind is not JSON serializable.
2. structural inspection was too brittle around memo sidecar detection/casing.
```

## Boundary

Allowed:

```text
replace tools/datadict/catalog/dottalk_x64_create_import_probe.py
emit reports
read probe table
```

Not allowed:

```text
C++ source edits
active catalog mutation
datadict_sandbox mutation
HELP/META/CMDHELPCHK mutation
LMDB build
```
