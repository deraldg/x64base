param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AcceptReportOnlyReconciliation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AcceptReportOnlyReconciliation) {
    throw "Refusing Phase 23Q message schema reconciliation without -AcceptReportOnlyReconciliation"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\reconcile_locale_phase23q_message_schema.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --accept-report-only-reconciliation
} else {
    & $PythonExe $script --repo-root $RepoRoot --accept-report-only-reconciliation
}
exit $LASTEXITCODE
