# DD-026 Data Dictionary Drop-in Install Note v0

Install from repository root:

```powershell
cd D:\code\ccode
Expand-Archive .\datadict_repo_dropin_dd026_v0.zip -DestinationPath . -Force
```

Smoke test:

```powershell
& $py12 .\tools\datadict\review\triage_report.py --help
```

Clean queue test:

```powershell
& $py12 .\tools\datadict\review\triage_report.py `
  --dd025 D:\code\ccode\docs\datadict\review_queue\DD025-stable-A-to-B-v0 `
  --out-dir D:\code\ccode\docs\datadict\review_queue\DD026-stable-A-to-B-v0 `
  --run-id DD026-stable-A-to-B-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```

Intentional blocked review test:

```powershell
& $py12 .\tools\datadict\review\triage_report.py `
  --dd025 D:\code\ccode\docs\datadict\review_queue\DD025-plan-to-full-v0 `
  --out-dir D:\code\ccode\docs\datadict\review_queue\DD026-plan-to-full-v0 `
  --run-id DD026-plan-to-full-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```

Boundary: report-only. No source, HELP, META, CMDHELPCHK, DBF/CDX/LMDB/catalog mutation.
