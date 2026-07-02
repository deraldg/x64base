param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptLeaf = (Split-Path $scriptDir -Leaf).ToLowerInvariant()

if ($scriptLeaf -eq "bin") {
    $appRoot = Split-Path -Parent $scriptDir
    $repoRoot = Split-Path -Parent $appRoot
} else {
    $repoRoot = $scriptDir
    $appRoot = Join-Path $repoRoot "dottalkpp"
}

$runtimeData = Join-Path $appRoot "data"
$tkLauncher = Join-Path $repoRoot "tools\gui_preview\dottalkpp_tk.py"

if (-not (Test-Path -LiteralPath $runtimeData)) {
    throw "Runtime data path not found: $runtimeData"
}

if (-not (Test-Path -LiteralPath $tkLauncher)) {
    throw "Tk launcher not found: $tkLauncher"
}

$env:DOTTALKPP_ROOT = $appRoot
$env:DOTTALKPP_DATA = $runtimeData
$env:DOTTALK_DATA = $runtimeData

Push-Location $runtimeData
try {
    python $tkLauncher @AppArgs
}
finally {
    Pop-Location
}
exit $LASTEXITCODE
