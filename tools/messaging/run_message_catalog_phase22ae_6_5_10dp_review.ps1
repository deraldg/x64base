param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview
)
$Script = Join-Path $RepoRoot "tools\messaging\review_message_catalog_phase22ae_6_5_10dp_shutdown_crash_triage_decision.py"
$Args = @($Script, "--repo-root", $RepoRoot)
if ($ReplaceExistingReview) { $Args += "--replace-existing-review" }
& $PythonExe @Args
exit $LASTEXITCODE
