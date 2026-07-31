param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview
)
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\review_message_catalog_phase22ae_6_5_10dr_shutdown_isolation_proof.py"
$args = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingReview) { $args += "--replace-existing-review" }
& $PythonExe @args
exit $LASTEXITCODE
