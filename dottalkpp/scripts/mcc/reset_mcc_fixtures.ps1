<#
.SYNOPSIS
    Reset the MCC sample data to a virgin state, ready for a clean databuild.

.DESCRIPTION
    This is the "clean slate" step before the DotScript databuild chain.

        MyCommunityCollege.zip  (dBase III / MS-DOS -- the only true original)
                |
                v
          data\dbf\og      untouched originals
                |
                +--> data\dbf\x32   (AS MSDOS)  + data\indexes\x32\*.cnx
                        |
                        +--> data\dbf\vfp   (AS VFP)  + data\indexes\vfp\*.cnx
                                |
                                +--> data\dbf\x64  (AS X64 VECTOR)
                                       + data\indexes\x64\*.cdx
                                       + data\lmdb\x64\*.cdx.d   (x64 only)

    WHY THE INDEXES MUST GO TOO
    ---------------------------
    CNX CREATE and CDX CREATE refuse to overwrite an existing container. If the
    old containers survive, a "rebuild" silently becomes a REINDEX of whatever
    tags were already there -- and any tag the build script declares is never
    actually created. On 2026-07-14 that produced three green transcripts that
    had rebuilt nothing.

    Virgin means virgin. The containers go.

    ALSO REMOVES the stray dottalkpp\x32, \vfp, \x64 directories, if present.
    Those were created by an earlier bug: COPY TO ..\x32\<T> resolves relative
    to the DATA ROOT, so "..\" climbed above data\ and wrote there instead.

    WHAT IS NEVER TOUCHED
    ---------------------
    - MyCommunityCollege.zip          the canonical origin
    - data\dbf\og                     the extracted originals
    - non-MCC tables in the target dirs (TEST64.dbf, X64SAMPLE.dbf, etc.)
    - any other lane: sandbox, help, memo, cobol, dev, metadata, ...

    REPORT-ONLY by default. Deletes nothing without -Execute.

.EXAMPLE
    .\dottalkpp\scripts\mcc\reset_mcc_fixtures.ps1
    .\dottalkpp\scripts\mcc\reset_mcc_fixtures.ps1 -Execute
#>

