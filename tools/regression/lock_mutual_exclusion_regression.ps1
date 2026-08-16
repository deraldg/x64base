# lock_mutual_exclusion_regression.ps1
# ============================================================================
# AIF-116 regression -- cross-process lock enforcement and stale recovery.
#
# WHY THIS EXISTS. Mutual exclusion was broken engine-wide on Windows from
# 2025-08-31 until 2026-08-15 and no test caught it, because no test of the
# lock subsystem existed at all:
#     grep -rln "try_lock_table|try_lock_record|LOCK TABLE|xbase::locks" tests/
# returned nothing. The defect was deterministic, not subtle. It survived
# because nobody looked.
#
# WHY POWERSHELL AND NOT A .dts. The property under test is CROSS-PROCESS.
# A script running inside one engine instance cannot express it.
#
# WHY IT MUST RUN ON WINDOWS. The defect cannot reproduce under POSIX:
# utf8_init.hpp installs C.UTF-8 there, which carries classic numeric facets.
# The Windows branch takes the native locale. A green suite on WSL proves
# nothing about this. See AIF-116 section 12b.
#
# METHOD, AND ITS ONE TRADE-OFF. Tests 3 and 4 FABRICATE a .lock sidecar with
# a chosen pid instead of orchestrating a second live engine. That makes
# "owner is alive" and "owner is dead" deterministic rather than timing
# dependent. The cost: this script hardcodes the sidecar FORMAT, so a
# deliberate format change will fail these tests. That is arguably a feature --
# the format is a cross-process protocol and changing it should be noticed --
# but it is a coupling and it is recorded here rather than discovered later.
#
# Usage:
#   pwsh -File tools\regression\lock_mutual_exclusion_regression.ps1
#   pwsh -File tools\regression\lock_mutual_exclusion_regression.ps1 -Verbose
#
# Exit codes: 0 all pass, 1 one or more failures.
# ============================================================================

[CmdletBinding()]
param(
    [string]$Root = "D:\code\ccode"
)

$ErrorActionPreference = "Stop"

$DataRun   = Join-Path $Root "datarun.ps1"
$Sandbox   = Join-Path $Root "dottalkpp\data\dbf\sandbox"
$TableName = "LOCKREGR"
$Dbf       = Join-Path $Sandbox "$TableName.dbf"
$LockFile  = "$Dbf.lock"

$script:Pass = 0
$script:Fail = 0

function Test-Result {
    # $Evidence is the engine output that produced the verdict. A failing
    # assertion that does not show what it saw is not a test result, it is a
    # rumour -- so the output is printed on failure, always.
    param([string]$Name, [bool]$Ok, [string]$Detail = "", [string]$Evidence = "")
    if ($Ok) {
        Write-Host ("  PASS  " + $Name) -ForegroundColor Green
        $script:Pass++
    } else {
        Write-Host ("  FAIL  " + $Name) -ForegroundColor Red
        if ($Detail) { Write-Host ("        " + $Detail) -ForegroundColor Red }
        if ($Evidence) {
            Write-Host "        ---- engine output ----" -ForegroundColor DarkYellow
            foreach ($line in ($Evidence -split "`r?`n")) {
                if ($line -match '^\s*$') { continue }
                if ($line -match '^WARNING:') { continue }
                Write-Host ("        | " + $line) -ForegroundColor DarkYellow
            }
            Write-Host "        -----------------------" -ForegroundColor DarkYellow
        }
        $script:Fail++
    }
}

function Invoke-Engine {
    # Each call is a fresh engine process. Returns combined output as one string.
    param([string[]]$Lines)
    $all = @("do sandbox") + $Lines
    $out = & $DataRun -CommandLines $all 2>&1 | Out-String
    Write-Verbose $out
    return $out
}

function Write-Sidecar {
    param([string]$Path, [string]$PidText, [string]$Host_ = "REGRESSION")
    $ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $body = "DotTalk++ lock`nowner=${Host_}:${PidText}:${ms}`npid=${PidText}`nms=${ms}`n"
    [System.IO.File]::WriteAllText($Path, $body)
}

