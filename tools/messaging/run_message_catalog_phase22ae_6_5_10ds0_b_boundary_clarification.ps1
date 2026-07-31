param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingClarification
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\clarify_message_catalog_phase22ae_6_5_10ds0_b_tooling_boundary_help_apply_intent.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingClarification) { $argsList += "--replace-existing-clarification" }
& $PythonExe @argsList
exit $LASTEXITCODE
