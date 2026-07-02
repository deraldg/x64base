param(
    [string]$StageDataRoot = "",
    [string]$DevDataRoot = "",
    [string[]]$Lane = @("dbf", "indexes", "lmdb"),
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ([string]::IsNullOrWhiteSpace($StageDataRoot)) {
    $StageDataRoot = Join-Path $repoRoot "dottalkpp\data"
}
if ([string]::IsNullOrWhiteSpace($DevDataRoot)) {
    $devRoot = if ($env:DOTTALKPP_DEV_ROOT) { $env:DOTTALKPP_DEV_ROOT } else { "D:\code\ccode" }
    $DevDataRoot = Join-Path $devRoot "dottalkpp\data"
}

if (-not (Test-Path -LiteralPath $StageDataRoot)) {
    throw "Stage data root not found: $StageDataRoot"
}

if (-not (Test-Path -LiteralPath $DevDataRoot)) {
    throw "Dev data root not found: $DevDataRoot"
}

$laneMap = @{
    "dbf" = @("dev", "memo", "x32", "x64")
    "indexes" = @("datadict", "help", "locale", "manuals", "memo", "messaging", "metadata", "vfp", "x32", "x64")
    "lmdb" = @("cmdhelp", "datadict", "help", "locale", "manuals", "memo", "messaging", "metadata", "x32", "x64")
}

function Invoke-RobocopyMirror {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Host "Skip missing source: $Source" -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path -LiteralPath $Destination)) {
        New-Item -ItemType Directory -Path $Destination | Out-Null
    }

    $args = @(
        $Source
        $Destination
        "/MIR"
        "/R:1"
        "/W:1"
        "/NFL"
        "/NDL"
        "/NP"
    )

    if ($WhatIf) {
        $args += "/L"
    }

    & robocopy @args
    $code = $LASTEXITCODE
    if ($code -ge 8) {
        throw "robocopy failed for $Source -> $Destination with exit code $code"
    }
}

Write-Host "Reverse-normalizing staged data back into dev"
Write-Host "  Stage : $StageDataRoot"
Write-Host "  Dev   : $DevDataRoot"
Write-Host "  Lanes : $($Lane -join ', ')"
Write-Host "  Mode  : $(if ($WhatIf) { 'WhatIf' } else { 'Apply' })"
Write-Host ""

foreach ($selectedLane in $Lane) {
    if ($laneMap.Keys -notcontains $selectedLane) {
        throw "Unknown lane: $selectedLane"
    }

    foreach ($subdir in $laneMap[$selectedLane]) {
        $src = Join-Path (Join-Path $StageDataRoot $selectedLane) $subdir
        $dst = Join-Path (Join-Path $DevDataRoot $selectedLane) $subdir
        Write-Host "Mirror $selectedLane\$subdir"
        Invoke-RobocopyMirror -Source $src -Destination $dst
    }

    Write-Host ""
}

Write-Host "Reverse normalization complete."
Write-Host "Next:"
Write-Host "  1. Inspect $DevDataRoot for data-lane changes"
Write-Host "  2. Rebuild or smoke-test targeted lanes as needed"
Write-Host "  3. Resume normal dev -> stage promotion"
