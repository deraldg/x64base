<#
.SYNOPSIS
    Build the DotTalk++ demo databases from the My Community College archive.

.DESCRIPTION
    THIS IS THE RELEASED ENTRY POINT for step 5 of setup:

        1. download the program
        2. read the instructions
        3. build the system
        4. build the runtime
        5. run the databuild / indexing scripts   <- THIS SCRIPT

    It creates the sample databases every HELP file, lesson and lab depends on.

    ############################################################
    #  THIS SCRIPT CREATES AND OVERWRITES DATABASES.           #
    #                                                          #
    #  If the demo databases already exist, they ARE REPLACED  #
    #  with fresh copies built from the original archive.      #
    #  ANY CHANGES YOU MADE TO THEM WILL BE LOST.              #
    ############################################################

    It shows you exactly what exists and what will be destroyed, then asks
    before touching anything. Nothing happens until you type YES.

    WHAT IT BUILDS
        MyCommunityCollege.zip   (dBase III / MS-DOS -- the only original)
            -> data\dbf\og       untouched originals
            -> data\dbf\x32      + data\indexes\x32\*.cnx
            -> data\dbf\vfp      + data\indexes\vfp\*.cnx
            -> data\dbf\x64      + data\indexes\x64\*.cdx
                                 + data\lmdb\x64\*.cdx.d   (x64 only)

    WHAT IT NEVER TOUCHES
        - MyCommunityCollege.zip        the archive itself
        - non-MCC tables in those directories
        - every other lane: sandbox, help, memo, cobol, dev, metadata

.PARAMETER Yes
    Skip the confirmation prompt. For automation only. If you are a person
    reading this, you do not want this flag.

.PARAMETER WhatIf
    Show what would be destroyed and built, then stop. Changes nothing.

.EXAMPLE
    .\build_mcc_demo_bases.ps1
    # warns, shows what it will overwrite, asks, then builds

.EXAMPLE
    .\build_mcc_demo_bases.ps1 -WhatIf
    # shows the plan and stops
#>

[CmdletBinding()]
param(
    [string] $Root = "D:\code\ccode",
    [switch] $Yes,
    [switch] $WhatIf
)

$ErrorActionPreference = "Stop"

$root    = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
$dtp     = Join-Path $root "dottalkpp"
$data    = Join-Path $dtp  "data"
$here    = Split-Path -Parent $MyInvocation.MyCommand.Path

$mcc = @('BUILDING','CLASSES','COURSES','DEPT','ENROLL','MAJORS',
         'ROOMS','STUDENTS','STUD_MAJ','TASSIGN','TEACHERS','TERMS')

# ---------------------------------------------------------------------------
# Survey: what already exists that we are about to replace?
# ---------------------------------------------------------------------------
$existing = New-Object System.Collections.ArrayList
$totalBytes = 0

foreach ($lane in 'x32','vfp','x64') {
    $dbfDir = Join-Path $data "dbf\$lane"
    $idxDir = Join-Path $data "indexes\$lane"

    $tables = @()
    if (Test-Path -LiteralPath $dbfDir) {
        $tables = @(Get-ChildItem -LiteralPath $dbfDir -File -EA SilentlyContinue |
                    Where-Object { $mcc -contains $_.BaseName.ToUpper() })
    }
    $idx = @()
    if (Test-Path -LiteralPath $idxDir) {
        $idx = @(Get-ChildItem -LiteralPath $idxDir -File -EA SilentlyContinue |
                 Where-Object { $mcc -contains $_.BaseName.ToUpper() -and
                                $_.Extension -imatch '\.(cnx|cdx|inx|idx|meta)$' })
    }

    if ($tables.Count -or $idx.Count) {
        $b = (($tables + $idx) | Measure-Object Length -Sum).Sum
        $totalBytes += $b
        [void]$existing.Add([pscustomobject]@{
            Lane    = $lane
            Tables  = $tables.Count
            Indexes = $idx.Count
            Newest  = (($tables + $idx) | Sort-Object LastWriteTime -Desc |
                        Select-Object -First 1).LastWriteTime
            MB      = [math]::Round($b / 1MB, 2)
        })
    }
}

$lmdb64 = Join-Path $data "lmdb\x64"
$lmdbEnvs = @()
if (Test-Path -LiteralPath $lmdb64) {
    $lmdbEnvs = @(Get-ChildItem -LiteralPath $lmdb64 -Directory -EA SilentlyContinue |
                  Where-Object { $_.Name -imatch '\.cdx\.d$' })
}

# ---------------------------------------------------------------------------
# The warning
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Yellow
Write-Host "   DotTalk++ -- BUILD DEMO DATABASES" -ForegroundColor Yellow
Write-Host "  ============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "  This script CREATES DATABASES." -ForegroundColor White
Write-Host ""

