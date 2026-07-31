param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPackage
)
$ErrorActionPreference = "Stop"
$script = Join-Path $RepoRoot "tools\messaging\package_message_catalog_phase22ae_6_5_10ds_dotscript_shutdown_exit_crash_fix_plan.py"
$argsList = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingPackage) { $argsList += "--replace-existing-package" }
& $PythonExe @argsList
exit $LASTEXITCODE
