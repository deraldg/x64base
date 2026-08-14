# Developer Manual Bundle MDO Intake v3

This package replaces v1 and v2.

Why:
- v1 failed under PowerShell StrictMode when a single directory did not expose `.Count`.
- v2 created destination folders but could fail to copy child files because of wildcard copy behavior.
- v3 enumerates source children explicitly, copies each child with `-LiteralPath`, and verifies destination file counts.

Use v3 only:

```text
install_developer_manual_bundle_mdo_v3.ps1
install_developer_manual_bundle_mdo_v3.cmd
```

## Use from D:\code\ccode

Extract:

```powershell
Expand-Archive .\dottalkpp_developer_manual_mdo_intake_v3.zip -DestinationPath . -Force
Unblock-File .\install_developer_manual_bundle_mdo_v3.ps1
```

Syntax-check:

```powershell
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
  ".\install_developer_manual_bundle_mdo_v3.ps1",
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
  -File .\install_developer_manual_bundle_mdo_v3.ps1 `
  -Package $bundle.FullName `
  -RepoRoot D:\code\ccode `
  -WhatIfPlan
```

Install:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\install_developer_manual_bundle_mdo_v3.ps1 `
  -Package $bundle.FullName `
  -RepoRoot D:\code\ccode
```

Verify:

```powershell
Get-ChildItem .\docs\manuals\developer\dev
Get-Content .\docs\MDO_DEVELOPER_MANUAL_BUNDLE_INTAKE_REPORT.md
```

The dev folder should show DEV-00 through DEV-19 files.
