<#
.SYNOPSIS
  Produce a canonical directly-teed transcript for the Pinocchio RELATIONAL
  read-only shakedown (Phase 3a, AIF-167) and print its SHA-256, so the results
  can be recorded in the historical benchmarks ledger from a real runner log.

.WHY
  `datarun` feeds the script through the top-level `--script` runner, which
  fires per-command `SET TIMER` output (Phase-1 finding #3). This wrapper runs
  the relational battery that way and captures the FULL console (all streams)
  to a timestamped log under labtalk/proofs/runs/, then hashes it.

.NOTES
  Host-only (maintainer runs dottalkpp on the real machine). READ-ONLY against
  the pinocchio fixtures -- no mutation, nothing to rebuild afterward. Expect a
  multi-minute run: the full-walk identities pass 1M-5.5M rows each. The
  MUTATING transactional battery is a separate runner
  (run_pinocchio_reltxn_teed.ps1) -- deliberately not chained here.

.USAGE
  From the repo root:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_relational_teed.ps1
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
    @{ Label = 'relational_readonly'; Path = Join-Path $PSScriptRoot 'pinocchio_relational_readonly.dts' }
)

$results = @()
foreach ($s in $Scripts) {
    if (-not (Test-Path -LiteralPath $s.Path)) {
        Write-Warning "Missing script: $($s.Path) -- skipping."
        continue
    }
    $log = Join-Path $OutDir ("{0}_teed_{1}.log" -f $s.Label, $Stamp)
    Write-Host "== Running $($s.Label) -> $log (multi-minute; do not abort) ==" -ForegroundColor Cyan

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
