param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowActiveCatalogMutation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowActiveCatalogMutation) {
    throw "Refusing Phase 22AE.5 active catalog promotion without -AllowActiveCatalogMutation"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\messaging\execute_message_catalog_phase22ae_5_memo_aware_promotion.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --mode prepare --allow-active-catalog-mutation
} else {
    & $PythonExe $script --repo-root $RepoRoot --mode prepare --allow-active-catalog-mutation
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$controlPath = Join-Path $RepoRoot "docs\messaging\reports\message_catalog_phase22ae_5_control_v1.json"
$control = Get-Content $controlPath -Raw | ConvertFrom-Json

if ($control.should_execute_runtime -eq $true) {
    $runlogPath = [string]$control.runlog_path
    New-Item -ItemType Directory -Force (Split-Path -Parent $runlogPath) | Out-Null
    $dtsPath = [string]$control.script_path
    Write-Host "[MSG-22AE.5] Executing memo-aware DTS:" $dtsPath
    Write-Host "[MSG-22AE.5] Runlog:" $runlogPath
    $runtimeInput = "DO $dtsPath`r`nQUIT`r`n"
    $datarun = Join-Path $RepoRoot "datarun"
    $runtimeInput | & $datarun 2>&1 | Tee-Object -FilePath $runlogPath
} else {
    Write-Host "[MSG-22AE.5] Runtime execution skipped; already-present noop or prepare-only green."
}

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --mode finalize --runtime-log ([string]$control.runlog_path)
} else {
    & $PythonExe $script --repo-root $RepoRoot --mode finalize --runtime-log ([string]$control.runlog_path)
}
exit $LASTEXITCODE
