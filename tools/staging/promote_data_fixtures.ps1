<#
.SYNOPSIS
    Promote clean MCC data fixtures from the development tree to staging.

.DESCRIPTION
    Authority chain (AI_PORTAL.md):

        D:\code\ccode  ->  C:\x64base  ->  github.com/deraldg/x64base
        development        clean staging     public snapshot

    Promotes:
        DBF tables      dottalkpp/data/dbf/{og,vfp,x32,x64}/*.DBF
        CDX containers  dottalkpp/data/indexes/**/*.cdx
        CNX containers  dottalkpp/data/indexes/**/*.cnx
        INX containers  dottalkpp/data/indexes/**/*.inx
        The canonical archive MyCommunityCollege.zip
        Schema notes

    Explicitly does NOT promote:
        *.cdx.d/          LMDB environments -- DERIVED from CDX, 53 GB measured
        dottalkpp/data/lmdb/                -- same
        *.bak* *.save *.before_mdo_*        -- development sidecars
        backup/ directories                 -- working state

    LMDB is regenerated on the far side by:
        dottalkpp/data/scripts/mcc/mcc_build_x64_lmdb.dts

    REPORT-ONLY by default. Copies nothing unless -Execute is passed.

.PARAMETER Execute
    Actually copy. Without this, the script only reports what would move.

.EXAMPLE
    .\tools\staging\promote_data_fixtures.ps1
    # dry run

.EXAMPLE
    .\tools\staging\promote_data_fixtures.ps1 -Execute
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

if ($dev -ieq $staging) { throw "Dev and staging resolve to the same path." }

Write-Host "Dev:     $dev"
Write-Host "Staging: $staging"
Write-Host "Mode:    $(if ($Execute) { 'EXECUTE' } else { 'REPORT-ONLY' })"
Write-Host ""

# --- What may be promoted ---------------------------------------------------
$include = @(
    @{ Rel = "dottalkpp\data\dbf";        Filter = @("*.DBF","*.dbf","*.txt","*.ini") }
    @{ Rel = "dottalkpp\data\indexes";    Filter = @("*.cdx","*.cnx","*.inx") }
    @{ Rel = "dottalkpp\data\schemas";    Filter = @("*.txt","*.dtschema") }
    @{ Rel = "dottalkpp\data\scripts\mcc";Filter = @("*.dts","*.md") }
)

# Single archive, promoted explicitly.
$singles = @("dottalkpp\data\dbf\MyCommunityCollege.zip")

# --- What must never be promoted, regardless of the above -------------------
# .cdx.d is the LMDB environment directory. Excluding it is the entire point.
$denyRegex = '(\.cdx\.d\\)|(\\lmdb\\)|(\\backup\\)|(\.bak)|(\.save)|(\.SAVE)|(\.before_mdo_)|(\.orig$)|(\.rej$)|(data\.mdb$)|(lock\.mdb$)'

$plan = @()

foreach ($grp in $include) {
    $srcRoot = Join-Path $dev $grp.Rel
    if (-not (Test-Path -LiteralPath $srcRoot)) {
        Write-Warning "Missing in dev, skipped: $($grp.Rel)"
        continue
    }
    foreach ($pat in $grp.Filter) {
        Get-ChildItem -LiteralPath $srcRoot -Recurse -File -Filter $pat -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch $denyRegex } |
            ForEach-Object {
                $plan += [pscustomobject]@{
                    Rel   = $_.FullName.Substring($dev.Length + 1)
                    Bytes = $_.Length
                }
            }
    }
}

foreach ($s in $singles) {
    $p = Join-Path $dev $s
    if (Test-Path -LiteralPath $p) {
        $plan += [pscustomobject]@{ Rel = $s; Bytes = (Get-Item -LiteralPath $p).Length }
    }
}

$plan = $plan | Sort-Object Rel -Unique

# --- Sanity gate: nothing LMDB-shaped may survive the filter ----------------
$leak = $plan | Where-Object { $_.Rel -match $denyRegex }
if ($leak) {
    $leak | ForEach-Object { Write-Error "DENY-LIST LEAK: $($_.Rel)" }
    throw "Refusing to promote: deny-list leak detected. This is the 53 GB LMDB guard. Fix the filter."
}

$totalMb = [math]::Round((($plan | Measure-Object Bytes -Sum).Sum) / 1MB, 1)

Write-Host "Promotion plan: $($plan.Count) files, $totalMb MB"
Write-Host ""
$plan |
    Group-Object { ($_.Rel -split '\\')[0..2] -join '\' } |
    Sort-Object Count -Descending |
    Format-Table @{L='Area';E={$_.Name}},
                 Count,
                 @{L='MB';E={[math]::Round((($_.Group | Measure-Object Bytes -Sum).Sum)/1MB,2)}} -AutoSize

# Report what we are deliberately leaving behind, so the omission is visible.
$lmdbDir = Join-Path $dev "dottalkpp\data\lmdb"
if (Test-Path -LiteralPath $lmdbDir) {
    Write-Host "EXCLUDED (derived, regenerable):"
    Write-Host "  dottalkpp\data\lmdb\   -- LMDB environments"
    Write-Host "  **\*.cdx.d\            -- LMDB environments"
    Write-Host "  Regenerate on the far side with scripts\mcc\mcc_build_x64_lmdb.dts"
    Write-Host ""
}

if (-not $Execute) {
    Write-Host "REPORT-ONLY. Nothing copied."
    Write-Host "Re-run with -Execute to promote."
    return
}

# --- Execute ----------------------------------------------------------------
$copied = 0
foreach ($item in $plan) {
    $src = Join-Path $dev     $item.Rel
    $dst = Join-Path $staging $item.Rel
    $dir = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $copied++
}

Write-Host "Promoted $copied files ($totalMb MB) to $staging"
Write-Host ""
Write-Host "REQUIRED NEXT STEP -- publication completeness."
Write-Host "src/CMakeLists.txt uses file(GLOB_RECURSE ...). A file present in the"
Write-Host "staging WORKING TREE but untracked will build locally and still be"
Write-Host "absent from GitHub. Working-copy equality is not publication proof."
Write-Host ""
Write-Host "  cd $staging"
Write-Host "  git status --short"
Write-Host "  git add -A dottalkpp/data"
Write-Host "  git status --short   # confirm no *.cdx.d or lmdb entries staged"
Write-Host ""
Write-Host "Verify no LMDB slipped in:"
Write-Host "  git diff --cached --name-only | Select-String 'cdx\.d|lmdb|\.mdb'"
Write-Host "  # expect: NO OUTPUT"
