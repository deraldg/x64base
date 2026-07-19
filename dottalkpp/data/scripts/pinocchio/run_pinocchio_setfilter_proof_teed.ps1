<#
.SYNOPSIS
  Directly-teed transcript for the Pinocchio SET FILTER string-literal fix proof
  (Phase 1.3c) with its SHA-256.

.NOTES
  Host-only. READ-ONLY against the pinocchio fixtures. Requires a build including
  the cmd_setfilter.cpp normalize_unquoted_rhs_literals change. Fast run.

.USAGE
  From the repo root, AFTER rebuilding:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_setfilter_proof_teed.ps1
#>
[CmdletBinding()]
param([string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ'))

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Script = Join-Path $PSScriptRoot 'pinocchio_setfilter_fix_proof.dts'
$log    = Join-Path $OutDir ("setfilter_fix_proof_teed_{0}.log" -f $Stamp)

Write-Host "== Running setfilter_fix_proof -> $log ==" -ForegroundColor Cyan
$content = Get-Content -Raw -LiteralPath $Script
& $DataRun -CommandLines $content *>&1 | Tee-Object -FilePath $log | Out-Null

$hash = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash
$hasElapsed = Select-String -LiteralPath $log -SimpleMatch 'ELAPSED' -Quiet

Write-Host ""
Write-Host "==== SET FILTER fix teed transcript ====" -ForegroundColor Green
$rel = $log.Replace($RepoRoot + '\', '').Replace('\','/')
Write-Host ("  log     : {0}" -f $rel)
Write-Host ("  SHA-256 : {0}" -f $hash)
Write-Host ("  timings : {0}" -f ($(if ($hasElapsed) {'per-command ELAPSED present'} else {'NO ELAPSED'})))
Write-Host ""
Write-Host "Confirm F1 == F2 == F3 == 90700 (unquoted SET FILTER now equals COUNT FOR)." -ForegroundColor Yellow
