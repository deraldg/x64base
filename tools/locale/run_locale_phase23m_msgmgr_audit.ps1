param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AcceptReportOnlyAudit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AcceptReportOnlyAudit) {
    throw "Refusing Phase 23M MSGMGR audit without -AcceptReportOnlyAudit"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\audit_locale_phase23m_msgmgr_hand_edit.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --accept-report-only-audit
} else {
    & $PythonExe $script --repo-root $RepoRoot --accept-report-only-audit
}
exit $LASTEXITCODE
