param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowX64CandidateRebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowX64CandidateRebuild) {
    throw "Refusing Phase 15X staging without -AllowX64CandidateRebuild"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\messaging\prepare_message_catalog_phase15x_x64_candidate_rebuild.py"
if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-x64-candidate-rebuild
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-x64-candidate-rebuild
}
exit $LASTEXITCODE
