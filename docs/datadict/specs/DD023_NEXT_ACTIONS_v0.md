# DD-023 Next Actions v0

1. Install the active diff tool under:

```text
tools/datadict/diff/redoc_diff.py
```

2. Run a harmless first diff between the two local DD-022 runs:

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

3. Expect REVIEW if comparing plan-only to full-scan. That is not red.

4. For a meaningful green-ish baseline, run DD-022 twice without source changes and compare those two full-scan runs.

5. After DD-023 is locally green, create DD-024 to add review-disposition tracking.
