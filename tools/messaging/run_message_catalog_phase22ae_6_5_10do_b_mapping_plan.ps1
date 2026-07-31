param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPlan
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\plan_message_catalog_phase22ae_6_5_10do_b_active_help_catalog_target_mapping.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingPlan) { $argsList += "--replace-existing-plan" }
& $PythonExe @argsList
exit $LASTEXITCODE
