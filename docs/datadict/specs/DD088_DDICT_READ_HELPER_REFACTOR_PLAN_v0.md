# DD-088 DDICT Read-Helper Refactor Plan v0

Created UTC: `2026-05-28T15:25:23+00:00`

## Purpose

DD-088 plans a safe refactor of the proven `DDICT` read surfaces into reusable read-only helper modules.

It is **plan-only**. It does not move code yet.

## Refactor goal

Keep command rendering stable while preparing shared read-only helpers for:

```text
catalog paths
existing CDX/LMDB artifact discovery
x64 DBF reading
DDOBJECT token resolution
simple row/string formatting
```

## Boundary

DD-088 does not edit C++ source, create new C++ files, edit build files, mutate active catalog data, create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair manual rows.
