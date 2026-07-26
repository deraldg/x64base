# DD-025 Drop-in Install Note v0

Install from repo root:

```powershell
Expand-Archive .\datadict_repo_dropin_dd025_v0.zip -DestinationPath . -Force
```

Smoke:

```powershell
& $py12 .	ools\datadicteview\change_classifier.py --help
```

Classify the stable A-to-B diff:

```powershell
& $py12 .	ools\datadicteview\change_classifier.py `
  --dd023 D:\code\ccode\docs\datadicteports\DDRUN-stable-A-to-B-diff-v0 `
  --out-dir D:\code\ccode\docs\datadicteview_queue\DD025-stable-A-to-B-v0 `
  --run-id DD025-stable-A-to-B-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```
