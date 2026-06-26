# Reverse Normalization Plan

## Goal

Realign the development runtime data under `D:\code\ccode\dottalkpp\data` to
the curated staging reference under `D:\code\ccode\x64base\dottalkpp\data`
without destroying dev-only roots that are intentionally outside the GitHub
edition.

Normal code flow remains:

`D:\code\ccode` -> `D:\code\ccode\x64base` -> `C:\x64base`

This reverse pass is a one-time cleanup because some of the data curation was
completed in stage first.

## Current Findings

### DBF

Dev roots:

- `cobol`
- `dev`
- `help`
- `memo`
- `sandbox`
- `vfp`
- `x32`
- `x64`

Stage roots:

- `dev`
- `memo`
- `x32`
- `x64`

Implication:

- Stage has the cleaned publish/runtime subset.
- Dev still carries old `help`, `sandbox`, `cobol`, and `vfp` DBF roots.
- Reverse normalization should mirror only `dev`, `memo`, `x32`, and `x64`
  from stage back into dev.
- Dev-only roots should remain in dev, but they are no longer the canonical
  publish layout.

Notable drift:

- Stage has `dbf\dev\x32\HIERNODE.dbf`, `dbf\dev\X64SAMPLE.*`,
  `dbf\dev\X64_ALL_TYPES.*` that do not exist in the matching dev lane.
- Stage has `dbf\x64\memo_sample\*` and `dbf\x64\contraints.ini`.
- Dev still has older `dbf\x64\MEMO_*` and `dbf\x64\memo\*` placements.

### Indexes

Dev roots:

- `cmdhelp`
- `datadict`
- `help`
- `locale`
- `manuals`
- `memo`
- `messaging`
- `meta`
- `metadata`
- `sandbox`
- `vfp`
- `x32`
- `x64`

Stage roots:

- `datadict`
- `help`
- `locale`
- `manuals`
- `memo`
- `messaging`
- `metadata`
- `vfp`
- `x32`
- `x64`

Implication:

- `cmdhelp`, `meta`, and `sandbox` are dev-only roots and should not be pushed
  forward into the GitHub edition.
- Reverse normalization should mirror the stage roots above back into the
  matching dev roots.

Notable drift:

- `indexes\x64` in dev still contains `MEMO_FOX26.cdx` which is not in stage.
- Dev still has sandbox-only CDX/INX assets that should stay dev-only.

### LMDB

Dev roots:

- ad hoc one-off roots such as `adbf_cg_ok.cdx.d`, `BIGCHAR_TEST.cdx.d`,
  `HIERNODE.cdx.d`, `M372E_ART.cdx.d`, `STUDENTS.cdx.d`, `X64SAMPLE.cdx.d`
- `backups`
- `cmdhelp`
- `datadict`
- `help`
- `locale`
- `manuals`
- `memo`
- `messaging`
- `metadata`
- `sandbox`
- `x32`
- `x64`

Stage roots:

- `cmdhelp`
- `datadict`
- `help`
- `locale`
- `manuals`
- `memo`
- `messaging`
- `metadata`
- `x32`
- `x64`

Implication:

- Reverse normalization should mirror only the curated stage roots above.
- Dev-only LMDB roots such as `sandbox`, `backups`, and one-off
  `.cdx.d` roots remain in dev unless explicitly cleaned later.

Important size result:

- Dev still has many 1 GiB LMDB maps in `locale`, `messaging`, `metadata`,
  `sandbox`, and `x64`.
- Stage has validated 128 MiB maps for the curated roots.

Structural problem in dev metadata lane:

- nested duplicate path:
  - `lmdb\metadata\SOURCE_COMMENT\SOURCE_COMMENT\...`
- nested duplicate container path:
  - `lmdb\metadata\SYSCMD.cdx.d\SYSCMD.cdx.d\...`

Stage does not have those nested duplicates.

## Action

Use stage as the reference and mirror only these subdirectories back into dev:

### DBF lanes to mirror

- `dev`
- `memo`
- `x32`
- `x64`

### Index lanes to mirror

- `datadict`
- `help`
- `locale`
- `manuals`
- `memo`
- `messaging`
- `metadata`
- `vfp`
- `x32`
- `x64`

### LMDB lanes to mirror

- `cmdhelp`
- `datadict`
- `help`
- `locale`
- `manuals`
- `memo`
- `messaging`
- `metadata`
- `x32`
- `x64`

## Safety Rule

Mirror subdirectories individually, not the whole `dbf`, `indexes`, or `lmdb`
root. That preserves dev-only roots like `sandbox`, `cobol`, and `backups`
while normalizing the curated lanes.

## Tool

Use:

```powershell
pwsh .\tools\normalize_stage_data_back_to_dev.ps1 -WhatIf
pwsh .\tools\normalize_stage_data_back_to_dev.ps1
```

This targets only the curated stage subdirectories listed above.
