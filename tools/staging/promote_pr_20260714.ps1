<#
.SYNOPSIS
    Promote the 2026-07-14 change set from D:\code\ccode to C:\x64base.

.DESCRIPTION
    Authority chain (AI_PORTAL.md):

        D:\code\ccode  ->  C:\x64base  ->  github.com/deraldg/x64base
        development        clean staging     public snapshot

    This is an EXPLICIT MANIFEST, not a glob. Every file that crosses into
    staging is named below. Nothing rides along.

    THE CHANGE SET
      1. Reproducible MCC sample data     the databuild lane + rebuilt fixtures
      2. Repo hygiene                     sidecar + LMDB exclusion
      3. AI portal authority corrections  C:\x64base purpose, AIF-006 gate
      4. Contract drift repair            index-expression, 13 files

    HARD EXCLUSIONS -- enforced by a deny-list that THROWS rather than filter:
      *.cdx.d/          LMDB environments. 53 GB measured. DERIVED from CDX.
      data\lmdb\        same.
      data\dbf\og\      DERIVED -- extract_mcc_og.ps1 rebuilds it from the zip.
      *.bak* *.save     development sidecars.
      backups\          BUILDLMDB archives.

    REPORT-ONLY by default.

.EXAMPLE
    .\tools\staging\promote_pr_20260714.ps1
    .\tools\staging\promote_pr_20260714.ps1 -Execute
#>

[CmdletBinding()]
param(
    [string] $Dev     = "D:\code\ccode",
    [string] $Staging = "C:\x64base",
    [switch] $Execute
)

$ErrorActionPreference = "Stop"

