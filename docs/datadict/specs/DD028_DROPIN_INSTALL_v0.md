# DD-028 Repo Drop-in

Installs the one-step accepted-baseline redocumentation check.

Active tool:

```text
tools/datadict/baseline/baseline_check.py
```

Smoke:

```powershell
& $py12 .	ools\datadictaselineaseline_check.py --help
```

Run against accepted baseline:

```powershell
& $py12 .	ools\datadictaselineaseline_check.py `
  --repo-root D:\code\ccode `
  --baseline D:\code\ccode\docs\datadictaselines\DDBASE-stable-v0 `
  --out-dir D:\code\ccode\docs\datadicteports\DD028-check-current-v0 `
  --run-id DD028-check-current-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```
