param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPlan
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\plan_message_catalog_phase22ae_6_5_10dr_b_source_locale_help_only_dry_run_eligibility.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingPlan) { $argsList += "--replace-existing-plan" }
& $PythonExe @argsList
exit $LASTEXITCODE
