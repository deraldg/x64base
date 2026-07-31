param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingIntake
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\intake_message_catalog_phase22ae_6_5_10dn_b_operator_help_target_evidence.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingIntake) { $argsList += "--replace-existing-intake" }
& $PythonExe @argsList
exit $LASTEXITCODE
