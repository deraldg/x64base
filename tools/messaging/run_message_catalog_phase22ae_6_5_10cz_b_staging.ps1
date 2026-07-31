param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingStaging,
  [switch]$AllowMissingCyBSavepoint
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\stage_message_catalog_phase22ae_6_5_10cz_b_help_cmdhelpchk_candidate_table_native_materialization.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingStaging) { $argsList += "--replace-existing-staging" }
if ($AllowMissingCyBSavepoint) { $argsList += "--allow-missing-cy-b-savepoint" }
& $PythonExe @argsList
exit $LASTEXITCODE
