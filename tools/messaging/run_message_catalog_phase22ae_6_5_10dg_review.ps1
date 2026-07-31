param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview,
  [switch]$ReplaceExisting
)

$ErrorActionPreference = "Stop"

$argsList = @(
  ".\tools\messaging\review_message_catalog_phase22ae_6_5_10dg_reuse_decision_runtime_proof_plan.py",
  "--repo-root", $RepoRoot
)

if ($ReplaceExistingReview -or $ReplaceExisting) {
  $argsList += "--replace-existing-review"
}

& $PythonExe @argsList
exit $LASTEXITCODE