[CmdletBinding()]
param(
    [string] $Root = "D:\code\ccode",
    [switch] $Execute
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
$dtp  = Join-Path $root "dottalkpp"
$data = Join-Path $dtp  "data"

# The 12 MCC tables. ONLY these are removed from the target dirs -- anything
# else living there (TEST64.dbf, X64SAMPLE.dbf, ...) is left alone.
$mcc = @('BUILDING','CLASSES','COURSES','DEPT','ENROLL','MAJORS',
         'ROOMS','STUDENTS','STUD_MAJ','TASSIGN','TEACHERS','TERMS')

Write-Host "Root: $root"
Write-Host "Mode: $(if ($Execute) { 'EXECUTE (destructive)' } else { 'REPORT-ONLY' })"
Write-Host ""

$targets = New-Object System.Collections.ArrayList

# --- 1. Stray directories from the ..\ path bug ------------------------------
foreach ($lane in 'x32','vfp','x64') {
    $stray = Join-Path $dtp $lane
    if (Test-Path -LiteralPath $stray) {
        $n = @(Get-ChildItem -LiteralPath $stray -File -Recurse -EA SilentlyContinue).Count
        [void]$targets.Add([pscustomobject]@{
            Kind = 'STRAY DIR (path bug)'; Path = $stray; Items = $n })
    }
}

# --- 2. MCC tables + their sidecars in the generated lanes -------------------
# og is NOT in this list. og is the source of truth.
foreach ($lane in 'x32','vfp','x64') {
    $dir = Join-Path $data "dbf\$lane"
    if (-not (Test-Path -LiteralPath $dir)) { continue }
    foreach ($t in $mcc) {
        Get-ChildItem -LiteralPath $dir -File -EA SilentlyContinue |
            Where-Object { $_.BaseName -ieq $t } |
            ForEach-Object {
                [void]$targets.Add([pscustomobject]@{
                    Kind = "DBF ($lane)"; Path = $_.FullName; Items = 1 })
            }
    }
}

# --- 3. Index containers -- these MUST go, or CREATE refuses ----------------
foreach ($lane in 'x32','vfp','x64') {
    $dir = Join-Path $data "indexes\$lane"
    if (-not (Test-Path -LiteralPath $dir)) { continue }
    foreach ($t in $mcc) {
        Get-ChildItem -LiteralPath $dir -File -EA SilentlyContinue |
            Where-Object { $_.BaseName -ieq $t -and $_.Extension -imatch '\.(cnx|cdx|inx|idx|meta)$' } |
            ForEach-Object {
                [void]$targets.Add([pscustomobject]@{
                    Kind = "INDEX ($lane)"; Path = $_.FullName; Items = 1 })
            }
    }
}

# --- 4. LMDB environments -- x64 ONLY (maintainer rule) ---------------------
$lmdb64 = Join-Path $data "lmdb\x64"
if (Test-Path -LiteralPath $lmdb64) {
    foreach ($t in $mcc) {
        Get-ChildItem -LiteralPath $lmdb64 -Directory -EA SilentlyContinue |
            Where-Object { $_.Name -ieq "$t.cdx.d" } |
            ForEach-Object {
                [void]$targets.Add([pscustomobject]@{
                    Kind = 'LMDB ENV (x64)'; Path = $_.FullName; Items = 1 })
            }
    }
    # BUILDLMDB CLEAN archives old envs here. They accumulate.
    $bak = Join-Path $lmdb64 "backups"
    if (Test-Path -LiteralPath $bak) {
        $n = @(Get-ChildItem -LiteralPath $bak -Directory -EA SilentlyContinue).Count
        if ($n -gt 0) {
            [void]$targets.Add([pscustomobject]@{
                Kind = 'LMDB BACKUPS'; Path = $bak; Items = $n })
        }
    }
}

# --- 5. Stray .cnx written to indexes\ ROOT by the earlier path bug ---------
$idxRoot = Join-Path $data "indexes"
foreach ($t in $mcc) {
    Get-ChildItem -LiteralPath $idxRoot -File -EA SilentlyContinue |
        Where-Object { $_.BaseName -ieq $t -and $_.Extension -imatch '\.(cnx|cdx)$' } |
        ForEach-Object {
            [void]$targets.Add([pscustomobject]@{
                Kind = 'STRAY INDEX (root)'; Path = $_.FullName; Items = 1 })
        }
}

# --- Report -----------------------------------------------------------------
if ($targets.Count -eq 0) {
    Write-Host "Already virgin. Nothing to reset."
    Write-Host "Next: DOTSCRIPT TRACE scripts\mcc\mcc_build_x32.dts OUT tmp\mcc_x32.log"
    return
}

$targets | Group-Object Kind | Sort-Object Name | Format-Table `
    @{L='What';E={$_.Name}},
    @{L='Count';E={$_.Count}} -AutoSize

Write-Host "PRESERVED (never touched):"
Write-Host "  data\dbf\MyCommunityCollege.zip   the canonical origin"
Write-Host "  data\dbf\og\                      the extracted originals"
Write-Host "  non-MCC tables (TEST64, X64SAMPLE, ...) in the target dirs"
Write-Host "  every other lane: sandbox, help, memo, cobol, dev, metadata"
Write-Host ""

if (-not $Execute) {
    Write-Host "REPORT-ONLY. Nothing deleted. $($targets.Count) items would be removed."
    Write-Host "Re-run with -Execute."
    return
}

$removed = 0
foreach ($t in $targets) {
    try {
        Remove-Item -LiteralPath $t.Path -Recurse -Force -ErrorAction Stop
        $removed++
    } catch {
        Write-Warning "Could not remove: $($t.Path) -- $($_.Exception.Message)"
    }
}

Write-Host "Removed $removed of $($targets.Count) items."
Write-Host ""
Write-Host "The fixtures are now virgin. Rebuild in order -- each stage feeds the next:"
Write-Host ""
Write-Host "  .\dottalkpp\scripts\mcc\extract_mcc_og.ps1        (if data\dbf\og is absent)"
Write-Host "  DOTSCRIPT TRACE scripts\mcc\mcc_build_x32.dts OUT tmp\mcc_x32.log"
Write-Host "  DOTSCRIPT TRACE scripts\mcc\mcc_build_vfp.dts OUT tmp\mcc_vfp.log"
Write-Host "  DOTSCRIPT TRACE scripts\mcc\mcc_build_x64.dts OUT tmp\mcc_x64.log"
Write-Host "  DOTSCRIPT TRACE scripts\mcc\mcc_demo.dts      OUT tmp\mcc_demo.log"
Write-Host ""
Write-Host "This time CNX CREATE / CDX CREATE will actually CREATE, because the"
Write-Host "old containers are gone. Watch for 'created:' rather than"
Write-Host "'file already exists'. That is the difference between a rebuild and"
Write-Host "a REINDEX wearing a rebuild's clothes."
