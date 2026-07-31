param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowX64CandidateLmdbBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowX64CandidateLmdbBuild) {
    throw "Refusing Phase 16X staging without -AllowX64CandidateLmdbBuild"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\messaging\prepare_message_catalog_phase16x_x64_lmdb_build.py"
if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-x64-candidate-lmdb-build
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-x64-candidate-lmdb-build
}
exit $LASTEXITCODE