if ($existing.Count -eq 0 -and $lmdbEnvs.Count -eq 0) {
    Write-Host "  No demo databases found. This is a first build." -ForegroundColor Green
    Write-Host "  Nothing will be overwritten."
    Write-Host ""
} else {
    Write-Host "  *** DEMO DATABASES ALREADY EXIST ***" -ForegroundColor Red
    Write-Host ""
    Write-Host "  They WILL BE OVERWRITTEN with fresh copies built from the" -ForegroundColor Red
    Write-Host "  original MyCommunityCollege archive." -ForegroundColor Red
    Write-Host ""
    Write-Host "  ANY CHANGES YOU HAVE MADE TO THIS DATA WILL BE LOST." -ForegroundColor Red
    Write-Host "  Records you added, edited or deleted. Index tags you created." -ForegroundColor Red
    Write-Host "  All of it. There is no undo." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Found:" -ForegroundColor White

    $existing | Format-Table `
        @{L='Lane';        E={$_.Lane}},
        @{L='Tables';      E={$_.Tables}},
        @{L='Indexes';     E={$_.Indexes}},
        @{L='Size (MB)';   E={$_.MB}},
        @{L='Last changed';E={$_.Newest}} -AutoSize | Out-String | Write-Host

    if ($lmdbEnvs.Count) {
        Write-Host "    plus $($lmdbEnvs.Count) LMDB environment(s) under data\lmdb\x64"
        Write-Host "    (derived -- these are always rebuilt, never authored)"
        Write-Host ""
    }
}

Write-Host "  WILL BE REBUILT:" -ForegroundColor White
Write-Host "    data\dbf\x32   + data\indexes\x32   (MS-DOS  + CNX)"
Write-Host "    data\dbf\vfp   + data\indexes\vfp   (VFP     + CNX)"
Write-Host "    data\dbf\x64   + data\indexes\x64   (x64     + CDX)"
Write-Host "    data\lmdb\x64                       (LMDB, x64 only)"
Write-Host ""
Write-Host "  WILL NOT BE TOUCHED:" -ForegroundColor Green
Write-Host "    MyCommunityCollege.zip     the original archive"
Write-Host "    data\dbf\og                the extracted originals"
Write-Host "    any table that is not part of the MCC sample set"
Write-Host "    every other lane: sandbox, help, memo, cobol, dev, metadata"
Write-Host ""

# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
if ($WhatIf) {
    Write-Host "  -WhatIf: nothing was changed." -ForegroundColor Cyan
    Write-Host ""
    return
}

if (-not $Yes) {
    Write-Host "  ------------------------------------------------------------" -ForegroundColor Yellow
    if ($existing.Count -gt 0) {
        Write-Host "  Type YES to overwrite the demo databases." -ForegroundColor Yellow
    } else {
        Write-Host "  Type YES to build the demo databases." -ForegroundColor Yellow
    }
    Write-Host "  Anything else aborts. Nothing has been changed yet." -ForegroundColor Yellow
    Write-Host "  ------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host ""
    $answer = Read-Host "  Continue? (YES / no)"

    if ($answer -cne 'YES') {
        Write-Host ""
        Write-Host "  ABORTED. Nothing was changed." -ForegroundColor Cyan
        Write-Host "  (The confirmation is case-sensitive: type YES in capitals.)"
        Write-Host ""
        return
    }
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
Write-Host "  [1/3] Resetting to a virgin slate..." -ForegroundColor Cyan
& (Join-Path $here "reset_mcc_fixtures.ps1") -Root $root -Execute
Write-Host ""

Write-Host "  [2/3] Extracting the canonical archive..." -ForegroundColor Cyan
& (Join-Path $here "extract_mcc_og.ps1") -Root $root -Force
Write-Host ""

Write-Host "  [3/3] Building the databases and indexes..." -ForegroundColor Cyan
Write-Host ""

$stages = @(
    'DOTSCRIPT TRACE scripts\mcc\mcc_build_x32.dts OUT tmp\mcc_x32.log'
    'DOTSCRIPT TRACE scripts\mcc\mcc_build_vfp.dts OUT tmp\mcc_vfp.log'
    'DOTSCRIPT TRACE scripts\mcc\mcc_build_x64.dts OUT tmp\mcc_x64.log'
    'DOTSCRIPT TRACE scripts\mcc\mcc_demo.dts      OUT tmp\mcc_demo.log'
    'QUIT'
)

$datarun = Join-Path $root "datarun.ps1"
$driven  = $false

if (Test-Path -LiteralPath $datarun) {
    try {
        & $datarun -CommandLines $stages
        $driven = $true
    } catch {
        Write-Warning "Could not drive datarun.ps1 automatically: $($_.Exception.Message)"
    }
}

if (-not $driven) {
    Write-Host "  Run the build stages by hand. Start the runtime:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "      .\datarun.ps1"
    Write-Host ""
    Write-Host "  then, in order -- each stage feeds the next:"
    Write-Host ""
    foreach ($s in $stages | Where-Object { $_ -ne 'QUIT' }) {
        Write-Host "      $s"
    }
    Write-Host ""
    return
}

# ---------------------------------------------------------------------------
# Closeout
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host "   DEMO DATABASES BUILT" -ForegroundColor Green
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  A zero exit code is NOT proof. The DotScript runner reports"
Write-Host "  unknown commands and CONTINUES. Read the transcripts:"
Write-Host ""
Write-Host "      data\tmp\mcc_x32.log"
Write-Host "      data\tmp\mcc_vfp.log"
Write-Host "      data\tmp\mcc_x64.log"
Write-Host "      data\tmp\mcc_demo.log"
Write-Host ""
Write-Host "  Each build stage ends with a FRESHNESS ASSERTION. Confirm it:"
Write-Host ""
Write-Host "      STUDENTS must report exactly 200 records"
Write-Host "      record 1 under TAG SID must read:  50000000  Taylor  Quinn"
Write-Host ""
Write-Host "  and that every CNX CREATE / CDX CREATE reported 'created:'"
Write-Host "  rather than 'file already exists'."
Write-Host ""
Write-Host "  Then try it:"
Write-Host ""
Write-Host "      .\datarun.ps1"
Write-Host "      USE STUDENTS"
Write-Host "      SET INDEX TO STUDENTS"
Write-Host "      SET ORDER TO TAG LNAME"
Write-Host "      SMARTLIST 10"
Write-Host ""
