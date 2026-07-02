param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$env:DOTTALK_APPEND_TRACE = "0"
$env:DOTTALK_INDEX_TRACE = "0"

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
$wxExe = Join-Path $repoRoot "build-wx-fixed-local\src\gui\wx\Release\dottalkpp_wx.exe"

$cliCandidates = @(
    (Join-Path $repoRoot "build-wx-fixed-local\src\Release\dottalkpp.exe"),
    (Join-Path $repoRoot "build\src\Release\dottalkpp.exe"),
    (Join-Path $appRoot "bin\dottalkpp.exe")
)

if (-not (Test-Path -LiteralPath $appRoot)) {
    throw "Application root not found: $appRoot"
}

if (-not (Test-Path -LiteralPath $runtimeData)) {
    throw "Runtime data path not found: $runtimeData"
}

if (-not (Test-Path -LiteralPath $wxExe)) {
    throw "wx executable not found: $wxExe"
}

$cliExe = $cliCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $cliExe) {
    throw "DotTalk++ CLI executable not found. Checked: $($cliCandidates -join ', ')"
}

$env:DOTTALKPP_GUI_CLI = $cliExe
$env:DOTTALKPP_EXE = $cliExe
$env:DOTTALKPP_ROOT = $appRoot
$env:DOTTALKPP_DATA = $runtimeData
$env:DOTTALK_DATA = $runtimeData

$wxDir = Split-Path -Parent $wxExe
$runtimePathParts = @($wxDir)
if ($env:VCPKG_ROOT) {
    $runtimePathParts += (Join-Path $env:VCPKG_ROOT "installed\x64-windows\bin")
}
$runtimePathParts += @(
    "C:\Users\deral\vcpkg\installed\x64-windows\bin",
    (Join-Path $repoRoot "vcpkg_installed\x64-windows\bin")
)
$runtimePathParts = $runtimePathParts | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
$env:PATH = "$($runtimePathParts -join ';');$env:PATH"

Push-Location $runtimeData
try {
    & $wxExe @AppArgs
}
finally {
    Pop-Location
}
exit $LASTEXITCODE
