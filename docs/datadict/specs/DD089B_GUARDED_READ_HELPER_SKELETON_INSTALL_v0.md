# DD-089B Guarded Read-Helper Skeleton Install v0

Created UTC: `2026-05-28T16:55:02+00:00`

## Purpose

DD-089B installs the generated DD-089A read-helper skeleton/interface artifacts into the repository source tree, but only when explicitly run with `--apply-install`.

It does not patch `cmd_ddict.cpp`, wire CMake, edit command registration, or migrate implementation code.

## Boundary

Allowed with explicit `--apply-install`:

```text
copy DD-089A skeleton headers/sources into include/datadict and src/datadict
copy candidate CMake fragment into docs/datadict/fragments
backup replaced targets if replacement is allowed
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
