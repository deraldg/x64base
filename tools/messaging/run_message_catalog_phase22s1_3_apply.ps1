param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,
    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",
    [switch]$AllowSourceMutation
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (-not $AllowSourceMutation) { throw "Refusing Phase 22S1.3 source patch without -AllowSourceMutation" }
if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}
$script = Join-Path $RepoRoot "tools\messaging\apply_message_catalog_phase22s1_3_live_source_repair.py"
if ($PythonExe -eq "py") { & py -3.12 $script --repo-root $RepoRoot --allow-source-mutation }
else { & $PythonExe $script --repo-root $RepoRoot --allow-source-mutation }
exit $LASTEXITCODE
