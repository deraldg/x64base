param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AcceptCandidateSchemaStaging
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AcceptCandidateSchemaStaging) {
    throw "Refusing Phase 23B candidate schema staging without -AcceptCandidateSchemaStaging"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\prepare_locale_phase23b_candidate_schema_staging.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --accept-candidate-schema-staging
} else {
    & $PythonExe $script --repo-root $RepoRoot --accept-candidate-schema-staging
}
exit $LASTEXITCODE
