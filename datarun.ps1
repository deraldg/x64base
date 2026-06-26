param(
    [string[]]$CommandLines,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$env:DOTTALK_APPEND_TRACE = "0"
$env:DOTTALK_INDEX_TRACE  = "0"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptLeaf = (Split-Path $scriptDir -Leaf).ToLowerInvariant()

if ($scriptLeaf -eq "bin") {
    $appRoot = Split-Path -Parent $scriptDir
    $repoRoot = Split-Path -Parent $appRoot
} else {
    $repoRoot = $scriptDir
    $appRoot = Join-Path $repoRoot "dottalkpp"
}

$builtExe = Join-Path $repoRoot "build\src\Release\dottalkpp.exe"
$runtimeExe = Join-Path $appRoot "bin\dottalkpp.exe"
$runtimeData = Join-Path $appRoot "data"

if (-not (Test-Path -LiteralPath $appRoot)) {
    throw "Application root not found: $appRoot"
}

if (-not (Test-Path -LiteralPath $builtExe)) {
    throw "Built executable not found: $builtExe"
}

if (-not (Test-Path -LiteralPath $runtimeExe)) {
    throw "Runtime executable path not found: $runtimeExe"
}

if (-not (Test-Path -LiteralPath $runtimeData)) {
    throw "Runtime data path not found: $runtimeData"
}

    try {
        Copy-Item -LiteralPath $builtExe -Destination $runtimeExe -Force
    }
    catch {
        Write-Warning "Runtime executable is locked; running existing copy at $runtimeExe"
    }

Push-Location $runtimeData
try {
    if ($CommandLines -and $CommandLines.Count -gt 0) {
        $commandStream = @($CommandLines)
        if ($commandStream[-1] -ne "") {
            $commandStream += ""
        }
        $commandStream | & $runtimeExe @AppArgs
    } else {
        & $runtimeExe @AppArgs
    }
}
finally {
    Pop-Location
}
