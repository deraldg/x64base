$ErrorActionPreference = "Stop"

$env:DOTTALK_APPEND_TRACE = "0"
$env:DOTTALK_INDEX_TRACE  = "0"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ((Split-Path $scriptDir -Leaf).ToLowerInvariant() -eq "bin") {
    $appRoot = Split-Path -Parent $scriptDir
    $stageRoot = Split-Path -Parent $appRoot
} else {
    $stageRoot = $scriptDir
    $appRoot = Join-Path $stageRoot "dottalkpp"
}

$builtExe = Join-Path $stageRoot "build\src\Release\dottalkpp.exe"
$runtimeExe = Join-Path $appRoot "bin\dottalkpp.exe"
$runtimeData = Join-Path $appRoot "data"

if (-not (Test-Path -LiteralPath $builtExe)) {
    throw "Built executable not found: $builtExe"
}

if (-not (Test-Path -LiteralPath $runtimeExe)) {
    throw "Runtime executable path not found: $runtimeExe"
}

if (-not (Test-Path -LiteralPath $runtimeData)) {
    throw "Runtime data path not found: $runtimeData"
}

Copy-Item -LiteralPath $builtExe -Destination $runtimeExe -Force

Push-Location $runtimeData
try {
    & $runtimeExe
}
finally {
    Pop-Location
}
