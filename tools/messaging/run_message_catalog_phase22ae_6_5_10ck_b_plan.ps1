param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPlan
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $RepoRoot "tools\messaging\plan_message_catalog_phase22ae_6_5_10ck_b_option_b_wrapper_contract.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingPlan) { $argsList += "--replace-existing-plan" }

& $PythonExe @argsList
exit $LASTEXITCODE
