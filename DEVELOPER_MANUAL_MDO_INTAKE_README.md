# Developer Manual Bundle MDO Intake v1

This package installs `dottalkpp_developer_manual_dropin_bundle_v0_1.zip` into the existing MDO documentation estate without creating a second `docs/developer_manual/` home.

## Use from D:\code\ccode

```powershell
Expand-Archive .\dottalkpp_developer_manual_mdo_intake_v1.zip -DestinationPath . -Force
Unblock-File .\install_developer_manual_bundle_mdo_v1.ps1
```

Syntax-check first:

```powershell
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
  ".\install_developer_manual_bundle_mdo_v1.ps1",
  [ref]$tokens,
  [ref]$errors
) | Out-Null
$errors
```

Dry run:

```powershell
.\install_developer_manual_bundle_mdo_v1.ps1 `
  -Package .\dottalkpp_developer_manual_dropin_bundle_v0_1.zip `
  -RepoRoot D:\code\ccode `
  -WhatIfPlan
```

Install:

```powershell
.\install_developer_manual_bundle_mdo_v1.ps1 `
  -Package .\dottalkpp_developer_manual_dropin_bundle_v0_1.zip `
  -RepoRoot D:\code\ccode
```

## Normalized destination map

```text
docs/developer_manual/DEVELOPER_MANUAL_DRAFT_COMBINED.md
  -> docs/manuals/developer/DEVELOPER_MANUAL_DRAFT_COMBINED.md

docs/developer_manual/dev/*
  -> docs/manuals/developer/dev/*

docs/developer_manual/manualgen/*
  -> docs/manuals/developer/manualgen/*

docs/developer_manual/evidence/*
  -> docs/evidence/developer_manual/*

docs/developer_manual/diagrams/*
  -> docs/diagrams/developer_manual/*

docs/developer_manual/status/*
  -> docs/review/developer_manual/status/*

README.md, INSTALL.md, MANIFEST.md, bundle.json
  -> docs/archive/package_summaries/developer_manual_bundle_v0_1/
```

## Boundary

The installer does not intentionally touch:

```text
src/
include/
bindings/
HELP
CMDHELPCHK
catalogs
runtime data
existing SelfDoc metadata
```

The bundle is accepted as GREEN_TENTATIVE Developer Manual draft material, not as a finished manual or generated command reference.
