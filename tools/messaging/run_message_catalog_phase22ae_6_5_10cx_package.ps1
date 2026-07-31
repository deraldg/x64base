param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$ReplaceExistingPackage
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\messaging\stage_message_catalog_phase22ae_6_5_10cx_native_writer_probes.py"
$argsList = @("--repo-root", $RepoRoot)
if ($ReplaceExistingPackage) { $argsList += "--replace-existing-package" }

if ($PythonExe -eq "py") { & py -3.12 $script @argsList } else { & $PythonExe $script @argsList }
exit $LASTEXITCODE
