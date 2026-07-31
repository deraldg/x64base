param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowInactiveCandidateDbfExecution
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowInactiveCandidateDbfExecution) {
    throw "Refusing Phase 11 DBF execution without -AllowInactiveCandidateDbfExecution"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) {
        $PythonExe = $env:PYTHON_EXE
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $PythonExe = "py"
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonExe = "python"
    } else {
        throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE."
    }
}

$script = Join-Path $RepoRoot "tools\messaging\execute_message_catalog_phase11_inactive_candidate_dbf.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-inactive-candidate-dbf-execution
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-inactive-candidate-dbf-execution
}
exit $LASTEXITCODE
