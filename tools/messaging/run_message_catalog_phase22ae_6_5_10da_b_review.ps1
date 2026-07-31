param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview,
  [switch]$AllowMissingCzBSavepoint
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\review_message_catalog_phase22ae_6_5_10da_b_help_cmdhelpchk_candidate_table_native_materialization.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingReview) { $argsList += "--replace-existing-review" }
if ($AllowMissingCzBSavepoint) { $argsList += "--allow-missing-cz-b-savepoint" }
& $PythonExe @argsList
exit $LASTEXITCODE
