param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPackage
)

$ErrorActionPreference = "Stop"
$args = @("--repo-root", $RepoRoot)
if ($ReplaceExistingPackage) { $args += "--replace-existing-package" }
& $PythonExe (Join-Path $RepoRoot "tools\messaging\package_message_catalog_phase22ae_6_5_10dq_shutdown_isolation_proof.py") @args
exit $LASTEXITCODE
