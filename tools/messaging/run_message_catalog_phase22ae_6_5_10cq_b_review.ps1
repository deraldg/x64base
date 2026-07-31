param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $RepoRoot "tools\messaging\review_message_catalog_phase22ae_6_5_10cq_b_targeted_native_writer_invocation.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingReview) { $argsList += "--replace-existing-review" }

& $PythonExe @argsList
exit $LASTEXITCODE
