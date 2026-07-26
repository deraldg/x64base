# DD-089G Guarded cmd_ddict Integration Apply v0

Created UTC: `2026-05-28T17:12:34+00:00`

## Purpose

DD-089G applies the reviewed `cmd_ddict.cpp` integration candidate produced by DD-089E/DD-089F.

It is narrowly scoped: `cmd_ddict.cpp` only.

## Boundary

Allowed with explicit `--apply-cmd-ddict`:

```text
backup src/cli/cmd_ddict.cpp
replace src/cli/cmd_ddict.cpp with reviewed candidate
```

Not allowed:

```text
helper source modifications
CMake/build edits
runtime command registration edits
active catalog mutation
append/replace/delete/pack/zap
CDX/LMDB create/rebuild
HELP/META/CMDHELPCHK mutation
catalog regeneration
manual row repair
```
