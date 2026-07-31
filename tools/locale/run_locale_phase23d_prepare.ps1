param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowCandidateCdxExecution
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowCandidateCdxExecution) {
    throw "Refusing Phase 23D candidate CDX execution prep without -AllowCandidateCdxExecution"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\prepare_locale_phase23d_candidate_cdx_execution.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-candidate-cdx-execution
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-candidate-cdx-execution
}
exit $LASTEXITCODE
