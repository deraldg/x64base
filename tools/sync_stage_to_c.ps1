param(
    [string]$Source = "D:\code\ccode\x64base",
    [string]$Destination = "C:\x64base",
    [switch]$WhatIf
)

# Checkpoint mirror only.
# Use this after several staging iterations, before a path-sensitive smoke test,
# or before final promotion. Do not run it as the normal inner-loop workflow.

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Source)) {
    throw "Source path not found: $Source"
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
