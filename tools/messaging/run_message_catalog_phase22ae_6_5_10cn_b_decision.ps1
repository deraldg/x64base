param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingDecision
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $RepoRoot "tools\messaging\decide_message_catalog_phase22ae_6_5_10cn_b_option_b_reuse_proof.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingDecision) { $argsList += "--replace-existing-decision" }

& $PythonExe @argsList
exit $LASTEXITCODE
