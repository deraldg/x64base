param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [Parameter(Mandatory=$false)]
    [string]$RuntimeLog = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\messaging\execute_message_catalog_phase22ae_6_5_10u_text_only_roundtrip.py"
$argsList = @("--repo-root", $RepoRoot, "--mode", "finalize")
if ($RuntimeLog) { $argsList += @("--runtime-log", $RuntimeLog) }

if ($PythonExe -eq "py") { & py -3.12 $script @argsList } else { & $PythonExe $script @argsList }
exit $LASTEXITCODE
