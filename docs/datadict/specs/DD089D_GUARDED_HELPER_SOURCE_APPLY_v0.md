# DD-089D Guarded Helper Source Apply v0

Created UTC: `2026-05-28T17:00:46+00:00`

## Purpose

DD-089D applies DD-089C generated helper implementation candidates into installed helper source files.

It does not patch `cmd_ddict.cpp`, wire CMake, edit command registration, or change runtime behavior yet.

## Boundary

Allowed with explicit `--apply-helper-sources`:

```text
copy generated helper implementation candidates into:
  src/datadict/ddict_read_helpers.cpp
  src/datadict/ddict_catalog_paths.cpp
  src/datadict/ddict_dbf_reader.cpp
  src/datadict/ddict_object_resolver.cpp
backup replaced targets
```

Not allowed:

```text
cmd_ddict.cpp patch
CMake/build edits
runtime command registration edits
active catalog mutation
append/replace/delete/pack/zap
CDX/LMDB create/rebuild
HELP/META/CMDHELPCHK mutation
catalog regeneration
manual row repair
```
