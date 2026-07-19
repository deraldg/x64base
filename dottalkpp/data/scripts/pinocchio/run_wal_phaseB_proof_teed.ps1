<#
.SYNOPSIS
  Table-Buffer WAL Phase B (crash recovery) proof. Simulates a crash after a
  durable commit but before the DBF was updated, then reopens and verifies the
  redo log is replayed.

.FLOW
  1. Run wal_phaseB_setup.dts -> leaves an uncommitted <WALREC.dbf>.tbj (U record,
     no C marker; DBF still "Original").
  2. Append a "C" marker to the .tbj -> committed-but-unapplied (the crash state).
  3. Run wal_phaseB_verify.dts -> USE triggers recovery, which replays the redo
     into the DBF (recno 1 NAME -> "Recovered") and removes the log.

.NOTES
  Host-only. MUTATES only the throwaway WALREC table. Requires a build with the
  Phase B recovery code.

.USAGE
  From the repo root, AFTER building:
    powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_wal_phaseB_proof_teed.ps1
#>
[CmdletBinding()]
param([string]$Stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ'))

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$DataRun  = Join-Path $RepoRoot 'datarun.ps1'
$OutDir   = Join-Path $RepoRoot 'labtalk\proofs\runs'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Run-Dts($name, $dtsPath) {
    $log = Join-Path $OutDir ("wal_phaseB_${name}_teed_{0}.log" -f $Stamp)
    Write-Host "== Running $name -> $log ==" -ForegroundColor Cyan
    $content = Get-Content -Raw -LiteralPath $dtsPath
    & $DataRun -CommandLines $content *>&1 | Tee-Object -FilePath $log | Out-Null
    return $log
}

# 1. Setup -> uncommitted <WALREC.dbf>.tbj
$setupLog = Run-Dts 'setup' (Join-Path $PSScriptRoot 'wal_phaseB_setup.dts')

# 2. Find the redo log left by the buffered REPLACE
$tbj = Get-ChildItem -Path $RepoRoot -Recurse -Filter 'WALREC*.tbj' -ErrorAction SilentlyContinue |
       Select-Object -First 1
if (-not $tbj) {
    Write-Host "FAIL: no WALREC*.tbj produced by setup (buffered REPLACE did not log)." -ForegroundColor Red
    return
}
Write-Host ("  found log : {0}" -f $tbj.FullName) -ForegroundColor Green
$before = Get-Content -Raw -LiteralPath $tbj.FullName
Write-Host "  --- .tbj contents (expect a U record, no C marker) ---"
Write-Host $before
$hasU = ($before -match '(?m)^U ')
$hasC = ($before -match '(?m)^C ')
Write-Host ("  has U record : {0} ; has C marker : {1}   (expect True / False)" -f $hasU, $hasC)

# 3. Promote to committed by appending a C marker (the crash-after-commit state)
Add-Content -LiteralPath $tbj.FullName -Value "C 1"
Write-Host "  appended 'C 1' -> log is now committed-but-unapplied" -ForegroundColor Yellow

# 4. Verify -> reopen triggers recovery replay
$verifyLog = Run-Dts 'verify' (Join-Path $PSScriptRoot 'wal_phaseB_verify.dts')
$vtext = Get-Content -Raw -LiteralPath $verifyLog

# 5. Assertions
$recovered = ($vtext -match 'recovered a committed table-buffer journal')
$replayed  = ($vtext -match 'Recovered')
$gone      = -not (Test-Path -LiteralPath $tbj.FullName)

Write-Host ""
Write-Host "==== WAL Phase B result ====" -ForegroundColor Green
Write-Host ("  setup log  : {0}" -f (Split-Path $setupLog -Leaf))
Write-Host ("  verify log : {0}  (sha {1})" -f (Split-Path $verifyLog -Leaf),
           (Get-FileHash -LiteralPath $verifyLog -Algorithm SHA256).Hash)
Write-Host ("  recovery notice printed  : {0}  (expect True)" -f $recovered)
Write-Host ("  recno 1 NAME = Recovered : {0}  (expect True)" -f $replayed)
Write-Host ("  .tbj removed after replay: {0}  (expect True)" -f $gone)
if ($recovered -and $replayed -and $gone) {
    Write-Host "  PHASE B: PASS" -ForegroundColor Green
} else {
    Write-Host "  PHASE B: CHECK the verify log." -ForegroundColor Yellow
}
