# DD-067R Local-Pattern DDICT Registration / Build Patch Repair v0

Created UTC: `2026-05-28T04:43:56+00:00`

## Purpose

DD-067R repairs DD-067 by using local-pattern probes for command registration and CMake source inclusion.

DD-067 found:

```text
include insertion possible
registration template not safely mirrorable
src/CMakeLists.txt has no explicit cli/cmd_*.cpp source-list anchor
```

DD-067R adds:

```text
multi-line registration block probing
candidate block report
CMake glob detection
local source anchor fallback
```

## Boundary

Allowed with `--apply-patch`:

```text
patch active command registry file if local pattern is recognized
patch active CMakeLists only if needed and safely anchored
write backups before patching
emit unified diff preview
```

Not allowed:

```text
active catalog mutation
DBF/CDX/LMDB mutation
HELP/META/CMDHELPCHK mutation
catalog regeneration
manual row repair
```
