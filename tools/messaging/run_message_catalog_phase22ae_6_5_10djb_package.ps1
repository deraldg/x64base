param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPackage,
  [switch]$ReplaceExisting
)
$ErrorActionPreference = "Stop"
$argsList = @((Join-Path $RepoRoot "tools\messaging\package_message_catalog_phase22ae_6_5_10djb_runtime_proof_crash_review_and_clean_rerun.py"), "--repo-root", $RepoRoot)
if ($ReplaceExistingPackage -or $ReplaceExisting) { $argsList += "--replace-existing-package" }
& $PythonExe @argsList
exit $LASTEXITCODE
