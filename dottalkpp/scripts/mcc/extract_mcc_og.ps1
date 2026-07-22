<#
.SYNOPSIS
    Extract the original My Community College DBF set from the canonical archive.

.DESCRIPTION
    MyCommunityCollege.zip is the reproducible origin of the MCC fixture set:
    12 tables, dBase III (0x03), no memo fields, FoxPro 2.6a compatible.

    This unpacks it to dottalkpp/data/dbf/og/ -- a staging area holding the
    untouched originals. The flavor conversions (VFP, x64) read from there via
    DotScript and never modify it.

    Non-destructive by default: refuses to overwrite an existing og/ set unless
    -Force is passed. The originals are the one thing in this pipeline that
    cannot be regenerated.

.PARAMETER Root
    Repo root. Defaults to the root inferred from this script's own location,
    so it runs against whatever clone it lives in.

.PARAMETER Force
    Replace an existing og/ directory.

.EXAMPLE
    .\dottalkpp\scripts\mcc\extract_mcc_og.ps1
#>

[CmdletBinding()]
param(
    [string] $Root,
    [switch] $Force
)

$ErrorActionPreference = "Stop"

if (-not $Root) {
    # Derive the repo root from this script's own location -- never hardcode a
    # dev path. <repo>\dottalkpp\scripts\mcc\extract_mcc_og.ps1
    $Root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
}

$resolved = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
$zip      = Join-Path $resolved "dottalkpp\data\dbf\MyCommunityCollege.zip"
$ogDir    = Join-Path $resolved "dottalkpp\data\dbf\og"

# Canonical archive hash, recorded 2026-07-14. Guards against a silently
# swapped or corrupted origin -- everything downstream derives from this file.
$expectedMd5 = "07EFFA84B4582B7D45DBCAB5E28AE94E"

if (-not (Test-Path -LiteralPath $zip)) {
    throw "Canonical archive not found: $zip"
}

$actualMd5 = (Get-FileHash -LiteralPath $zip -Algorithm MD5).Hash
Write-Host "Archive: $zip"
Write-Host "MD5:     $actualMd5"

if ($actualMd5 -ne $expectedMd5) {
    Write-Warning "MD5 MISMATCH."
    Write-Warning "  expected: $expectedMd5"
    Write-Warning "  actual:   $actualMd5"
    Write-Warning "The canonical MCC archive has changed since 2026-07-14."
    Write-Warning "Every fixture downstream derives from this file. Stop and confirm"
    Write-Warning "this is intended before regenerating fixtures from it."
    throw "Refusing to extract an unexpected archive. Pass -Force only after confirming the change is deliberate."
}
Write-Host "MD5 OK (matches canonical)."
Write-Host ""

if (Test-Path -LiteralPath $ogDir) {
    if (-not $Force) {
        Write-Host "og/ already exists: $ogDir"
        Write-Host "Contents:"
        Get-ChildItem -LiteralPath $ogDir -File |
            Select-Object Name, Length |
            Format-Table -AutoSize
        Write-Host "Nothing to do. Pass -Force to re-extract."
        return
    }
    Write-Host "Removing existing og/ (-Force)..."
    Remove-Item -LiteralPath $ogDir -Recurse -Force
}

$tmp = Join-Path $env:TEMP ("mcc_og_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

try {
    Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force

    # The archive nests everything under MyCommunityCollege/. Flatten it so the
    # DBF path slot can point straight at og/ without an extra level.
    $inner = Join-Path $tmp "MyCommunityCollege"
    $src   = if (Test-Path -LiteralPath $inner) { $inner } else { $tmp }

    New-Item -ItemType Directory -Force -Path $ogDir | Out-Null
    Get-ChildItem -LiteralPath $src -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $ogDir -Force
    }
} finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

$dbfs = @(Get-ChildItem -LiteralPath $ogDir -Filter *.DBF -File)

Write-Host "Extracted to: $ogDir"
Write-Host "DBF tables:   $($dbfs.Count)  (expected 12)"
Write-Host ""
$dbfs | Select-Object Name, Length | Format-Table -AutoSize

if ($dbfs.Count -ne 12) {
    Write-Warning "Expected 12 DBF tables, found $($dbfs.Count). Inspect before converting."
}

Write-Host "Next -- inside dottalkpp.exe. Flavor scripts are independent of each"
Write-Host "other; mcc_build_x64_lmdb MUST follow mcc_build_x64."
Write-Host ""
Write-Host "  DOTSCRIPT TRACE scripts\mcc\mcc_build_x32.dts      OUT tmp\mcc_x32.log"
Write-Host "  DOTSCRIPT TRACE scripts\mcc\mcc_build_vfp.dts      OUT tmp\mcc_vfp.log"
Write-Host "  DOTSCRIPT TRACE scripts\mcc\mcc_build_x64.dts      OUT tmp\mcc_x64.log"
Write-Host "  DOTSCRIPT TRACE scripts\mcc\mcc_build_x64_lmdb.dts OUT tmp\mcc_lmdb.log"
Write-Host ""
Write-Host "Review the full transcript. A zero exit code is NOT proof -- the"
Write-Host "DotScript runner reports unknown commands and continues to later lines."
Write-Host ""
Write-Host "These scripts are CANDIDATE / REVIEW_BEFORE_EXECUTION. They have never"
Write-Host "been run. Expect something to be wrong; that is what the trace is for."
