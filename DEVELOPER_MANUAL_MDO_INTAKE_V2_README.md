# Developer Manual Bundle MDO Intake v2

This package replaces v1. The v1 script had a PowerShell StrictMode bug when a single directory was returned by `Get-ChildItem`.

Use v2 only:

```text
install_developer_manual_bundle_mdo_v2.ps1
install_developer_manual_bundle_mdo_v2.cmd
```

## Use from D:\code\ccode

Extract:

```powershell
Expand-Archive .\dottalkpp_developer_manual_mdo_intake_v2.zip -DestinationPath . -Force
Unblock-File .\install_developer_manual_bundle_mdo_v2.ps1
```

Syntax-check:

```powershell
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
  ".\install_developer_manual_bundle_mdo_v2.ps1",
  [ref]$tokens,
  [ref]$errors
) | Out-Null
$errors
```

Find bundle if needed:

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
  -File .\install_developer_manual_bundle_mdo_v2.ps1 `
  -Package $bundle.FullName `
  -RepoRoot D:\code\ccode `
  -WhatIfPlan
```

Install:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\install_developer_manual_bundle_mdo_v2.ps1 `
  -Package $bundle.FullName `
  -RepoRoot D:\code\ccode
```

## Boundary

The installer is normalized into the existing MDO documentation estate and does not intentionally touch source, HELP, CMDHELPCHK, catalogs, runtime data, or existing SelfDoc metadata.
