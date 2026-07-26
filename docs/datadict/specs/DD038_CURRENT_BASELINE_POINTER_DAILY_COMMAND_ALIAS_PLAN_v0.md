# DD-038 Current Baseline Pointer / Daily Command Alias Plan v0

Created UTC: `2026-05-27T20:24:15+00:00`

## Purpose

DD-038 makes the Data Dictionary redocumentation lane practical for day-to-day use by adding a current-baseline pointer and a standard status command.

The goal is to replace long paths like:

```powershell
& $py12 .\tools\datadict\baseline\baseline_status.py `
  --repo-root D:\code\ccode `
  --baseline D:\code\ccode\docs\datadict\baselines\DDBASE-stable-v2 `
  --out-dir ...
```

with:

```powershell
.\tools\datadict\dd-status.ps1
```

## Baseline pointer

DD-038 installs:

```text
docs/datadict/baselines/current_baseline.json
```

The pointer references:

```text
DDBASE-stable-v2
docs/datadict/baselines/DDBASE-stable-v2
```

## Active tools

```text
tools/datadict/baseline/baseline_pointer.py
tools/datadict/dd-status.ps1
```

## Daily usage

Basic daily status check:

```powershell
cd D:\code\ccode
.\tools\datadict\dd-status.ps1
```

Daily status with accepted baseline/proof artifact closure:

```powershell
.\tools\datadict\dd-status.ps1 -AcceptBaselineArtifacts
```

## Boundary

DD-038 is report-only. It does not edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, move/delete files, or replace baselines.

Changing the current-baseline pointer should be reviewed as a Data Dictionary governance action.
