param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingReconciliation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $RepoRoot "tools\messaging\reconcile_message_catalog_phase22ae_6_5_10cj_option_b_branch.py"

$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingReconciliation) {
  $argsList += "--replace-existing-reconciliation"
}

& $PythonExe @argsList
exit $LASTEXITCODE
