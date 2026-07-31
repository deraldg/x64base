param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AcceptReportOnlyRuntimeConsumerPlan
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AcceptReportOnlyRuntimeConsumerPlan) {
    throw "Refusing Phase 23H runtime consumer plan without -AcceptReportOnlyRuntimeConsumerPlan"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\prepare_locale_phase23h_runtime_consumer_plan.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --accept-report-only-runtime-consumer-plan
} else {
    & $PythonExe $script --repo-root $RepoRoot --accept-report-only-runtime-consumer-plan
}
exit $LASTEXITCODE
