<#
.SYNOPSIS
  Produce a canonical directly-teed transcript for the Pinocchio DESTRUCTIVE verb
  battery (Phase 1.3b) and print its SHA-256, so the timings can be recorded in
  the scale benchmarks ledger from a real runner log.

.WHY
  `datarun` feeds a script through the top-level `--script` runner, which fires
  per-command `SET TIMER` output. This wrapper runs the destructive battery that
  way and captures the FULL console (all streams) to a timestamped log under
  labtalk/proofs/runs/, then hashes it.

.SAFETY
  The battery mutates ONLY a disposable scratch clone (SCR_DESTR) that it builds
  and ERASEs; the pinocchio fixtures (STUDENTS, ENROLL) are only read. No lane
  rebuild is required afterward. Multi-minute run -- every verb is a full pass
  over ~1,000,000 rows.

.USAGE
  From the repo root:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_destructive_teed.ps1
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
    @{ Label = 'scale_destructive'; Path = Join-Path $PSScriptRoot 'pinocchio_scale_destructive.dts' }
)

$results = @()
foreach ($s in $Scripts) {
    if (-not (Test-Path -LiteralPath $s.Path)) {
        Write-Warning "Missing script: $($s.Path) -- skipping."
        continue
    }
    $log = Join-Path $OutDir ("{0}_teed_{1}.log" -f $s.Label, $Stamp)
    Write-Host "== Running $($s.Label) -> $log (multi-minute, mutates scratch only) ==" -ForegroundColor Cyan

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
Write-Host "==== Teed transcript (record this in the scale benchmarks ledger) ====" -ForegroundColor Green
foreach ($r in $results) {
    $rel = $r.Log.Replace($RepoRoot + '\', '').Replace('\','/')
    Write-Host ("{0,-18} {1}" -f $r.Label, $rel)
    Write-Host ("  SHA-256 : {0}" -f $r.Sha256)
    Write-Host ("  timings : {0}" -f ($(if ($r.HasTimings) {'per-command ELAPSED present'} else {'NO ELAPSED -- see fallback below'})))
}

if ($results | Where-Object { -not $_.HasTimings }) {
    Write-Host ""
    Write-Warning @"
A log has no per-command ELAPSED lines. Fallback: launch interactive
  .\datarun.ps1
then at the '.' prompt run:
  SET TIMER ON
  SET ALTERNATE TO tmp\pinocchio\scale_destructive_$Stamp
  SET ALTERNATE ON
  <paste the body of pinocchio_scale_destructive.dts>
  SET ALTERNATE OFF
The alternate file is the teed transcript; hash it with Get-FileHash.
"@
}

Write-Host ""
Write-Host "Post-run: SCR_DESTR is ERASEd by the script. If SCR_DESTR.cdx /" -ForegroundColor Yellow
Write-Host "SCR_DESTR.cdx.d remain under INDEXES/pinocchio or LMDB/pinocchio, remove them." -ForegroundColor Yellow
