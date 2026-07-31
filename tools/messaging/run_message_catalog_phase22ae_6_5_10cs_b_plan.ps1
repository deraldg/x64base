param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPlan
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $RepoRoot "tools\messaging\plan_message_catalog_phase22ae_6_5_10cs_b_active_candidate_native_writer_invocation.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingPlan) { $argsList += "--replace-existing-plan" }

& $PythonExe @argsList
exit $LASTEXITCODE
