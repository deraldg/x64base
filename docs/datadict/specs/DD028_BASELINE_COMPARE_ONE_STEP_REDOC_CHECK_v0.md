# DD-028 Baseline Compare Command / One-Step Redoc Check v0

## Purpose

DD-028 turns the accepted DD-027 baseline into a daily working command. It runs the report-only redocumentation loop against the accepted baseline and emits one status:

```text
PASS
REVIEW
BLOCKED_REVIEW
TOOL_ERROR
```

The command is deliberately report-only. It does not edit source, run a build, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB catalog data, or replace the accepted baseline.

## Pipeline

```text
accepted DD-027 baseline
  -> DD-024 stable scan
  -> DD-023 diff against baseline scan
  -> DD-025 change classification
  -> DD-026 triage report
  -> DD-028 summary / boundary ledger / next action
```

## Active tool

```text
tools/datadict/baseline/baseline_check.py
```

## Recommended command

```powershell
& $py12 .	ools\datadictaselineaseline_check.py `
  --repo-root D:\code\ccode `
  --baseline D:\code\ccode\docs\datadictaselines\DDBASE-stable-v0 `
  --out-dir D:\code\ccode\docs\datadicteports\DD028-check-current-v0 `
  --run-id DD028-check-current-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```

## Expected clean result

When nothing meaningful changed since `DDBASE-stable-v0`:

```text
status: PASS; added: 0; removed: 0; changed: 0; review_rows: 0; high: 0
```

## Boundary

DD-028 is a check, not a promotion. Baseline replacement, catalog import, HELP mutation, and documentation publication remain separate explicit gates.
