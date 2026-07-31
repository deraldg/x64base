param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingStaging
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $RepoRoot "tools\messaging\stage_message_catalog_phase22ae_6_5_10cl_b_option_b_wrapper_contract.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingStaging) { $argsList += "--replace-existing-staging" }

& $PythonExe @argsList
exit $LASTEXITCODE
