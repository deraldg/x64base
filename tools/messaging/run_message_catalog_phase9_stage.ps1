param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [Parameter(Mandatory=$false)][string]$PythonExe = "",
  [switch]$AllowCandidateStaging
)

$ErrorActionPreference = "Stop"

if (-not $AllowCandidateStaging) {
  throw "Phase 9 requires -AllowCandidateStaging. This creates inactive candidate staging artifacts only; it does not create DBF/CDX/LMDB files or promote catalogs."
}

if (-not $PythonExe) {
  if ($env:PYTHON) { $PythonExe = $env:PYTHON }
  elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = (Get-Command python).Source }
  else { throw "No Python executable found. Pass -PythonExe `$py12 or set PYTHON." }
}

$script = Join-Path $RepoRoot "tools\messaging\stage_message_catalog_phase9_inactive_candidate.py"
& $PythonExe $script --repo-root $RepoRoot --allow-candidate-staging
exit $LASTEXITCODE
