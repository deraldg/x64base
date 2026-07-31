param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingSelection
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $RepoRoot "tools\messaging\select_message_catalog_phase22ae_6_5_10cj_option_b.py"

$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingSelection) {
  $argsList += "--replace-existing-selection"
}

& $PythonExe @argsList
exit $LASTEXITCODE
