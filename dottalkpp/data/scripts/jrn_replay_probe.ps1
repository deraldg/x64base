# Journal replay probe harness.
#
# Measures site 3 of the recno-reservation family -- table_state.cpp:1015, the
# crash-recovery replay -- WITHOUT needing a crash. Part 1 builds tables of known
# size and closes them; this script then hand-writes a .tbj beside each carrying a
# deliberately stale recno; part 2 opens them, which is what fires
# recover_table_buffer_journal (table_state.cpp:798).
#
# The journal format is specified in that same file:
#   header   TBJ<version> <name>
#   record   I <recno> <priority> <H|S> <field>:<hex> [<field>:<hex> ...]
#   marker   C <count>
# The reader validates the version (journal_header_version) and the record tags
# (journal_record_is_known) and NOTHING about the recnos. A C marker sets
# has_commit, which short-circuits the group decision lookup.
#
# Fields: 1 = ID C(4), 2 = TAG C(12).
#   "J1"=4A31  "J2"=4A32  "J3"=4A33
#   "REPLAYED"=5245504C41594544   "BLENDED"=424C454E444544

$ErrorActionPreference = "Stop"

# DERIVED, NEVER HARDCODED. This file lives at <repo>/dottalkpp/data/scripts/,
# so the repo root is three levels up. A literal "D:\code\ccode" here would be
# one more machine-absolute path in a tree that already carries 71 of them
# (OI-017), and it would be wrong in every clone but one.
$repo    = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$sandbox = Join-Path $repo "dottalkpp\data\DBF\SANDBOX"
Write-Host ("repo root: {0}" -f $repo) -ForegroundColor DarkGray

Write-Host "=============== PART 1: build the fixtures ===============" -ForegroundColor Cyan
& (Join-Path $repo "datarun.ps1") -AppArgs '--script','scripts\journal_replay_probe_part1.dts'

Write-Host ""
Write-Host "=============== writing the hand-made journals ===============" -ForegroundColor Cyan

$logs = @{
    # CONTROL: 2 records on disk, recno 3 IS the true next -- must append cleanly.
    "JRN1" = "TBJ1 JRN1`nI 3 1 S 1:4A31 2:5245504C41594544`nC 1`n"
    # STALE, IN BOUNDS: 4 records on disk, recno 3 is a live row.
    "JRN2" = "TBJ1 JRN2`nI 3 1 S 1:4A32 2:5245504C41594544`nC 1`n"
    # STALE, OUT OF BOUNDS: 1 record on disk, recno 3 is past the end.
    "JRN3" = "TBJ1 JRN3`nI 3 1 S 1:4A33 2:5245504C41594544`nC 1`n"
    # THE BLEND: 4 records on disk, recno 3 is live, and the record sets ONLY field 2.
    "JRN4" = "TBJ1 JRN4`nI 3 1 S 2:424C454E444544`nC 1`n"
}

foreach ($name in ($logs.Keys | Sort-Object)) {
    $dbf = Join-Path $sandbox "$name.dbf"
    if (-not (Test-Path -LiteralPath $dbf)) {
        Write-Warning "$dbf does not exist -- part 1 did not build it. Skipping."
        continue
    }
    $tbj = "$dbf.tbj"
    # LF endings on purpose; the reader strips CR, but the format is LF.
    [System.IO.File]::WriteAllText($tbj, $logs[$name], [System.Text.Encoding]::ASCII)
    $sz = (Get-Item -LiteralPath $tbj).Length
    Write-Host ("  wrote {0}  ({1} bytes)" -f $tbj, $sz)
}

Write-Host ""
Write-Host "  DBF sizes going in:" -ForegroundColor DarkGray
Get-ChildItem -LiteralPath $sandbox -Filter "JRN*.dbf" |
    ForEach-Object { Write-Host ("    {0,-14} {1,8} bytes" -f $_.Name, $_.Length) }

Write-Host ""
Write-Host "=============== PART 2: open, and watch recovery run ===============" -ForegroundColor Cyan
& (Join-Path $repo "datarun.ps1") -AppArgs '--script','scripts\journal_replay_probe_part2.dts'

Write-Host ""
Write-Host "=============== did the logs survive? ===============" -ForegroundColor Cyan
Write-Host "A DELETED log means recovery called itself done. Site 3 removes the log"
Write-Host "after the loop with no count of applied-vs-skipped records, so a replay"
Write-Host "that dropped everything looks exactly like one that applied everything."
$left = @(Get-ChildItem -LiteralPath $sandbox -Filter "JRN*.tbj" -ErrorAction SilentlyContinue)
if ($left.Count -eq 0) {
    Write-Host "  ALL FOUR LOGS GONE." -ForegroundColor Yellow
} else {
    $left | ForEach-Object { Write-Host ("  KEPT: {0}  ({1} bytes)" -f $_.Name, $_.Length) }
}
