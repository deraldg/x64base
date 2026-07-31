param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowToolRepair
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowToolRepair) {
    throw "Refusing Phase 22AE.1 script repair without -AllowToolRepair"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\messaging\repair_message_catalog_phase22ae_1_execution_script_constants.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-tool-repair
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-tool-repair
}
exit $LASTEXITCODE