$dev     = (Resolve-Path -LiteralPath $Dev).Path.TrimEnd('\')
$staging = (Resolve-Path -LiteralPath $Staging).Path.TrimEnd('\')
if ($dev -ieq $staging) { throw "Dev and staging are the same path." }

Write-Host "Dev:     $dev"
Write-Host "Staging: $staging"
Write-Host "Mode:    $(if ($Execute) { 'EXECUTE' } else { 'REPORT-ONLY' })"
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Named files. Explicit. Reviewable.
# ---------------------------------------------------------------------------
$files = @(
    # --- repo hygiene ------------------------------------------------------
    '.gitignore'

    # --- AI portal authority + AIF-006 closeout gate -----------------------
    'AI_PORTAL.md'
    'AI_README.md'
    'docs\agents\CURRENT_TARGET.md'
    'docs\ai-friendly\AI_ASSIMILATION_BOOK_V1.md'
    'docs\ai-friendly\AI_INTERACTION_INTAKE_QUEUE_V1.md'

    # --- contract drift: index keys are fields, not expressions -------------
    'docs\contracts\CONTRACT_REGISTRY_V1.md'
    'docs\contracts\reports\CONTRACT_DRIFT_INDEX_EXPRESSION_2026-07-14.md'
    'dottalkpp\data\dbf\mcc_schema.txt'
    'dottalkpp\data\dbf\community_college_schema.txt'
    'dottalkpp\data\dbf\community_college_x64_schema.txt'
    'dottalkpp\data\dbf\x64\community_college_x64_schema.txt'
    'dottalkpp\data\dbf\x64\Original Vector Name Sizes\community_college_x64_schema.txt'
    'dottalkpp\data\dbf\x32\README.txt'
    'dottalkpp\data\help\DATA_INDEX_README.txt'
    'dottalkpp\data\help\V32_help\DATA_INDEX_README.txt'
    'src\data\DATA_INDEX_README.txt'
    'mcc\community_college_schema.txt'
    'mcc\README.txt'
    'dottalkpp\docs\My_Comminty_College_README.txt'
    'dottalkpp\docs\My_Comminty_College_Data_Schema_README.txt'

    # --- the databuild lane -------------------------------------------------
    'dottalkpp\scripts\mcc\build_mcc_demo_bases.ps1'
    'dottalkpp\scripts\mcc\reset_mcc_fixtures.ps1'
    'dottalkpp\scripts\mcc\extract_mcc_og.ps1'
    'dottalkpp\data\scripts\mcc\README.md'
    'dottalkpp\data\scripts\mcc\mcc_build_x32.dts'
    'dottalkpp\data\scripts\mcc\mcc_build_vfp.dts'
    'dottalkpp\data\scripts\mcc\mcc_build_x64.dts'
    'dottalkpp\data\scripts\mcc\mcc_build_x64_lmdb.dts'
    'dottalkpp\data\scripts\mcc\mcc_demo.dts'

    # --- tools --------------------------------------------------------------
    'tools\hygiene\purge_dev_sidecars.ps1'
    'tools\staging\promote_data_fixtures.ps1'
    'tools\staging\promote_pr_20260714.ps1'

    # --- the canonical origin ----------------------------------------------
    'dottalkpp\data\dbf\MyCommunityCollege.zip'
)

# ---------------------------------------------------------------------------
# 2. Rebuilt fixtures. Globbed, but tightly.
# ---------------------------------------------------------------------------
$globs = @(
    @{ Dir='dottalkpp\data\dbf\x32';      Pat='*.dbf'  }
    @{ Dir='dottalkpp\data\dbf\x32';      Pat='*.DBF'  }
    @{ Dir='dottalkpp\data\dbf\vfp';      Pat='*.dbf'  }
    @{ Dir='dottalkpp\data\dbf\vfp';      Pat='*.DBF'  }
    @{ Dir='dottalkpp\data\dbf\x64';      Pat='*.dbf'  }
    @{ Dir='dottalkpp\data\dbf\x64';      Pat='*.DBF'  }
    @{ Dir='dottalkpp\data\indexes\x32';  Pat='*.cnx'  }
    @{ Dir='dottalkpp\data\indexes\vfp';  Pat='*.cnx'  }
    @{ Dir='dottalkpp\data\indexes\x64';  Pat='*.cdx'  }
    @{ Dir='dottalkpp\data\workspaces';   Pat='mcc_*.dtschema' }
)

# ---------------------------------------------------------------------------
# 3. The deny-list. This is the 53 GB guard. It THROWS.
# ---------------------------------------------------------------------------
$deny = '(\.cdx\.d\\)|(\\lmdb\\)|(\\backups?\\)|(\\og\\)|(\.bak)|(\.save)|(\.before_mdo_)|(data\.mdb$)|(lock\.mdb$)'

# ---------------------------------------------------------------------------
# Build the plan
# ---------------------------------------------------------------------------
$plan    = New-Object System.Collections.ArrayList
$missing = New-Object System.Collections.ArrayList

foreach ($rel in $files) {
    $p = Join-Path $dev $rel
    if (Test-Path -LiteralPath $p) {
        [void]$plan.Add([pscustomobject]@{
            Rel = $rel; Bytes = (Get-Item -LiteralPath $p).Length; Kind = 'named' })
    } else {
        [void]$missing.Add($rel)
    }
}

foreach ($g in $globs) {
    $d = Join-Path $dev $g.Dir
    if (-not (Test-Path -LiteralPath $d)) {
        [void]$missing.Add("$($g.Dir)\  (directory absent)")
        continue
    }
    Get-ChildItem -LiteralPath $d -File -Filter $g.Pat -EA SilentlyContinue | ForEach-Object {
        [void]$plan.Add([pscustomobject]@{
            Rel = $_.FullName.Substring($dev.Length + 1); Bytes = $_.Length; Kind = 'fixture' })
    }
}

$plan = @($plan | Sort-Object Rel -Unique)

# ---------------------------------------------------------------------------
# THE GUARD. Nothing LMDB-shaped survives this.
# ---------------------------------------------------------------------------
$leak = @($plan | Where-Object { $_.Rel -match $deny })
if ($leak.Count) {
    $leak | ForEach-Object { Write-Error "DENY-LIST LEAK: $($_.Rel)" }
    throw "REFUSING TO PROMOTE. The deny-list caught $($leak.Count) file(s). This guard exists because data\lmdb measured 53 GB on 2026-07-14. Fix the manifest."
}

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
$mb = [math]::Round((($plan | Measure-Object Bytes -Sum).Sum) / 1MB, 2)

Write-Host "PROMOTION PLAN: $($plan.Count) files, $mb MB" -ForegroundColor Cyan
Write-Host ""

$plan | Group-Object { ($_.Rel -split '\\')[0] } | Sort-Object Count -Desc |
    Format-Table @{L='Top-level';E={$_.Name}},
                 @{L='Files';E={$_.Count}},
                 @{L='MB';E={[math]::Round((($_.Group|Measure-Object Bytes -Sum).Sum)/1MB,2)}} -AutoSize |
    Out-String | Write-Host

if ($missing.Count) {
    Write-Warning "NOT FOUND IN DEV -- these were in the manifest but do not exist:"
    $missing | ForEach-Object { Write-Warning "    $_" }
    Write-Host ""
}

Write-Host "EXCLUDED BY DESIGN:" -ForegroundColor Green
Write-Host "  data\lmdb\            LMDB environments. Derived from CDX. 53 GB."
Write-Host "  **\*.cdx.d\           same."
Write-Host "  data\dbf\og\          derived -- extract_mcc_og.ps1 rebuilds it from the zip."
Write-Host "  *.bak* *.save         development sidecars."
Write-Host ""
Write-Host "  A fresh clone regenerates all of it:"
Write-Host "      .\dottalkpp\scripts\mcc\build_mcc_demo_bases.ps1"
Write-Host ""

if (-not $Execute) {
    Write-Host "REPORT-ONLY. Nothing copied. Re-run with -Execute." -ForegroundColor Yellow
    return
}

# ---------------------------------------------------------------------------
# Execute
# ---------------------------------------------------------------------------
$copied = 0
foreach ($item in $plan) {
    $src = Join-Path $dev     $item.Rel
    $dst = Join-Path $staging $item.Rel
    $dir = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $copied++
}

Write-Host "Promoted $copied files ($mb MB) to $staging" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT -- in C:\x64base. Read before you run." -ForegroundColor Cyan
Write-Host ""
Write-Host "  git status --short"
Write-Host ""
Write-Host "  # THE PUBLICATION CHECK. src\CMakeLists.txt uses file(GLOB_RECURSE),"
Write-Host "  # so a file present in the working tree but UNTRACKED will build"
Write-Host "  # locally and still be absent from GitHub. A green build is not"
Write-Host "  # publication proof."
Write-Host "  git add -A"
Write-Host "  git diff --cached --name-only | Select-String 'cdx\.d|lmdb|\.mdb|\\og\\'"
Write-Host "  #   ^ MUST PRINT NOTHING. If it prints anything, unstage and stop."
Write-Host ""
Write-Host "  git switch -c mcc-databuild-and-hygiene"
Write-Host "  git commit -m 'Reproducible MCC sample data, repo hygiene, AI portal corrections'"
Write-Host "  git push -u origin mcc-databuild-and-hygiene"
Write-Host ""
