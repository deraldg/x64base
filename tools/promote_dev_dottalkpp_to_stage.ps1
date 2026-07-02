param(
    [string]$DevRoot = "",
    [string]$StageRoot = "",
    [string[]]$DataLane = @(),
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ([string]::IsNullOrWhiteSpace($StageRoot)) {
    $StageRoot = $repoRoot
}
if ([string]::IsNullOrWhiteSpace($DevRoot)) {
    $DevRoot = if ($env:DOTTALKPP_DEV_ROOT) { $env:DOTTALKPP_DEV_ROOT } else { "D:\code\ccode" }
}

if (-not (Test-Path -LiteralPath $DevRoot)) {
    throw "Dev root not found: $DevRoot"
}

if (-not (Test-Path -LiteralPath $StageRoot)) {
    throw "Stage root not found: $StageRoot"
}

$mirrorDirs = @(
    "bindings",
    "cmake",
    "docs",
    "include",
    "src",
    "tests",
    "tools"
)

$rootFiles = @(
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "CMakeLists.txt",
    "CMakePresets.json",
    "MANIFEST.txt",
    "README.md",
    "README_NEW.md",
    "WORKFLOW_X64BASE.md",
    "X64BASE_DATA_STAGING_TRIAGE.md",
    "X64BASE_HYGIENE_INVENTORY.md",
    "datarun.ps1"
)

$dataMirrorDirs = @(
    "comments",
    "datadict",
    "dbf",
    "help",
    "import",
    "indexes",
    "locale",
    "manuals",
    "messaging",
    "meta",
    "metadata",
    "schemas",
    "scripts",
    "workspaces"
)

$dataRootFiles = @(
    "cmdhelp.dts",
    "ersatz_browser.dts",
    "metadata.dts",
    "run_tests.bat",
    "run_tests.ps1",
    "run-tests.bat",
    "sandbox.dts",
    "vfp.dts",
    "x32.dts",
    "x64.dts"
)

$excludeDirs = @(
    ".git",
    ".vs",
    "build",
    "build-linux",
    "vcpkg_installed",
    "biblebase",
    "cascade_precision_erp",
    "logs",
    "tmp",
    "backup",
    "out",
    "system",
    "projects",
    ".relations"
)

$excludeFiles = @(
    "*.VC.db",
    "*.vcxproj.user",
    "data.mdb",
    "lock.mdb"
)

function Invoke-RobocopyMirror {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
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
        "/XD"
    ) + $excludeDirs + @(
        "/XF"
    ) + $excludeFiles

    if ($WhatIf) {
        $args += "/L"
    }

    & robocopy @args
    $code = $LASTEXITCODE
    if ($code -ge 8) {
        throw "robocopy failed for $Source -> $Destination with exit code $code"
    }
}

Write-Host "Promoting dev repo to stage repo"
Write-Host "  Dev   : $DevRoot"
Write-Host "  Stage : $StageRoot"
Write-Host "  Data  : $(if ($DataLane.Count -gt 0) { $DataLane -join ', ' } else { 'none (code-first mode)' })"
Write-Host "  Mode  : $(if ($WhatIf) { 'WhatIf' } else { 'Apply' })"
Write-Host ""

foreach ($dir in $mirrorDirs) {
    Invoke-RobocopyMirror `
        -Source (Join-Path $DevRoot $dir) `
        -Destination (Join-Path $StageRoot $dir)
}

foreach ($name in $rootFiles) {
    $src = Join-Path $DevRoot $name
    $dst = Join-Path $StageRoot $name
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination $dst -Force -WhatIf:$WhatIf
    }
}

$devRuntime = Join-Path $DevRoot "dottalkpp"
$stageRuntime = Join-Path $StageRoot "dottalkpp"

foreach ($dir in @("bin", "docs", "help", "user")) {
    Invoke-RobocopyMirror `
        -Source (Join-Path $devRuntime $dir) `
        -Destination (Join-Path $stageRuntime $dir)
}

$devData = Join-Path $devRuntime "data"
$stageData = Join-Path $stageRuntime "data"

foreach ($dir in $dataMirrorDirs) {
    if ($DataLane.Count -eq 0) {
        continue
    }
    if ($DataLane -notcontains $dir) {
        continue
    }

    Invoke-RobocopyMirror `
        -Source (Join-Path $devData $dir) `
        -Destination (Join-Path $stageData $dir)
}

if ($DataLane.Count -gt 0) {
    foreach ($name in $dataRootFiles) {
        $src = Join-Path $devData $name
        $dst = Join-Path $stageData $name
        if (Test-Path -LiteralPath $src) {
            Copy-Item -LiteralPath $src -Destination $dst -Force -WhatIf:$WhatIf
        }
    }
}

Write-Host ""
Write-Host "Promotion complete."
Write-Host "Next:"
Write-Host "  1. Review git status in $StageRoot"
Write-Host "  2. Build/test there"
Write-Host "  3. Keep this stage root external to the dev repo"
