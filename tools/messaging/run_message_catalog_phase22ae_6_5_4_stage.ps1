param([Parameter(Mandatory=$true)][string]$RepoRoot,[string]$PythonExe="",[switch]$ReplaceExistingSandbox)
Set-StrictMode -Version Latest; $ErrorActionPreference="Stop"
if (-not $PythonExe) { if ($env:PYTHON_EXE) { $PythonExe=$env:PYTHON_EXE } elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe="py" } else { $PythonExe="python" } }
$script=Join-Path $RepoRoot "tools\messaging\stage_message_catalog_phase22ae_6_5_4_full_state_zap_import.py"
$argsList=@("--repo-root",$RepoRoot); if ($ReplaceExistingSandbox) { $argsList += "--replace-existing-sandbox" }
if ($PythonExe -eq "py") { & py -3.12 $script @argsList } else { & $PythonExe $script @argsList }
exit $LASTEXITCODE
