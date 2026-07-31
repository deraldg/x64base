param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowInactiveCandidateCdxExecution
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowInactiveCandidateCdxExecution) {
    throw "Refusing Phase 14.1 staging without -AllowInactiveCandidateCdxExecution"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\messaging\prepare_message_catalog_phase14_1_cdx_execution.py"
if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-inactive-candidate-cdx-execution
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-inactive-candidate-cdx-execution
}
exit $LASTEXITCODE
