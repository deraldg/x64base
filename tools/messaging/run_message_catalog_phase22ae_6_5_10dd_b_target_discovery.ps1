param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingStaging,
  [int]$MaxFiles = 25000
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\stage_message_catalog_phase22ae_6_5_10dd_b_active_help_cmdhelpchk_target_discovery.py"
$argsList = @($script, "--repo-root", $RepoRoot, "--max-files", "$MaxFiles")
if ($ReplaceExistingStaging) { $argsList += "--replace-existing-staging" }
& $PythonExe @argsList
exit $LASTEXITCODE
