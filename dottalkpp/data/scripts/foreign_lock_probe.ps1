# Foreign table lock probe. Measures, in ONE process, what a SECOND process
# could do to a table this one has fenced.
#
# OI-043's remaining half asserts that src/cli/cmd_sql_insert.cpp can grow a
# fenced table because it never calls try_lock_table. That was read from source
# and never measured. This measures it.
#
# HOW IT IS HONEST. The fence is a lock FILE. Its owner token is host:pid:ms,
# minted once per process (src/xbase/xbase_locks.cpp:41-67), and
# create_or_validate_owned removes a foreign lock ONLY when its pid is provably
# dead -- an unreadable or live owner is respected, deliberately failing closed
# (AIF-116). So a hand-written lock carrying a DIFFERENT owner string over a
# LIVE pid is, to the engine, exactly a second engine holding the table.
#
# The file format is src/xbase/xbase_locks.cpp lock_file_body():
#   DotTalk++ lock
#   owner=<host:pid:ms>
#   pid=<pid>
#   ms=<ms>
# read back by read_lock_meta, which parses pid STRICTLY and requires the whole
# field to be consumed.

$ErrorActionPreference = "Stop"
$repo    = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$sandbox = Join-Path $repo "dottalkpp\data\DBF\SANDBOX"
$dbf     = Join-Path $sandbox "LOCKP.dbf"
$lock    = "$dbf.lock"

Write-Host "repo root: $repo" -ForegroundColor DarkGray

Write-Host "=============== PART 1: fixture ===============" -ForegroundColor Cyan
& (Join-Path $repo "datarun.ps1") -AppArgs '--script','scripts\foreign_table_lock_probe_part1.dts'

if (-not (Test-Path -LiteralPath $dbf)) { throw "part 1 did not build $dbf" }

Write-Host ""
Write-Host "=============== planting a FOREIGN, LIVE table lock ===============" -ForegroundColor Cyan

# $PID is THIS PowerShell process. It is alive for the whole run, and it is not
# the dottalkpp process -- which is the entire definition of "foreign" here.
$ms   = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$body = "DotTalk++ lock`nowner=$($env:COMPUTERNAME):$PID`:$ms`npid=$PID`nms=$ms`n"
[System.IO.File]::WriteAllText($lock, $body, [System.Text.Encoding]::ASCII)

Write-Host "  wrote $lock"
Get-Content -LiteralPath $lock | ForEach-Object { Write-Host "    $_" }
Write-Host ("  harness pid $PID is alive, so the engine must treat this as a live foreign owner") -ForegroundColor DarkGray

# L5 needs a CSV to import. Two rows, matching LOCKP (ID C(4), TAG C(12)).
$feed = Join-Path (Join-Path $repo "dottalkpp\data") "lockfeed.csv"
[System.IO.File]::WriteAllText($feed, "L5A,IMPORTED1`nL5B,IMPORTED2`n", [System.Text.Encoding]::ASCII)
Write-Host "  wrote $feed for L5"
# L6 needs its own feed WITH a header row, because IMPORTSQL maps by column name.
$feed2 = Join-Path (Join-Path $repo "dottalkpp\data") "lockfeed2.csv"
[System.IO.File]::WriteAllText($feed2, "ID,TAG`nL6A,SQLIMPORTED`n", [System.Text.Encoding]::ASCII)
Write-Host "  wrote $feed2 for L6"

Write-Host ""
Write-Host "=============== PART 2: six doors ===============" -ForegroundColor Cyan
Write-Host "  L1 APPEND BLANK   expect REFUSED (append_support locks first)" -ForegroundColor Yellow
Write-Host "  L2 bare INSERT    expect ??? -- this is the measurement" -ForegroundColor Yellow
Write-Host "  L3 SQLSEL INSERT  expect REFUSED (enlist takes the fence)" -ForegroundColor Yellow
Write-Host "  L4 REPLACE        expect REFUSED (record lock checks the table lock)" -ForegroundColor Yellow
Write-Host "  L5 IMPORT         expect ??? -- appends into the CURRENT area, no lock in that file" -ForegroundColor Yellow
Write-Host "  L6 IMPORTSQL FILE expect ??? -- same shape, threaded through run_file_import" -ForegroundColor Yellow
Write-Host ""
& (Join-Path $repo "datarun.ps1") -AppArgs '--script','scripts\foreign_table_lock_probe_part2.dts'

Write-Host ""
Write-Host "=============== cleanup ===============" -ForegroundColor Cyan

# THE LOCK CHECK AND THE FEED CHECK ARE SEPARATE, AND AN EARLIER EDIT MERGED
# THEM. The lock's else-branch ended up attached to the feed's if, so a missing
# FEED would have printed "THE PLANTED LOCK IS GONE" -- a false alarm about the
# one condition this harness exists to detect honestly. Written out in full
# rather than patched again.

# The engine cannot remove a lock it does not own, so the planter removes it.
if (Test-Path -LiteralPath $lock) {
    Remove-Item -LiteralPath $lock -Force
    Write-Host "  removed the planted lock"
} else {
    Write-Host "  THE PLANTED LOCK IS GONE and this harness did not remove it." -ForegroundColor Red
    Write-Host "  Something declared a LIVE foreign owner stale. That is its own"
    Write-Host "  finding and a worse one than any arm above -- AIF-116 made that"
    Write-Host "  path fail closed on purpose."
}

foreach ($f in @($feed, $feed2)) {
    if ($f -and (Test-Path -LiteralPath $f)) {
        Remove-Item -LiteralPath $f -Force
        Write-Host ("  removed {0}" -f (Split-Path -Leaf $f))
    }
}

Write-Host ""
Write-Host "L2 / L5 / L6 are the measurement. A door that changed the table does"
Write-Host "not consult the fence, and a second engine could walk through it."
