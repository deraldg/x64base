# DD-066R DDICT Registration / Build Target Refinement v0

Created UTC: `2026-05-28T04:30:07+00:00`

## Purpose

DD-066R refines DD-066 discovery output so DD-067 patches only active registration/build targets

The DD-066 discovery was green, but the build heuristic selected a legacy/generated `.vcxproj` path ahead of the active source build file. DD-066R corrects the patch target policy before any edit package.

## Boundary

Allowed:

```text
read DD-066 reports
classify legacy/generated build paths
select accepted active registration target
select accepted active build target
emit refined report-only patch plan
optionally write readiness markdown
```

Not allowed:

```text
C++ source edits
build file edits
runtime command registration
active catalog mutation
DBF/CDX/LMDB mutation
HELP/META/CMDHELPCHK mutation
```
