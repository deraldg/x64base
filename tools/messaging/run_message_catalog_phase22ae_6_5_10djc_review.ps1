param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview,
  [switch]$ReplaceExistingPackage,
  [switch]$ReplaceExisting
)
$ErrorActionPreference = "Stop"
$argsList = @((Join-Path $RepoRoot "tools\messaging\package_message_catalog_phase22ae_6_5_10djc_clean_runtime_proof_transcript_review.py"), "--repo-root", $RepoRoot)
if ($ReplaceExistingReview -or $ReplaceExistingPackage -or $ReplaceExisting) { $argsList += "--replace-existing-package" }
& $PythonExe @argsList
exit $LASTEXITCODE
