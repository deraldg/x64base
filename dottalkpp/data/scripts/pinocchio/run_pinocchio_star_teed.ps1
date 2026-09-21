<#
.SYNOPSIS
  Produce a canonical directly-teed transcript for the Pinocchio STAR battery
  (Phase 3c, AIF-167) and print its SHA-256.

.WHY
  Same teed-transcript discipline as every Pinocchio battery: datarun runs the
  script through the top-level --script path (per-command SET TIMER fires), the
  FULL console goes to a timestamped log under labtalk/proofs/runs/, and the
  hash is what the benchmarks ledger cites.

.NOTES
  Host-only. READ-ONLY against fixtures AND dims. Prerequisites, in order:
    1. dottalkpp\scripts\pinocchio\gen_pinocchio_dims.ps1   (CSVs, seconds)
    2. datarun with pinocchio_build_dims.dts                (tables, ~1 min)
    3. the 3c form smoke at 200 rows                        (seconds)
  Expect ~15-25 minutes; the dim-driven joins process the 5.5M candidate
  stream three times.

.USAGE
  From the repo root:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_star_teed.ps1
#>
[CmdletBinding()]
param(
    [string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'

# Repo root is four levels up from dottalkpp/data/scripts/pinocchio/.
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Scripts = @(
    @{ Label = 'star_readonly'; Path = Join-Path $PSScriptRoot 'pinocchio_star_readonly.dts' }
)

$results = @()
foreach ($s in $Scripts) {
    if (-not (Test-Path -LiteralPath $s.Path)) {
        Write-Warning "Missing script: $($s.Path) -- skipping."
        continue
    }
    $log = Join-Path $OutDir ("{0}_teed_{1}.log" -f $s.Label, $Stamp)
    Write-Host "== Running $($s.Label) -> $log (~15-25 min; do not abort) ==" -ForegroundColor Cyan

    $content = Get-Content -Raw -LiteralPath $s.Path
    & $DataRun -CommandLines $content *>&1 | Tee-Object -FilePath $log | Out-Null

    $hash = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash
    $hasElapsed = Select-String -LiteralPath $log -SimpleMatch 'ELAPSED' -Quiet
    $results += [pscustomobject]@{
        Label      = $s.Label
        Log        = $log
        Sha256     = $hash
        HasTimings = [bool]$hasElapsed
    }
}

Write-Host ""
Write-Host "==== Teed transcript (record this in the benchmarks ledger) ====" -ForegroundColor Green
foreach ($r in $results) {
    $rel = $r.Log.Replace($RepoRoot + '\', '').Replace('\','/')
    Write-Host ("{0,-20} {1}" -f $r.Label, $rel)
    Write-Host ("  SHA-256 : {0}" -f $r.Sha256)
    Write-Host ("  timings : {0}" -f ($(if ($r.HasTimings) {'per-command ELAPSED present'} else {'NO ELAPSED -- SET TIMER did not fire; rerun via datarun --script, do not record'})))
}
