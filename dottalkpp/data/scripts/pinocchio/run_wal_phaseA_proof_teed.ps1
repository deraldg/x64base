<#
.SYNOPSIS
  Directly-teed transcript for the Table-Buffer WAL Phase A proof, plus a check
  that no .tbj redo log lingers after clean commit/rollback.

.NOTES
  Host-only. MUTATES only a throwaway table (WALDEMO), ERASEd by the script.
  Requires a build with the Phase A WAL writer (table_state.cpp).

.USAGE
  From the repo root, AFTER building:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_wal_phaseA_proof_teed.ps1
#>
[CmdletBinding()]
param([string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ'))

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Script = Join-Path $PSScriptRoot 'wal_phaseA_proof.dts'
$log    = Join-Path $OutDir ("wal_phaseA_proof_teed_{0}.log" -f $Stamp)

Write-Host "== Running wal_phaseA_proof -> $log ==" -ForegroundColor Cyan
$content = Get-Content -Raw -LiteralPath $Script
& $DataRun -CommandLines $content *>&1 | Tee-Object -FilePath $log | Out-Null

$hash = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash

# After a clean commit + rollback the redo log must be gone. Look for leftovers.
$leftover = Get-ChildItem -Path $RepoRoot -Recurse -Filter '*.tbj' -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match 'WALDEMO|area\d+\.tbj' }

Write-Host ""
Write-Host "==== WAL Phase A teed transcript ====" -ForegroundColor Green
$rel = $log.Replace($RepoRoot + '\', '').Replace('\','/')
Write-Host ("  log      : {0}" -f $rel)
Write-Host ("  SHA-256  : {0}" -f $hash)
if ($leftover) {
    Write-Host ("  .tbj     : LEFTOVER logs found (should be none after clean commit/rollback):") -ForegroundColor Yellow
    $leftover | ForEach-Object { Write-Host ("    {0}" -f $_.FullName) }
} else {
    Write-Host ("  .tbj     : none lingering (log removed on commit/rollback) -- expected") -ForegroundColor Green
}
Write-Host ""
Write-Host "Confirm P3 NAME=Alpha2 (commit applied), P4 NAME=Beta (rollback discarded)." -ForegroundColor Yellow
