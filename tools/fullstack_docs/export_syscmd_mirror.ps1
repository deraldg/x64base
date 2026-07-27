<#
    export_syscmd_mirror.ps1

    Refresh the tracked SYSCMD CSV FROM the live table, then verify before
    promoting. Clears stack_audit's CSV_VS_TABLE/STALE_CSV for the SYSCMD lane.

    DIRECTION MATTERS. The table is authority; the CSV is its readable shadow.
    Measured 2026-07-26: SYSCMD_IMPORT_v2.csv (216 rows) is NOT a superset of
    the live 203 -- importing it would add 28 rows and silently drop 15
    deliberate maintainer entries (BUILDLMDB, SETPATH, PREDHELP, WHERECACHE,
    STUDENTECHO, STUDENTHELLO and the nine SET compounds). This script only
    ever moves data table -> CSV.

    The 28 rows v2 would add are a SEED GAP for separate review. Nothing here
    applies them.

    USAGE
      .\tools\fullstack_docs\export_syscmd_mirror.ps1              # dry run
      .\tools\fullstack_docs\export_syscmd_mirror.ps1 -Execute     # promote
#>
param(
    [switch]$Execute,
    # Names present in the tracked CSV but ABSENT from the live table. Each must
    # be named explicitly to promote -- never a blanket override. See the
    # CSV-ONLY PHANTOMS note below.
    [string[]]$AcceptCsvOnly = @()
)

$ErrorActionPreference = "Stop"
$Repo    = "D:\code\ccode"
$Stamp   = Get-Date -Format "yyyyMMdd-HHmmss"
$Dts     = "$Repo\dottalkpp\data\scripts\metadata\SYSCMD_EXPORT_MIRROR_v1.dts"
$Out     = "$Repo\dottalkpp\data\tmp\SYSCMD_EXPORT_MIRROR_v1.csv"
$Tracked = "$Repo\dottalkpp\data\scripts\metadata\SYSCMD_IMPORT_v1.csv"
$Dbf     = "$Repo\dottalkpp\data\metadata\SYSCMD.dbf"

Set-Location $Repo

# Expected row count is READ FROM THE DBF HEADER, never typed in.
$fs = [System.IO.File]::OpenRead($Dbf)
$hb = New-Object byte[] 12
[void]$fs.Read($hb, 0, 12)
$fs.Close()
$ExpectRecs = [BitConverter]::ToUInt32($hb, 4)

Write-Host "=== SYSCMD export mirror ===" -ForegroundColor Cyan
Write-Host "  direction : LIVE TABLE -> CSV   (never the reverse)"
Write-Host "  table     : dottalkpp\data\metadata\SYSCMD.dbf   $ExpectRecs records"
Write-Host "  tracked   : dottalkpp\data\scripts\metadata\SYSCMD_IMPORT_v1.csv"
Write-Host ""

if (Test-Path $Out) { Remove-Item $Out -Force }

Write-Host "--- running EXPORT" -ForegroundColor Cyan
& "$Repo\datarun.ps1" -CommandLines "DOTSCRIPT $Dts" | Tee-Object "$Repo\tmp\syscmd_export_$Stamp.txt"

if (-not (Test-Path $Out)) {
    throw "EXPORT produced no file at $Out -- check the transcript, do not promote."
}

# --- verify ------------------------------------------------------------------
Write-Host ""
Write-Host "--- verifying the export against the table" -ForegroundColor Cyan
$new = Import-Csv $Out
$old = Import-Csv $Tracked

$newCols = ($new[0].PSObject.Properties.Name) -join ','
$oldCols = ($old[0].PSObject.Properties.Name) -join ','

$bad = 0
if ($new.Count -ne $ExpectRecs) {
    Write-Host "    rows    $($new.Count) != $ExpectRecs from the DBF header   MISMATCH" -ForegroundColor Red; $bad++
} else {
    Write-Host "    rows    $($new.Count)  OK (matches DBF header)" -ForegroundColor Green
}
if ($newCols -ne $oldCols) {
    Write-Host "    columns CHANGED" -ForegroundColor Yellow
    Write-Host "      was: $oldCols"
    Write-Host "      now: $newCols"
} else {
    Write-Host "    columns $newCols  OK" -ForegroundColor Green
}

