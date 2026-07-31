param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\review_message_catalog_phase22ae_6_5_10cm_b_option_b_wrapper_contract_proof.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingReview) { $argsList += "--replace-existing-review" }
& $PythonExe @argsList
exit $LASTEXITCODE
