# X64Base Workflow

## Roles

`D:\code\ccode`
Development intake repo. This can stay messy. Research, backups, scaffolding,
alternate layouts, and work-in-progress all live here.

`D:\code\ccode\x64base`
Canonical staging repo. This is the only repo Codex should edit for cleanup,
promotion, and Git work. Build/test decisions should be made here first. This
is the normal inner-loop repo.

`C:\x64base`
Disposable runtime/build mirror. Do not treat this as a second source of truth.
Refresh it from `D:\code\ccode\x64base`, then build or smoke-test there if you
want the `C:` layout. This is a checkpoint mirror, not an every-edit mirror.

`GitHub`
Push only from `D:\code\ccode\x64base` after staging is clean and verified.

## Rules

1. Do not hand-edit both `D:\code\ccode\x64base` and `C:\x64base`.
2. Codex works in `D:\code\ccode\x64base`.
3. `C:\x64base` is refreshed from `D:\code\ccode\x64base` by script.
4. Git status, staging, commits, and push happen only in `D:\code\ccode\x64base`.
5. If something is fixed in `C:\x64base` during a smoke test, copy that fix back
   into `D:\code\ccode\x64base` immediately or it will drift again.
6. Do not mirror to `C:\x64base` for every small improvement. Refresh it only at
   checkpoints.

## Recommended Loop

1. Intake or review changes from `D:\code\ccode`.
2. Apply the approved subset into `D:\code\ccode\x64base`.
3. Build, inspect, and iterate in `D:\code\ccode\x64base`.
4. Refresh `C:\x64base` only at a checkpoint.
5. Run the `C:\x64base` build/runtime smoke when you want the live staging-path
   proof.
6. If the smoke reveals a bug, fix it back in `D:\code\ccode\x64base`.
7. When green, commit and push from `D:\code\ccode\x64base`.

Common commands:

```powershell
pwsh .\tools\stage_status.ps1
pwsh .\tools\build_stage.ps1
pwsh .\datarun.ps1
```

`build_stage.ps1` uses the `stage` CMake preset and auto-reconfigures when a
copied build directory still points at another source tree such as `C:\x64base`.

## Checkpoints

Refresh `C:\x64base` only when one of these is true:

1. Several related fixes have accumulated in `D:\code\ccode\x64base`.
2. You need a path-sensitive runtime proof in the real `C:` layout.
3. You are preparing for a release/staging decision.
4. You want one final mirror proof before GitHub promotion.

## Promotion Steps

Dry run:

```powershell
pwsh .\tools\sync_stage_to_c.ps1 -WhatIf
```

Real mirror:

```powershell
pwsh .\tools\sync_stage_to_c.ps1
```

Then in `C:\x64base`:

```powershell
./datarun
```

or rebuild there if you still want a separate `C:` build proof.

## Why This Is Safer

- It removes three-way drift between `ccode`, `ccode\x64base`, and `C:\x64base`.
- It gives Codex one repo to reason about.
- It makes runtime surprises reproducible because `C:` becomes a mirror, not a
  second editing surface.
