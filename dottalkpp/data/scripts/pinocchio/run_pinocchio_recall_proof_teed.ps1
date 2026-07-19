<#
.SYNOPSIS
  Directly-teed transcript for the Pinocchio RECALL batching proof (Phase 1.3d)
  with its SHA-256.

.NOTES
  Host-only. MUTATES only the disposable SCR_RECALL clone (ERASEd at the end);
  the pinocchio fixtures are only read. Requires a build with the DELETE/RECALL
  index-write batching. Multi-minute (COPY + BUILDLMDB + two delete/recall A/B).

.USAGE
  From the repo root, AFTER building:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_recall_proof_teed.ps1
#>
[CmdletBinding()]
param([string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ'))

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Script = Join-Path $PSScriptRoot 'pinocchio_recall_batch_proof.dts'
$log    = Join-Path $OutDir ("recall_batch_proof_teed_{0}.log" -f $Stamp)

Write-Host "== Running recall_batch_proof -> $log (multi-minute, mutates scratch only) ==" -ForegroundColor Cyan
$content = Get-Content -Raw -LiteralPath $Script
& $DataRun -CommandLines $content *>&1 | Tee-Object -FilePath $log | Out-Null

$hash = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash
$hasElapsed = Select-String -LiteralPath $log -SimpleMatch 'ELAPSED' -Quiet

Write-Host ""
Write-Host "==== RECALL batching teed transcript ====" -ForegroundColor Green
$rel = $log.Replace($RepoRoot + '\', '').Replace('\','/')
Write-Host ("  log     : {0}" -f $rel)
Write-Host ("  SHA-256 : {0}" -f $hash)
Write-Host ("  timings : {0}" -f ($(if ($hasElapsed) {'per-command ELAPSED present'} else {'NO ELAPSED'})))
Write-Host ""
Write-Host "Confirm RA RECALL ALL ~= RB (surcharge gone), SEEK 50999999 fast, COUNT DELETED=0." -ForegroundColor Yellow
