param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\repair_message_catalog_phase22ae_6_5_10dj_b_docs_variable.py"
& $PythonExe $script --repo-root $RepoRoot
exit $LASTEXITCODE
