param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [switch]$ReplaceExistingPackage
)
$script = Join-Path $RepoRoot "tools\messaging\package_message_catalog_phase22ae_6_5_10dm_runtime_exit_crash_triage.py"
$args = @($script, "--repo-root", $RepoRoot)
if ($ReplaceExistingPackage) { $args += "--replace-existing-package" }
& $PythonExe @args
exit $LASTEXITCODE
