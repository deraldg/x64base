# DD-058 Controlled Active Catalog Promotion Execution v0

Created UTC: `2026-05-28T03:29:34+00:00`

## Purpose

DD-058 is the first controlled package authorized to promote the staged Data Dictionary catalog into the active metadata catalog.

It requires DD-057 readiness and explicit `--execute-promotion`.

## Execution behavior

```text
1. Validate DD-057 readiness.
2. Validate staged DBF/DTX and CDX/LMDB artifacts.
3. Create timestamped rollback backup.
4. Generate restore script.
5. Copy staged DBF/DTX artifacts into active metadata/datadict.
6. Adopt existing table CDX/LMDB artifacts in place.
7. Optionally run pydottalk post-promotion row-count verification.
8. Emit DotTalk++ post-promotion runtime verification script.
```

## Boundary

Allowed with explicit execution flag:

```text
active metadata/datadict DBF/DTX replacement
rollback backup creation
restore script creation
post-promotion pydottalk readback
```

Still disallowed:

```text
source edits
HELP/META/CMDHELPCHK mutation
catalog content regeneration
manual row repair
```
