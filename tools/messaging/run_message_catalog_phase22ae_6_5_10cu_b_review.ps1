param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview,
  [switch]$AllowMissingCtBSavepoint
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\review_message_catalog_phase22ae_6_5_10cu_b_native_candidate_table_materialization.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingReview) { $argsList += "--replace-existing-review" }
if ($AllowMissingCtBSavepoint) { $argsList += "--allow-missing-ct-b-savepoint" }
& $PythonExe @argsList
exit $LASTEXITCODE
