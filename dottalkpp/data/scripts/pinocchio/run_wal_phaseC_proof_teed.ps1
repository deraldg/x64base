<#
.SYNOPSIS
  Directly-teed transcript for the Table-Buffer WAL Phase C proof (DELETE routed
  through the buffer/log) with its SHA-256.

.NOTES
  Host-only. MUTATES only the throwaway WALDEL table (ERASEd by the script).
  Requires a build with the Phase C buffered-delete change.

.USAGE
  From the repo root, AFTER building:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_wal_phaseC_proof_teed.ps1
#>
[CmdletBinding()]
param([string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ'))

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Script = Join-Path $PSScriptRoot 'wal_phaseC_proof.dts'
$log    = Join-Path $OutDir ("wal_phaseC_proof_teed_{0}.log" -f $Stamp)

Write-Host "== Running wal_phaseC_proof -> $log ==" -ForegroundColor Cyan
$content = Get-Content -Raw -LiteralPath $Script
& $DataRun -CommandLines $content *>&1 | Tee-Object -FilePath $log | Out-Null

$hash = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash
Write-Host ""
Write-Host "==== WAL Phase C teed transcript ====" -ForegroundColor Green
$rel = $log.Replace($RepoRoot + '\', '').Replace('\','/')
Write-Host ("  log     : {0}" -f $rel)
Write-Host ("  SHA-256 : {0}" -f $hash)
Write-Host ""
Write-Host "Confirm C1: COUNT DELETED 0 -> 1 across COMMIT; C2: stays 1 after ROLLBACK." -ForegroundColor Yellow
