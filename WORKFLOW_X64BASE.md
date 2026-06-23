# X64Base Workflow

## Roles

`D:\code\ccode`
Primary development repo. New code, real fixes, active data work, and ongoing
development happen here first. Runtime data lives under its `dottalkpp`
subtree.

`D:\code\ccode\x64base\dottalkpp`
Curated GitHub staging tree. This is not the authoring source of truth. It is a
publishable subset promoted from the development tree, then verified, committed,
and pushed.

`C:\x64base`
Checkpoint runtime mirror. Refresh it from `D:\code\ccode\x64base` only when a
path-sensitive smoke or release-style runtime proof is needed.

`GitHub`
Push only from `D:\code\ccode\x64base` after staging is clean and verified.

## Direction Of Travel

Normal direction:

`D:\code\ccode` -> `D:\code\ccode\x64base` -> `C:\x64base`

Do not treat `C:\x64base` or `D:\code\ccode\x64base\dottalkpp` as the place
where ordinary development starts.

## Rules

1. Code fixes happen in `D:\code\ccode` first.
2. `D:\code\ccode\x64base\dottalkpp` is a curated promotion target, not the main development surface.
3. `C:\x64base` is a mirror only. Never let it become a second working tree.
4. Git status, staging, commits, PRs, and push happen only in `D:\code\ccode\x64base`.
5. If a smoke test in `C:\x64base` uncovers a defect, fix it in `D:\code\ccode\dottalkpp`, then promote again.
6. Do not hand-edit the same change in both dev and stage.

## Promotion Policy

### Code

- Promote source, headers, CMake files, scripts, docs, and runtime support from
  `D:\code\ccode` into `D:\code\ccode\x64base`.
- Prefer targeted promotion over root-level blanket copying.

### DBF Layout

- The curated layout in `x64base` is the publish target.
- If dev still has older folder placement, reconcile dev to match the curated
  `x64base` layout before the next long development phase.
- Do not run a blind full data mirror from dev to stage until that layout
  normalization is complete.

### Index Containers

- Keep and promote `cdx`, `cnx`, `idx`, and `inx` files when they are validated.
- These are portable distribution assets and belong in the staged tree.

### LMDB Environments

- LMDB env payloads are local runtime artifacts.
- Oversized `data.mdb` files in dev are not publish assets.
- Stage may keep local rebuilt LMDB envs for testing, but GitHub should only get
  the portable index containers.
- If dev has stale 1 GiB LMDB envs and stage has validated 128 MiB rebuilds,
  use stage as the one-time cleanup reference and realign dev accordingly.

### Holdouts

- `biblebase` and `cascade_precision_erp` stay outside the GitHub promotion path
  for now.

## Recommended Loop

1. Make or review changes in `D:\code\ccode\dottalkpp`.
2. Promote the approved subset into `D:\code\ccode\x64base`.
3. Build and smoke-test in `D:\code\ccode\x64base`.
4. Refresh `C:\x64base` only at a checkpoint.
5. Run the `C:\x64base` proof if path-sensitive runtime behavior matters.
6. Commit and push from `D:\code\ccode\x64base`.

## Current Reality

At the moment, some cleanup exists only in stage:

- curated workspace and support-data layout
- reduced LMDB mapsizes in stage
- GitHub-safe LMDB handling

That means the next cleanup step is asymmetric:

1. keep dev as the code source of truth
2. use stage as the reference for one-time data-layout normalization
3. once dev matches the curated layout, resume the normal `dev -> stage` flow

## Common Commands

From `D:\code\ccode\x64base`:

```powershell
pwsh .\tools\stage_status.ps1
pwsh .\tools\build_stage.ps1
pwsh .\datarun.ps1
pwsh .\tools\promote_dev_dottalkpp_to_stage.ps1 -WhatIf
```

Code-first promotion is the safe default. Data lanes must be named explicitly:

```powershell
pwsh .\tools\promote_dev_dottalkpp_to_stage.ps1 -WhatIf -DataLane indexes,metadata
```

## C Mirror

Dry run:

```powershell
pwsh .\tools\sync_stage_to_c.ps1 -WhatIf
```

Real mirror:

```powershell
pwsh .\tools\sync_stage_to_c.ps1
```
