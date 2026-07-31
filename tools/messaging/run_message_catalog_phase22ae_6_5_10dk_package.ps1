param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPackage,
  [switch]$ReplaceExistingReview,
  [switch]$ReplaceExisting
)
$ErrorActionPreference = "Stop"
$argsList = @((Join-Path $RepoRoot "tools\messaging\package_message_catalog_phase22ae_6_5_10dk_runtime_proof_evidence_decision.py"), "--repo-root", $RepoRoot)
if ($ReplaceExistingPackage -or $ReplaceExistingReview -or $ReplaceExisting) { $argsList += "--replace-existing-package" }
& $PythonExe @argsList
exit $LASTEXITCODE
