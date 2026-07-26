# DD-089H Guarded DDICT Helper Build Wiring v0

Created UTC: `2026-05-28T17:16:08+00:00`

## Purpose

DD-089H wires the extracted Data Dictionary helper `.cpp` files into the `dottalkpp` build.

It is narrowly scoped to `src/CMakeLists.txt`.

## Boundary

Allowed with explicit `--apply-build-wiring`:

```text
backup src/CMakeLists.txt
add guarded target_sources(dottalkpp PRIVATE ...) helper-source block if not already wired
```

Not allowed:

```text
cmd_ddict.cpp patch
helper source modifications
runtime command registration edits
active catalog mutation
append/replace/delete/pack/zap
CDX/LMDB create/rebuild
HELP/META/CMDHELPCHK mutation
catalog regeneration
manual row repair
```
