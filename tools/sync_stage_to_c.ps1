param(
    [string]$Source = "",
    [string]$Destination = "",
    [switch]$WhatIf
)

# Legacy checkpoint mirror helper.
# With x64base staged directly at C:\x64base, this script is normally a no-op.
# Pass -Destination explicitly only when creating a separate checkpoint mirror.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ([string]::IsNullOrWhiteSpace($Source)) {
    $Source = $repoRoot
}
if ([string]::IsNullOrWhiteSpace($Destination)) {
    $Destination = if ($env:X64BASE_MIRROR_ROOT) { $env:X64BASE_MIRROR_ROOT } else { "C:\x64base" }
}

if (-not (Test-Path -LiteralPath $Source)) {
    throw "Source path not found: $Source"
}

$sourceFull = [System.IO.Path]::GetFullPath($Source).TrimEnd('\')
$destinationFull = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
if ([string]::Equals($sourceFull, $destinationFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Source and destination are the same path: $sourceFull"
}

if (-not (Test-Path -LiteralPath $Destination)) {
    New-Item -ItemType Directory -Path $Destination | Out-Null
}

$robocopyArgs = @(
    $Source
    $Destination
    "/MIR"
    "/R:1"
    "/W:1"
    "/NFL"
    "/NDL"
    "/NP"
    "/XD"
    ".git"
    ".vs"
    "build"
    "vcpkg_installed"
    "/XF"
    "*.VC.db"
    "*.vcxproj.user"
)

if ($WhatIf) {
    $robocopyArgs += "/L"
}

Write-Host "Syncing stage repo"
Write-Host "  Source      : $Source"
Write-Host "  Destination : $Destination"
Write-Host "  Mode        : " -NoNewline
if ($WhatIf) {
    Write-Host "WhatIf"
} else {
    Write-Host "Mirror"
}

& robocopy @robocopyArgs
$code = $LASTEXITCODE

if ($code -ge 8) {
    throw "robocopy failed with exit code $code"
}

Write-Host "robocopy exit code: $code"
Write-Host "Sync complete."
