# DD-034 Daily Redoc Check / Baseline Status Command v0

## Purpose

DD-034 adds the day-to-day Data Dictionary status command. It answers one ordinary maintenance question:

> Is the repository still aligned with the accepted Data Dictionary baseline?

DD-034 wraps the existing report-only pipeline rather than replacing it:

1. DD-028 accepted-baseline compare.
2. DD-033 baseline self-artifact closure, when DD-028 reports review rows.
3. A single daily status manifest and Markdown report.

## Status vocabulary

| Status | Meaning |
|---|---|
| `PASS_NO_SOURCE_DRIFT` | DD-028 reports no added, removed, changed, or review rows. |
| `REVIEW_SELF_ARTIFACT_ONLY` | DD-028 reports review rows, but DD-033 proves all are baseline/review self-artifacts. |
| `REVIEW_SELF_ARTIFACT_ACCEPTED` | Same as above, with explicit `--accept-self-artifacts` used for the DD-034 report packet only. |
| `REVIEW_REAL_CHANGE` | DD-028 reports changes and DD-033 finds non-self rows or cannot classify them as baseline self-artifacts. |
| `BLOCKED_SCRIPT_BOUNDARY` | Reserved for future DD-029/DD-030 integration when real changes are script-boundary blockers. |
| `TOOL_ERROR` | A child tool failed or a required manifest could not be read. |
| `PLAN_ONLY` | DD-034 wrote a step plan without running child tools. |

## Boundaries

DD-034 is report-only. It does not edit source, launch DotTalk++, build, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, move/delete files, accept a new baseline, or replace an existing baseline.

## Active tool

`tools/datadict/baseline/baseline_status.py`

## Inputs

- `--repo-root`: repository root to scan.
- `--baseline`: accepted DD-027 baseline directory or manifest.
- `--out-dir`: output directory for the DD-034 status packet.
- `--run-id`: stable run id.
- `--profile`: profile labels such as `ENGINE` and `PROFESSIONAL`.
- `--accept-self-artifacts`: marks self-artifact-only churn as accepted within the report packet only.

## Outputs

- `dd034_daily_redoc_status_manifest.json`
- `DD034_DAILY_REDOC_STATUS_REPORT.md`
- `dd034_summary.csv`
- `dd034_step_ledger.csv`
- `dd034_boundary_ledger.csv`
- child output folders `dd028/` and, when needed, `dd033/`

## Intended daily usage

```powershell
cd D:\code\ccode
$py12 = "D:\code\ccode\build\vcpkg_installed\x64-windows\tools\python3\python.exe"

& $py12 .\tools\datadict\baseline\baseline_status.py `
  --repo-root D:\code\ccode `
  --baseline D:\code\ccode\docs\datadict\baselines\DDBASE-stable-v1 `
  --out-dir D:\code\ccode\docs\datadict\reports\DD034-daily-current-v0 `
  --run-id DD034-daily-current-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```
