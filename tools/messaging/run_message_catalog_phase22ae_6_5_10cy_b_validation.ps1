param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingValidation,
  [switch]$AllowMissingCxBSavepoint
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\validate_message_catalog_phase22ae_6_5_10cy_b_help_cmdhelpchk_candidate_mapping.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingValidation) { $argsList += "--replace-existing-validation" }
if ($AllowMissingCxBSavepoint) { $argsList += "--allow-missing-cx-b-savepoint" }
& $PythonExe @argsList
exit $LASTEXITCODE
