# Does crash recovery LOSE anything when the table is held by another engine?
#
# WHY THIS AND NOT THE WHOLE-LOOP FENCE. COMMIT already holds a table lock for
# the entire transaction when the buffer carries an INSERT (cmd_commit.cpp:658,
# gated on has_insert, declared "released LAST"). Recovery does not -- it fences
# each append. Under rule (A) an interleaved replay is SAFE, because rows
# interleave rather than clobber, so the whole-loop fence buys CONTIGUITY and
# not correctness. What would make it urgent is recovery LOSING rows when the
# table is held, and that is answerable without two processes.
#
# Same technique as the six-door probe: the fence is a lock FILE whose owner is
# host:pid:ms, and create_or_validate_owned removes one only when its pid is
# PROVABLY dead. A hand-written lock over this harness's own live pid IS a
# second engine as far as the engine can tell.

$ErrorActionPreference = "Stop"
$repo    = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$sandbox = Join-Path $repo "dottalkpp\data\DBF\SANDBOX"
$dbf     = Join-Path $sandbox "JRN5.dbf"
$lock    = "$dbf.lock"
$tbj     = "$dbf.tbj"

function Show-Log([string]$when) {
    if (Test-Path -LiteralPath $tbj) {
        Write-Host ("  {0}: LOG PRESENT ({1} bytes)" -f $when, (Get-Item $tbj).Length) -ForegroundColor Green
    } else {
        Write-Host ("  {0}: LOG GONE" -f $when) -ForegroundColor Red
    }
}

Write-Host "=============== PART 1: fixture ===============" -ForegroundColor Cyan
& (Join-Path $repo "datarun.ps1") -AppArgs '--script','scripts\recovery_under_foreign_lock_part1.dts'
if (-not (Test-Path -LiteralPath $dbf)) { throw "part 1 did not build $dbf" }

Write-Host ""
Write-Host "=============== planting a TWO-RECORD journal and a FOREIGN lock ===============" -ForegroundColor Cyan
# ID C(4), TAG C(12).  "R1"=5231 "RECOVER1"=5245434F56455231
#                      "R2"=5232 "RECOVER2"=5245434F56455232
# Two I records, so this is a multi-row replay -- the case a per-append fence
# cannot hold together.
$log = "TBJ1 JRN5`nI 3 1 S 1:5231 2:5245434F56455231`nI 4 1 S 1:5232 2:5245434F56455232`nC 2`n"
[System.IO.File]::WriteAllText($tbj, $log, [System.Text.Encoding]::ASCII)
Write-Host ("  wrote {0} ({1} bytes, TWO I records)" -f $tbj, (Get-Item $tbj).Length)

$ms   = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$body = "DotTalk++ lock`nowner=$($env:COMPUTERNAME):$PID`:$ms`npid=$PID`nms=$ms`n"
[System.IO.File]::WriteAllText($lock, $body, [System.Text.Encoding]::ASCII)
Write-Host ("  planted {0} -- harness pid {1}, alive for the whole run" -f $lock, $PID)

Write-Host ""
Write-Host "=============== PART 2: USE with the table HELD ===============" -ForegroundColor Cyan
Show-Log "before"
& (Join-Path $repo "datarun.ps1") -AppArgs '--script','scripts\recovery_under_foreign_lock_part2.dts'
Write-Host ""
Show-Log "after "
Write-Host "  A LOG PRESENT here is OI-044 working: a record the replay could not" -ForegroundColor Yellow
Write-Host "  place is a COMMITTED row, and the log is the only evidence it exists." -ForegroundColor Yellow
Write-Host "  A LOG GONE here would be the defect that makes the fence urgent." -ForegroundColor Yellow

Write-Host ""
Write-Host "=============== releasing the lock, keeping the log ===============" -ForegroundColor Cyan
Remove-Item -LiteralPath $lock -Force
Write-Host "  lock removed"
Show-Log "still "

Write-Host ""
Write-Host "=============== PART 3: retry, unheld ===============" -ForegroundColor Cyan
& (Join-Path $repo "datarun.ps1") -AppArgs '--script','scripts\recovery_under_foreign_lock_part3.dts'
Write-Host ""
Show-Log "after "
Write-Host "  EXPECT count 4 with R1/RECOVER1 and R2/RECOVER2, and the LOG GONE --" -ForegroundColor Yellow
Write-Host "  deleted correctly this time because nothing was skipped." -ForegroundColor Yellow
Write-Host ""
Write-Host "  IF PART 3 RECOVERS BOTH ROWS: recovery is RETRYABLE and LOSSLESS, so" -ForegroundColor Yellow
Write-Host "  per-append fencing is sufficient and the whole-loop fence is a" -ForegroundColor Yellow
Write-Host "  contiguity nicety rather than a correctness fix." -ForegroundColor Yellow

Write-Host ""
Write-Host "=============== cleanup ===============" -ForegroundColor Cyan
foreach ($f in @($lock, $tbj)) {
    if (Test-Path -LiteralPath $f) { Remove-Item -LiteralPath $f -Force; Write-Host ("  removed {0}" -f (Split-Path -Leaf $f)) }
}
Write-Host "NOTHING COMMITTED." -ForegroundColor Yellow
