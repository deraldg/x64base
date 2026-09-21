<#
.SYNOPSIS
  Produce a canonical directly-teed transcript for the Pinocchio TRANSACTIONAL
  DML shakedown (Phase 3b, AIF-167) and print its SHA-256.

.WHY
  Same teed-transcript discipline as every Pinocchio battery: datarun runs the
  script through the top-level --script path (per-command SET TIMER fires), the
  FULL console goes to a timestamped log under labtalk/proofs/runs/, and the
  hash is what the benchmarks ledger cites.

.NOTES
  Host-only. MUTATING -- but only against the disposable clones SCR_SQLTXN and
  SCR_SQLTX2, which the script builds by COPY TO and ERASEs at the end. The
  pinocchio fixtures (STUDENTS, ENROLL) are only read. If a run aborts midway,
  simply rerun: the script drops stale clones at startup. Expect several
  minutes -- two 1M-row COPY TO clones (~84 s each) plus BUILDLMDB (~18 s)
  dominate. Run the READ-ONLY battery (run_pinocchio_relational_teed.ps1)
  first; this one assumes nothing from it but the pairing keeps evidence tidy.

.USAGE
  From the repo root:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_reltxn_teed.ps1
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
    @{ Label = 'relational_txn'; Path = Join-Path $PSScriptRoot 'pinocchio_relational_txn.dts' }
)

$results = @()
foreach ($s in $Scripts) {
    if (-not (Test-Path -LiteralPath $s.Path)) {
        Write-Warning "Missing script: $($s.Path) -- skipping."
        continue
    }
    $log = Join-Path $OutDir ("{0}_teed_{1}.log" -f $s.Label, $Stamp)
    Write-Host "== Running $($s.Label) -> $log (several minutes; do not abort) ==" -ForegroundColor Cyan

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
