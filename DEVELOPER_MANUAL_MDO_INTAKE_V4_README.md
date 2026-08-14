# Developer Manual Bundle MDO Intake v4

Use v4 only.

Fix history:
- v1 failed under PowerShell StrictMode when a single directory did not expose `.Count`.
- v2 created destination folders but could fail to copy child files.
- v3 fixed copy behavior but used `[System.IO.Path]::GetRelativePath`, which is unavailable in older Windows PowerShell/.NET.
- v4 replaces `GetRelativePath` with a compatible URI-based helper.

## Use from D:\code\ccode

Extract:

```powershell
Expand-Archive .\dottalkpp_developer_manual_mdo_intake_v4.zip -DestinationPath . -Force
Unblock-File .\install_developer_manual_bundle_mdo_v4.ps1
```

Syntax-check:

```powershell
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
  ".\install_developer_manual_bundle_mdo_v4.ps1",
  [ref]$tokens,
  [ref]$errors
) | Out-Null
$errors
```

Find bundle:

```powershell
$bundle = Get-ChildItem -Path D:\code\ccode,$env:USERPROFILE\Downloads `
  -Filter "dottalkpp_developer_manual_dropin_bundle_v0_1.zip" `
  -Recurse `
  -ErrorAction SilentlyContinue |
  Select-Object -First 1
$bundle.FullName
```

Dry run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\install_developer_manual_bundle_mdo_v4.ps1 `
  -Package $bundle.FullName `
  -RepoRoot D:\code\ccode `
  -WhatIfPlan
```

Install:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\install_developer_manual_bundle_mdo_v4.ps1 `
  -Package $bundle.FullName `
  -RepoRoot D:\code\ccode
```

Verify:

```powershell
Get-ChildItem .\docs\manuals\developer\dev
Get-ChildItem .\docs\manuals\developer\dev | Measure-Object
Get-Content .\docs\MDO_DEVELOPER_MANUAL_BUNDLE_INTAKE_REPORT.md
```
