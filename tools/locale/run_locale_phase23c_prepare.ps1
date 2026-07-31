param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowCandidateRuntimeExecution
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowCandidateRuntimeExecution) {
    throw "Refusing Phase 23C candidate runtime execution prep without -AllowCandidateRuntimeExecution"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\prepare_locale_phase23c_candidate_runtime_execution.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-candidate-runtime-execution
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-candidate-runtime-execution
}
exit $LASTEXITCODE
