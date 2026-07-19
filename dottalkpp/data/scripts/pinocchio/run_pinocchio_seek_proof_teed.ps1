<#
.SYNOPSIS
  Directly-teed transcript for the Pinocchio SEEK fix proof (Phase 1.3c) with its
  SHA-256, so the before/after SEEK numbers can be recorded from a real runner log.

.NOTES
  Host-only. READ-ONLY against the pinocchio fixtures. Requires a build that
  includes the cmd_seek.cpp keyed-range-seek change. Fast run (a handful of SEEKs;
  the whole point is that the slow ones are now milliseconds).

.USAGE
  From the repo root, AFTER rebuilding:
    cmake --build .\build --config Release
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_seek_proof_teed.ps1
#>
[CmdletBinding()]
param(
    [string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ')
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Script = Join-Path $PSScriptRoot 'pinocchio_seek_fix_proof.dts'
$log    = Join-Path $OutDir ("seek_fix_proof_teed_{0}.log" -f $Stamp)

Write-Host "== Running seek_fix_proof -> $log ==" -ForegroundColor Cyan
$content = Get-Content -Raw -LiteralPath $Script
& $DataRun -CommandLines $content *>&1 | Tee-Object -FilePath $log | Out-Null

$hash = (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash
$hasElapsed = Select-String -LiteralPath $log -SimpleMatch 'ELAPSED' -Quiet

Write-Host ""
Write-Host "==== SEEK fix teed transcript ====" -ForegroundColor Green
$rel = $log.Replace($RepoRoot + '\', '').Replace('\','/')
Write-Host ("  log     : {0}" -f $rel)
Write-Host ("  SHA-256 : {0}" -f $hash)
Write-Host ("  timings : {0}" -f ($(if ($hasElapsed) {'per-command ELAPSED present'} else {'NO ELAPSED'})))
Write-Host ""
Write-Host "Confirm S2/S6 collapsed to ~ms and the Found-at recnos are unchanged." -ForegroundColor Yellow
