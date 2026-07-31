param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReview,
  [switch]$ReplaceExistingPackage,
  [switch]$ReplaceExisting
)
$ErrorActionPreference = "Stop"
$argsList = @((Join-Path $RepoRoot "tools\messagingeview_message_catalog_phase22ae_6_5_10dl_runtime_proof_evidence_decision.py"), "--repo-root", $RepoRoot)
if ($ReplaceExistingReview -or $ReplaceExistingPackage -or $ReplaceExisting) { $argsList += "--replace-existing-review" }
& $PythonExe @argsList
exit $LASTEXITCODE
