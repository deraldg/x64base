# DD-037 Status Command Closure Integration v0

## Purpose

DD-037 integrates DD-036 baseline-acceptance/proof-artifact closure into the daily Data Dictionary status command.

The immediate problem proven during the DDBASE-stable-v2 cycle was:

- DD-027 successfully accepted `DDBASE-stable-v2`.
- The final DD-034 check found six review rows.
- Manual inspection showed all six rows were baseline acceptance/proof artifacts:
  - three rows under `docs/datadict/baselines/DDBASE-stable-v2/`
  - three rows under `docs/datadict/review_queue/DD025-stable-v2-A-to-B/` and `DD026-stable-v2-A-to-B/`
- DD-036 strict mode correctly blocked until explicit acceptance.
- DD-036 accepted mode classified all six as accepted acceptance/proof artifacts.

DD-037 teaches the status layer how to consume DD-036 closure output and produce a final operator-facing status.

## Status model

DD-037 introduces these statuses:

| Status | Meaning |
|---|---|
| `PASS_NO_SOURCE_DRIFT` | DD-028 found no added, removed, changed, or review rows. |
| `PASS_WITH_ACCEPTED_BASELINE_ARTIFACTS` | DD-028 found only baseline acceptance/proof artifacts and DD-036 accepted them. |
| `REVIEW_BASELINE_ARTIFACTS_UNACCEPTED` | DD-028 found only baseline acceptance/proof artifacts but DD-036 has not accepted them. |
| `REVIEW_REAL_CHANGE` | DD-028 found changes not fully explained by DD-036 closure. |
| `TOOL_ERROR` | Required input missing or unreadable. |

## Boundary

DD-037 is report-only. It does not accept or replace a baseline, edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, move/delete files, or promote dictionary facts.

## Expected use

For the DDBASE-stable-v2 closure case:

```powershell
& $py12 .	ools\datadictaselineaseline_status_closure.py `
  --dd034 D:\code\ccode\docs\datadicteports\DD034-check-DDBASE-stable-v2-current `
  --dd036 D:\code\ccode\docs\datadicteview_queue\DD036-stable-v2-acceptance-artifact-accepted-v0 `
  --out-dir D:\code\ccode\docs\datadicteports\DD037-status-closure-v2-v0 `
  --run-id DD037-status-closure-v2-v0 `
  --baseline-id DDBASE-stable-v2 `
  --profile ENGINE `
  --profile PROFESSIONAL
```

Expected result:

```text
status: PASS_WITH_ACCEPTED_BASELINE_ARTIFACTS
review_rows: 6
accepted_closure_rows: 6
unexplained_rows: 0
```
