param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowCandidateLmdbExecution
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowCandidateLmdbExecution) {
    throw "Refusing Phase 23E candidate LMDB execution prep without -AllowCandidateLmdbExecution"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\prepare_locale_phase23e_candidate_lmdb_execution.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-candidate-lmdb-execution
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-candidate-lmdb-execution
}
exit $LASTEXITCODE
