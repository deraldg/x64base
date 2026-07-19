<#
.SYNOPSIS
  Produce a canonical directly-teed transcript for the Pinocchio scale read-only
  verb battery (Phase 1.3a) and print its SHA-256, so the results can be recorded
  in the historical benchmarks ledger from a real runner log rather than a chat
  paste.

.WHY
  `datarun` feeds a script through the top-level `--script` runner, which fires
  per-command `SET TIMER` output (unlike `DOTSCRIPT` nesting; Phase-1 finding #3).
  This wrapper runs the scale battery that way and captures the FULL console (all
  streams) to a timestamped log under labtalk/proofs/runs/, then hashes it.

.NOTES
  Host-only (maintainer runs dottalkpp on the real machine). READ-ONLY against the
  pinocchio fixtures -- no mutation, nothing to rebuild afterward. This is the
  "phase 1 (read-only) first" battery; the destructive battery is a separate run.
  Expect a multi-minute run: every LINEAR verb makes a full pass over the table.

.USAGE
  From the repo root:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_scale_teed.ps1
#>
[CmdletBinding()]
param(
    [string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'

# Repo root is four levels up from dottalkpp/data/scripts/pinocchio/.
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
# Durable, versioned proof home (same lane as the other labtalk/proofs/runs logs).
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Scripts = @(
    @{ Label = 'scale_readonly'; Path = Join-Path $PSScriptRoot 'pinocchio_scale_readonly.dts' }
)

$results = @()
foreach ($s in $Scripts) {
    if (-not (Test-Path -LiteralPath $s.Path)) {
        Write-Warning "Missing script: $($s.Path) -- skipping."
        continue
    }
    $log = Join-Path $OutDir ("{0}_teed_{1}.log" -f $s.Label, $Stamp)
    Write-Host "== Running $($s.Label) -> $log (multi-minute; do not abort) ==" -ForegroundColor Cyan

    # Pass the script CONTENT as -CommandLines so datarun runs it through the
    # top-level --script path (per-command timing fires). Capture ALL streams.
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
    Write-Host ("{0,-16} {1}" -f $r.Label, $rel)
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
  SET ALTERNATE TO tmp\pinocchio\scale_readonly_$Stamp
  SET ALTERNATE ON
  <paste the body of pinocchio_scale_readonly.dts>
  SET ALTERNATE OFF
The alternate file is the teed transcript; hash it with Get-FileHash.
"@
}

Write-Host ""
Write-Host "Next: send the relative path + SHA-256 back so the STUDENTS-vs-ENROLL" -ForegroundColor Yellow
Write-Host "ELAPSED numbers can be recorded (flat verbs, linear verbs, SEEK sentinel)." -ForegroundColor Yellow
