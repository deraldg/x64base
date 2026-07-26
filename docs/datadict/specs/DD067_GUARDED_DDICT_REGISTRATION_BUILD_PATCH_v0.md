# DD-067 Guarded DDICT Registration / Build Patch v0

Created UTC: `2026-05-28T04:37:27+00:00`

## Purpose

DD-067 patches the active DDICT registration and build targets accepted by DD-066R

Targets:

```text
src/cli/command_registry.cpp
src/CMakeLists.txt
```

## Boundary

Allowed with `--apply-patch`:

```text
patch active command registry file
patch active CMakeLists source list
write backups before patching
emit unified diff preview
```

Not allowed:

```text
active catalog mutation
DBF append/replace/delete/pack/zap
CDX/LMDB create/rebuild
HELP/META/CMDHELPCHK mutation
catalog regeneration
manual row repair
```

Build and runtime smoke remain separate after apply.
