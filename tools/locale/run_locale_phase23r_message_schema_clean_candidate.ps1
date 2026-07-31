param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AcceptReportOnlyCleanCandidate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AcceptReportOnlyCleanCandidate) {
    throw "Refusing Phase 23R clean candidate without -AcceptReportOnlyCleanCandidate"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\repair_locale_phase23r_message_schema_clean_candidate.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --accept-report-only-clean-candidate
} else {
    & $PythonExe $script --repo-root $RepoRoot --accept-report-only-clean-candidate
}
exit $LASTEXITCODE
