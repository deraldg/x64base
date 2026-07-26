# DD-023 Change Detection / Diff Contract v0

Status: REPORT_ONLY / SKELETON_CREATED  
Created UTC: 2026-05-27T17:03:45+00:00

## Purpose

DD-023 adds the first repeatable change-detection layer to the DotTalk++ / x64base
Data Dictionary redocumentation lane.

DD-022 proved that the repo-level orchestrator can perform a local dry-run scan.
DD-023 answers the next necessary question:

> What changed between two redocumentation runs?

This is not a one-time documentation pass. It is the beginning of the recurring
redocumentation audit loop.

## Inputs

DD-023 expects two DD-022 run manifests or run directories:

```text
base DD-022 run
candidate DD-022 run
```

Each run should contain or reference:

```text
dd022_redoc_run_manifest.json
dd022_source_inventory.csv
```

## Outputs

```text
dd023_redoc_diff_manifest.json
dd023_diff_summary.csv
dd023_file_diff.csv
dd023_change_by_kind.csv
dd023_review_queue.csv
```

## Change kinds

```text
ADDED
  Candidate contains a file/object absent from base.

REMOVED
  Base contains a file/object absent from candidate.

CHANGED
  File/object exists in both runs but content hash changed.

UNCHANGED
  Path and hash match. Not emitted to the review queue by default.
```

## Review discipline

DD-023 deliberately produces REVIEW when any added, removed, or changed source
artifact is found. That is not a failure. It is the correct signal that the
redocumentation system has work to do.

Typical follow-up lanes:

```text
source/header changed        -> rerun source-contract / HELP / runtime-proof checks
script changed               -> review DD_SCRIPT boundary and lifecycle role
schema/rule changed          -> rerun schema/rule extractors and validation plan
HELP/manual/doc changed      -> rerun HELP/manual link checks
data/proof transcript changed -> rerun transcript parser and proof gates
```

## Boundaries

DD-023 is report-only.

It does not:

```text
edit source
launch DotTalk++
run CMDHELP BUILD
run CMDHELPCHK
mutate HELP/META/CMDHELPCHK
write DBF/CDX/LMDB/catalog rows
promote dictionary facts
regenerate manuals
```

## Active tool target

When installed into the repo, the active tool should live at:

```text
tools/datadict/diff/redoc_diff.py
```

Package-preserved copies may live under:

```text
docs/datadict/packages/DD-023_...
```

## Local usage pattern

```powershell
$py12 = "D:\code\ccode\build\vcpkg_installed\x64-windows\tools\python3\python.exe"

& $py12 .\tools\datadict\diff\redoc_diff.py `
  --base D:\code\ccode\docs\datadict\reports\DDRUN-plan-only-v0 `
  --candidate D:\code\ccode\docs\datadict\reports\DDRUN-local-smoke-v0 `
  --out-dir D:\code\ccode\docs\datadict\reports\DDRUN-local-smoke-v0-diff `
  --run-id DD023-local-smoke-diff-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```

For the specific local runs just shown, comparing plan-only to full-scan will
produce a large REVIEW queue because plan-only has no source inventory. That is
expected. A more meaningful diff is between two full DD-022 runs.