function Remove-Locks {
    Get-ChildItem -Path $Sandbox -Filter "*.lock*" -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "AIF-116 lock regression" -ForegroundColor Cyan
Write-Host "Root: $Root"

if (-not $IsWindows) {
    Write-Host "SKIP: this regression is Windows-only by design (AIF-116 12b)." -ForegroundColor Yellow
    exit 0
}

# --- setup -------------------------------------------------------------------
# The fixture MUST verify itself. A silently-empty table makes T5 report a
# lock defect that did not happen -- which is how the first run of this script
# behaved, and is precisely the failure family this lane exists to document.
Remove-Locks

# Create in its own process. CREATE leaves the new table open in the current
# area and closes whatever was there, so mixing it with the populate step makes
# the area state harder to reason about than it needs to be.
$null = Invoke-Engine @("CREATE X64 $TableName (ID I, NOTE C(32))")
if (-not (Test-Path $Dbf)) {
    Write-Host "SETUP FAILED: $Dbf was not created." -ForegroundColor Red
    exit 1
}

# Populate in a fresh process, then COUNT in that same process.
$setup = Invoke-Engine @(
    "SELECT 1",
    "USE $TableName",
    "APPEND_BLANK",
    "REPLACE ID WITH 1",
    "REPLACE NOTE WITH `"lock regression fixture`"",
    "GO TOP",
    "COUNT"
)

# Re-open in yet another process and confirm the row PERSISTED, not merely that
# it existed in the writer's session.
$verify = Invoke-Engine @("SELECT 1", "USE $TableName", "COUNT")
if ($verify -notmatch "Opened $TableName .*Record count [1-9]") {
    Write-Host "SETUP FAILED: fixture table has no persisted records." -ForegroundColor Red
    Write-Host "  Without a record, LOCK has no current row and T5 cannot run." -ForegroundColor Red
    Write-Host "  ---- populate output ----" -ForegroundColor DarkYellow
    foreach ($line in ($setup -split "`r?`n")) {
        if ($line -match '^\s*$' -or $line -match '^WARNING:') { continue }
        Write-Host ("  | " + $line) -ForegroundColor DarkYellow
    }
    Write-Host "  ---- verify output ----" -ForegroundColor DarkYellow
    foreach ($line in ($verify -split "`r?`n")) {
        if ($line -match '^\s*$' -or $line -match '^WARNING:') { continue }
        Write-Host ("  | " + $line) -ForegroundColor DarkYellow
    }
    exit 1
}
Remove-Locks

# --- T1: the owner pid round-trips byte-identical ----------------------------
# The direct regression guard for AIF-116. Under a grouping locale the engine
# wrote pid=16,984 and read it back as 16.
Write-Host ""
Write-Host "T1  owner pid round-trips with no digit grouping"
$null = Invoke-Engine @("SELECT 1", "USE $TableName", "LOCK TABLE")

if (Test-Path $LockFile) {
    $text = Get-Content $LockFile -Raw
    $pidLine = ($text -split "`n" | Where-Object { $_ -like "pid=*" }) -join ""
    $pidVal  = ($pidLine -replace "^pid=", "").Trim()

    Test-Result "sidecar written" $true
    Test-Result "pid has no thousands separator" (-not $pidVal.Contains(",")) "pid line was: '$pidLine'"
    Test-Result "pid parses whole as an integer" ($pidVal -match '^\d+$') "pid value was: '$pidVal'"

    $ownerLine = ($text -split "`n" | Where-Object { $_ -like "owner=*" }) -join ""
    Test-Result "owner string has no separators" (-not $ownerLine.Contains(",")) "owner line was: '$ownerLine'"
} else {
    Test-Result "sidecar written" $false "no $LockFile after LOCK TABLE"
}

# --- T2: a provably dead owner IS reclaimed ----------------------------------
# The fix must not become a liveness bug. T1's engine has exited, so the
# sidecar it left names a dead pid.
Write-Host ""
Write-Host "T2  stale lock from a dead owner is reclaimed"
$out2 = Invoke-Engine @("SELECT 1", "USE $TableName", "LOCK TABLE", "LOCK STATUS")
Test-Result "dead-owner lock reclaimed" ($out2 -match "LOCK: table locked\.") "expected acquisition to succeed; output did not contain 'LOCK: table locked.'"

# --- T3: a LIVE foreign owner is refused -------------------------------------
# The core mutual-exclusion property. Uses this PowerShell process's own pid,
# which is alive by construction.
Write-Host ""
Write-Host "T3  live foreign owner is refused"
Remove-Locks
Write-Sidecar -Path $LockFile -PidText "$PID"
$out3 = Invoke-Engine @("SELECT 1", "USE $TableName", "LOCK TABLE")
Test-Result "live-owner lock refused" ($out3 -match "LOCK: failed") "expected refusal; a second acquire succeeded while pid $PID holds the table"

$after3 = if (Test-Path $LockFile) { Get-Content $LockFile -Raw } else { "" }
Test-Result "foreign sidecar left intact" ($after3 -match "pid=$PID") "the refused acquire must not overwrite or remove the holder's sidecar"

# --- T4: an UNPARSEABLE owner fails CLOSED -----------------------------------
# The old reader accepted the longest valid prefix, so pid=1,234 became 1,
# is_pid_alive(1) was false, and the lock was stolen. Now an owner that cannot
# be verified must be presumed ALIVE.
Write-Host ""
Write-Host "T4  malformed owner pid fails closed (presumed alive)"
Remove-Locks
Write-Sidecar -Path $LockFile -PidText "1,234"
$out4 = Invoke-Engine @("SELECT 1", "USE $TableName", "LOCK TABLE")
Test-Result "malformed-owner lock refused" ($out4 -match "LOCK: failed") "expected refusal; an unreadable owner must be presumed alive, not assumed dead"

# --- T5: record locks obey the same rules ------------------------------------
Write-Host ""
Write-Host "T5  record lock respects a live foreign TABLE lock"
Remove-Locks
Write-Sidecar -Path $LockFile -PidText "$PID"
Test-Result "T5 fixture: table sidecar exists before the attempt" (Test-Path $LockFile) "Write-Sidecar did not produce $LockFile"
$out5 = Invoke-Engine @("SELECT 1", "USE $TableName", "GO TOP", "LOCK STATUS", "LOCK")
Test-Result "T5 fixture: cursor is on a real record" ($out5 -notmatch "no current record") "LOCK found no current row -- the fixture is empty or GO TOP failed, so no record lock was attempted" $out5
Test-Result "engine SEES the foreign table lock" ($out5 -match "Table: LOCKED") "LOCK STATUS did not report the fabricated table lock -- the engine is not reading the sidecar this test wrote" $out5
Test-Result "record lock refused under foreign table lock" ($out5 -match "LOCK: failed|table locked") "a record lock was granted underneath a live foreign table lock" $out5

# --- teardown ----------------------------------------------------------------
Remove-Locks

Write-Host ""
Write-Host ("Passed: {0}   Failed: {1}" -f $script:Pass, $script:Fail)
if ($script:Fail -gt 0) {
    Write-Host "REGRESSION FAILED" -ForegroundColor Red
    exit 1
}
Write-Host "REGRESSION PASSED" -ForegroundColor Green
exit 0
