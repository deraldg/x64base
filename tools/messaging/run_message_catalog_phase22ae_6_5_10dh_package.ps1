param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPackage,
  [switch]$ReplaceExisting
)

$ErrorActionPreference = "Stop"

$argsList = @(
  ".\tools\messaging\package_message_catalog_phase22ae_6_5_10dh_runtime_proof_staging.py",
  "--repo-root", $RepoRoot
)

if ($ReplaceExistingPackage -or $ReplaceExisting) {
  $argsList += "--replace-existing-package"
}

& $PythonExe @argsList
exit $LASTEXITCODE
