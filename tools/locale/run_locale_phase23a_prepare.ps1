param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AcceptReportOnlyLocaleContract
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AcceptReportOnlyLocaleContract) {
    throw "Refusing Phase 23A locale contract without -AcceptReportOnlyLocaleContract"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\prepare_locale_phase23a_shared_locale_contract.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --accept-report-only-locale-contract
} else {
    & $PythonExe $script --repo-root $RepoRoot --accept-report-only-locale-contract
}
exit $LASTEXITCODE