# --- CSV-ONLY PHANTOMS -------------------------------------------------------
#
# The export CANNOT lose rows: it emits exactly what the table holds, and the
# row-count check above already proves that against the DBF header. So a name
# in the tracked CSV but absent from the table is NOT export data loss. It means
# the CSV asserts a command the canonical table does not have.
#
# That still must not promote silently, because the two possibilities are very
# different:
#   (a) the table is missing a real command  -> a SEED GAP; fix the table first
#   (b) the CSV invented one                 -> a PHANTOM; dropping it is correct
#
# Only a human can tell those apart, so each name must be acknowledged BY NAME
# via -AcceptCsvOnly. Never add a blanket override.
#
# ADJUDICATED 2026-07-26 -- LOAD is case (b), a phantom:
#   the CSV row claims HANDLER cmd_LOAD; no such function exists in the tree,
#   there is no src/cli/cmd_load.*, and dotref.hpp does not list it. LOAD exists
#   only as a SUBCOMMAND (BETA LOAD, REL LOAD, USER LOAD, CODASYL LOAD,
#   ERSATZ LOAD) and as a reserved word. A seed generator promoted a subcommand
#   token to a top-level command and invented a handler name to go with it; the
#   error propagated into both SYSCMD_IMPORT_v1.csv and _v2.csv. The live table
#   is correct to lack it.
#
$oldNames = $old   | ForEach-Object { $_.CAN_NAME.Trim().ToUpper() }
$newNames = $new   | ForEach-Object { $_.CAN_NAME.Trim().ToUpper() }
$csvOnly  = $oldNames | Where-Object { $newNames -notcontains $_ }
$gained   = $newNames | Where-Object { $oldNames -notcontains $_ }
$accepted = $AcceptCsvOnly | ForEach-Object { $_.Trim().ToUpper() }

Write-Host ""
Write-Host "    gained vs tracked CSV: $($gained.Count)  (rows the table has and the CSV lacked)"
if ($gained.Count) { Write-Host ("      " + (($gained | Sort-Object) -join ', ')) }

$unack = $csvOnly | Where-Object { $accepted -notcontains $_ }
Write-Host "    CSV-only names       : $($csvOnly.Count)  (asserted by the CSV, absent from the table)"
foreach ($n in ($csvOnly | Sort-Object)) {
    if ($accepted -contains $n) {
        Write-Host "      $n  -- acknowledged, will be dropped" -ForegroundColor Yellow
    } else {
        Write-Host "      $n  -- UNACKNOWLEDGED" -ForegroundColor Red
    }
}
if ($unack.Count) {
    Write-Host ""
    Write-Host "    Adjudicate each name, then re-run with:" -ForegroundColor Red
    Write-Host ("      -AcceptCsvOnly " + (($unack | Sort-Object) -join ',')) -ForegroundColor Red
    Write-Host "    Is it a SEED GAP (fix the table) or a PHANTOM (drop it)?" -ForegroundColor Red
    $bad++
}

# Logical-field encoding note, measured 2026-07-26: the DBF stores 'T' and
# EXPORT emits lowercase 't'. Both round-trip through IMPORT, but the bytes are
# not identical, so a naive diff of old vs new CSV shows every row as changed.
$actives = ($new | ForEach-Object { $_.ACTIVE } | Sort-Object -Unique) -join ','
Write-Host ""
Write-Host "    ACTIVE encoding      : '$actives'  (DBF holds 'T'; EXPORT emits lowercase -- known asymmetry)"

if ($bad -gt 0) { throw "VERIFICATION FAILED ($bad check(s)). Not promoting." }

Write-Host ""
Write-Host "Verification PASSED." -ForegroundColor Green

if (-not $Execute) {
    Write-Host ""
    Write-Host "DRY RUN. Re-run with -Execute to promote over the tracked CSV." -ForegroundColor Yellow
    Write-Host "  exported: $Out"
    exit 0
}

Copy-Item $Tracked "$Repo\..\ccode.sidecar\SYSCMD_IMPORT_v1.csv.$Stamp.bak" -Force
Copy-Item $Out $Tracked -Force
Write-Host "Promoted -> $Tracked" -ForegroundColor Green

Write-Host ""
Write-Host "--- stack audit (CSV_VS_TABLE/STALE_CSV for SYSCMD should clear)" -ForegroundColor Cyan
python "$Repo\tools\fullstack_docs\stack_audit_v1.py" --root $Repo
