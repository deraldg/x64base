<#
.SYNOPSIS
  Produce canonical directly-teed transcripts for the Pinocchio nav proof scripts
  and print their SHA-256, so the historical benchmarks ledger can be rebound from
  a chat-sourced capture to a real runner log.

.WHY
  `datarun` feeds a script through the top-level `--script` runner, which fires
  per-command `SET TIMER` output (unlike `DOTSCRIPT` nesting; Phase-1 finding #3).
  This wrapper runs the two nav proof scripts that way and captures the FULL
  console (all streams) to timestamped logs under data/tmp/pinocchio/, then hashes
  them. The logs are the teed raw transcripts; the hashes rebind the ledger.

.NOTES
  Host-only (maintainer runs dottalkpp on the real machine). Read-only against the
  pinocchio fixtures. Output logs are derived/gitignored like all pinocchio data.
  Placement: co-located with the pinocchio proof lane; move under tools/ if the
  maintenance-script-root policy requires it.

.USAGE
  From the repo root:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_nav_teed.ps1
#>
[CmdletBinding()]
param(
    [string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'

# Repo root is four levels up from dottalkpp/data/scripts/pinocchio/.
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
# Durable, versioned proof home (same lane as the other labtalk/proofs/runs logs),
# so the teed transcript is retained evidence rather than gitignored churn.
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# The two proof scripts to tee, and a friendly label for each log.
$Scripts = @(
    @{ Label = 'nav_defect_after';        Path = Join-Path $PSScriptRoot 'pinocchio_nav_defect_proof.dts' },
    @{ Label = 'nav_filter_boundary_after'; Path = Join-Path $PSScriptRoot 'pinocchio_nav_filter_boundary.dts' }
)

$results = @()
foreach ($s in $Scripts) {
    if (-not (Test-Path -LiteralPath $s.Path)) {
        Write-Warning "Missing script: $($s.Path) -- skipping."
        continue
    }
    $log = Join-Path $OutDir ("{0}_teed_{1}.log" -f $s.Label, $Stamp)
    Write-Host "== Running $($s.Label) -> $log ==" -ForegroundColor Cyan

    # Pass the script CONTENT as -CommandLines so datarun runs it through the
    # top-level --script path (per-command timing fires). Capture ALL streams.
    $content = Get-Content -Raw -LiteralPath $s.Path
    & $DataRun -CommandLines $content *>&1 | Tee-Object -FilePath $log | Out-Null

    $hash = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash
    $hasElapsed = Select-String -LiteralPath $log -SimpleMatch 'ELAPSED' -Quiet
    $results += [pscustomobject]@{
        Label       = $s.Label
        Log         = $log
        Sha256      = $hash
        HasTimings  = [bool]$hasElapsed
    }
}

Write-Host ""
Write-Host "==== Teed transcripts (rebind the ledger with these) ====" -ForegroundColor Green
foreach ($r in $results) {
    $rel = $r.Log.Replace($RepoRoot + '\', '').Replace('\','/')
    Write-Host ("{0,-26} {1}" -f $r.Label, $rel)
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
  SET ALTERNATE TO tmp\pinocchio\nav_after_teed_$Stamp
  SET ALTERNATE ON
  <paste the body of the proof .dts>
  SET ALTERNATE OFF
The alternate file is the teed transcript; hash it with Get-FileHash.
"@
}

Write-Host ""
Write-Host "Next: send the two relative paths + SHA-256 values back to rebind" -ForegroundColor Yellow
Write-Host "docs/maintenance/PINOCCHIO_HISTORICAL_ENGINE_BENCHMARKS_V1.csv" -ForegroundColor Yellow
Write-Host "(after_evidence_path/sha256, transcript_status -> RAW_TEED_TRANSCRIPT)." -ForegroundColor Yellow
