# DD-038 daily Data Dictionary status wrapper
# Report-only wrapper. It does not accept baselines or mutate protected systems.

param(
  [string]$RepoRoot = "",
  [string]$Python = "",
  [string]$OutDir = "",
  [string]$RunId = "",
  [string[]]$Profile = @("ENGINE", "PROFESSIONAL"),
  [switch]$AcceptBaselineArtifacts,
  [switch]$FailOnReview,
  [switch]$FailOnBlocked
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
if ([string]::IsNullOrWhiteSpace($Python)) {
  $Candidate = Join-Path $RepoRoot "build\vcpkg_installed\x64-windows\tools\python3\python.exe"
  if (Test-Path $Candidate) {
    $Python = $Candidate
  } else {
    $Python = "python"
  }
}
if ([string]::IsNullOrWhiteSpace($RunId)) {
  $RunId = "DDSTATUS-current"
}
if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDir = Join-Path $RepoRoot ("docs\datadict\reports\" + $RunId)
}

$PointerPath = Join-Path $RepoRoot "docs\datadict\baselines\current_baseline.json"
if (-not (Test-Path $PointerPath)) {
  throw "Current baseline pointer not found: $PointerPath"
}

$Pointer = Get-Content $PointerPath -Raw | ConvertFrom-Json
$BaselinePath = Join-Path $RepoRoot ($Pointer.baseline_path -replace '/', '\')
if (-not (Test-Path $BaselinePath)) {
  throw "Current baseline path not found: $BaselinePath"
}

Write-Host "[DD-STATUS] repo: $RepoRoot"
Write-Host "[DD-STATUS] baseline: $($Pointer.baseline_id)"
Write-Host "[DD-STATUS] baseline path: $BaselinePath"
Write-Host "[DD-STATUS] out: $OutDir"

$args034 = @(
  (Join-Path $RepoRoot "tools\datadict\baseline\baseline_status.py"),
  "--repo-root", $RepoRoot,
  "--baseline", $BaselinePath,
  "--out-dir", $OutDir,
  "--run-id", $RunId
)
foreach ($p in $Profile) {
  $args034 += @("--profile", $p)
}
& $Python @args034

$Manifest034 = Join-Path $OutDir "dd034_daily_redoc_status_manifest.json"
if (-not (Test-Path $Manifest034)) {
  throw "DD-034 manifest not found: $Manifest034"
}
$M034 = Get-Content $Manifest034 -Raw | ConvertFrom-Json
$FinalStatus = $M034.status

if ($AcceptBaselineArtifacts -and ($M034.review_rows -gt 0)) {
  $ClosureDir = Join-Path $RepoRoot ("docs\datadict\review_queue\" + $RunId + "-acceptance-artifact-closure")
  $args036 = @(
    (Join-Path $RepoRoot "tools\datadict\baseline\baseline_acceptance_artifact_closure.py"),
    "--dd034", $OutDir,
    "--out-dir", $ClosureDir,
    "--run-id", ($RunId + "-acceptance-artifact-closure"),
    "--baseline-id", $Pointer.baseline_id,
    "--accept-acceptance-artifacts"
  )
  foreach ($p in $Profile) {
    $args036 += @("--profile", $p)
  }
  & $Python @args036

  $ClosureStatusDir = Join-Path $RepoRoot ("docs\datadict\reports\" + $RunId + "-status-closure")
  $args037 = @(
    (Join-Path $RepoRoot "tools\datadict\baseline\baseline_status_closure.py"),
    "--dd034", $OutDir,
    "--dd036", $ClosureDir,
    "--out-dir", $ClosureStatusDir,
    "--run-id", ($RunId + "-status-closure"),
    "--baseline-id", $Pointer.baseline_id
  )
  foreach ($p in $Profile) {
    $args037 += @("--profile", $p)
  }
  & $Python @args037

  $Manifest037 = Join-Path $ClosureStatusDir "dd037_status_closure_manifest.json"
  if (Test-Path $Manifest037) {
    $M037 = Get-Content $Manifest037 -Raw | ConvertFrom-Json
    $FinalStatus = $M037.status
  }
}

Write-Host "[DD-STATUS] final status: $FinalStatus"

if ($FailOnBlocked -and ($FinalStatus -like "BLOCKED*" -or $FinalStatus -eq "TOOL_ERROR")) {
  exit 2
}
if ($FailOnReview -and ($FinalStatus -notlike "PASS*")) {
  exit 1
}
exit 0
