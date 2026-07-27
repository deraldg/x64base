<#
    reload_src_comments.ps1  --  Gate 1 driver for the COMMENTS lane (SRC* catalog)

    Reloads the eight canonical SRC* tables from a reharvest candidate.
    DESTRUCTIVE: drops and recreates every table in the lane.

    Supersedes the one-shot reload-src-comments-v3.ps1 at the repo root, which
    should be deleted. This one is parameterised, so the next reload does not
    need a new script.

    -------------------------------------------------------------------------
    METHOD -- deliberately NOT a new load script
    -------------------------------------------------------------------------
    dottalkpp\data\scripts\comments\SOURCE_COMMENT_RESET_RELOAD.dts is the
    STABLE_CANONICAL_SCRIPT for this operation. It carries the correct CREATE
    X64 schemas, CDX tags and BUILDLMDB for all eight tables, and resolves
    paths through slots (SETPATH DBF COMMENTS), not absolutes.

    So this driver does NOT rewrite the load. It STAGES a candidate into the
    directory that script already reads, then runs it unchanged. The proven
    path stays the proven path.

    -------------------------------------------------------------------------
    MEMBERSHIP RULE (settled 2026-07-26, member.derald)
    -------------------------------------------------------------------------
    The catalog documents the REPOSITORY, not the working tree: membership is
    `git ls-files` over {src, include, bindings}. A filesystem walk sees
    whatever happens to be lying around on one machine, and no clone can
    reproduce that.

    This was learned the hard way. The 2026-07-26 reload landed cleanly -- all
    eight tables matched their expected counts exactly -- and SRCFILE_DRIFT
    still did not clear, because the drift was baked into the candidate rather
    than caused by the load:

      * the harvester walked the filesystem over {src, include, bindings}
      * stack_audit_v1 used git ls-files over {src, include}

    Two tools answering different questions. Result: 10 PHANTOM rows (files on
    disk that were never committed) and 1 UNCOLLECTED row. All three tools now
    share one rule. Do not let them drift apart again.

    -------------------------------------------------------------------------
    NOTE ON MEMO_LINES
    -------------------------------------------------------------------------
    RESET_RELOAD imports MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv, not
    MEMO_LINES_IMPORT.csv. The v2 variant flattens multi-line memo cells to one
    physical row each, sidestepping the quoted-newline IMPORT path that
    csv::read_record() supports but that no previously loaded metadata CSV had
    ever exercised. Keep that choice.

    -------------------------------------------------------------------------
    NOTE ON INDEXES -- the .cdx mtimes are SUPPOSED to look old
    -------------------------------------------------------------------------
    The reload prints "CDX CREATE: file already exists" and "CDX ADDTAG: tag
    already exists", and afterwards every .cdx still carries its original date
    while the .dbf files are new. That is correct and is NOT stale-index drift.
    Those containers are 488-776 byte declaration shells holding tag names and
    expressions, which do not change. The actual keys live in the LMDB envs,
    and BUILDLMDB CLEAN YES rebuilds all of them, archiving the previous ones
    under lmdb\COMMENTS\backups\. Verify by size, not by timestamp.

    To inspect tags afterwards: open the table, SELECT its area, then CDX INFO.
    STRUCT reports tags only when the index is open.

    USAGE
      .\tools\fullstack_docs\reload_src_comments.ps1                 # dry run
      .\tools\fullstack_docs\reload_src_comments.ps1 -Execute
      .\tools\fullstack_docs\reload_src_comments.ps1 -Candidate <dir> -Execute
#>
param(
    [switch]$Execute,
    [string]$Candidate = "docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001\comments_reharvest\fullstack_20260726_contracts_v5_tracked\candidate_source_comment_metadata_import_v2"
)

$ErrorActionPreference = "Stop"
$Repo    = "D:\code\ccode"
$Stamp   = Get-Date -Format "yyyyMMdd-HHmmss"
$Cand    = Join-Path $Repo $Candidate
$Staging = "$Repo\dottalkpp\docs\generated\staging\source_comment_metadata_import_v1"
$Backup  = "$Repo\..\ccode.sidecar\comments_reload_backup_$Stamp"
$Reload  = "$Repo\dottalkpp\data\scripts\comments\SOURCE_COMMENT_RESET_RELOAD.dts"
$Verify  = "$Repo\dottalkpp\data\scripts\comments\SOURCE_COMMENT_READBACK_VALIDATION.dts"

Set-Location $Repo

if (-not (Test-Path $Cand)) { throw "candidate not found: $Cand" }

# Expected counts are READ FROM THE CANDIDATE'S OWN MANIFEST, never typed in.
# Hand-entered expectations are how a reload gets declared successful against
# numbers that were guessed rather than measured.
$ManifestPath = Join-Path (Split-Path $Cand -Parent) "source_comment_reharvest_manifest_v1.json"
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json

$Expect = [ordered]@{}
foreach ($p in $Manifest.candidate_files.PSObject.Properties) {
    if ($p.Name -eq "MEMO_LINES_IMPORT.csv") { continue }   # not the file RESET_RELOAD imports
    $t = $p.Name -replace '_IMPORT.*$',''
    $Expect[$t] = $p.Value.rows
}

Write-Host "=== Gate 1 reload -- COMMENTS lane ===" -ForegroundColor Cyan
Write-Host "  candidate  : $Candidate"
Write-Host "  membership : $($Manifest.membership)   roots: $($Manifest.roots -join ', ')"
Write-Host "  banners    : $($Manifest.files_with_header) / $($Manifest.files) files"
Write-Host "  staging    : $Staging"
Write-Host "  backup     : $Backup"
Write-Host ""
Write-Host "  delta vs current staging:" -ForegroundColor Cyan
foreach ($p in $Manifest.delta_counts.PSObject.Properties) {
    Write-Host ("    {0,-28} {1,6}" -f $p.Name, $p.Value)
}
Write-Host ""
Write-Host "  expected rows after reload (from the manifest):" -ForegroundColor Cyan
foreach ($k in $Expect.Keys) { Write-Host ("    {0,-12} {1,7}" -f $k, $Expect[$k]) }
Write-Host ""

if (-not $Execute) {
    Write-Host "DRY RUN. With -Execute this will:" -ForegroundColor Yellow
    Write-Host "  1. stop the DotTalkBBSD scheduled task (it shares the data root)"
    Write-Host "  2. back up dottalkpp\data\comments + indexes\COMMENTS (~22 MB)"
    Write-Host "     and the current staging CSVs, to $Backup"
    Write-Host "     NOT lmdb -- it is derived, and copying it filled the disk on 2026-07-26"
    Write-Host "  3. copy the candidate CSVs into the canonical staging directory"
    Write-Host "  4. run SOURCE_COMMENT_RESET_RELOAD.dts  (DESTRUCTIVE)"
    Write-Host "  5. run SOURCE_COMMENT_READBACK_VALIDATION.dts"
    Write-Host "  6. re-run stack_audit_v1 to confirm SRCFILE_DRIFT clears"
    Write-Host ""
    Write-Host "  Rollback: restore from $Backup and re-run RESET_RELOAD." -ForegroundColor Yellow
    exit 0
}

# --- 1. daemon ---------------------------------------------------------------
Write-Host "--- stopping DotTalkBBSD (shares dottalkpp\data)" -ForegroundColor Cyan
try { Stop-ScheduledTask -TaskName 'DotTalkBBSD' -ErrorAction Stop; Write-Host "    stopped" }
catch { Write-Host "    not running / not present -- continuing" -ForegroundColor Yellow }

# --- 2. backup ---------------------------------------------------------------
#
# BACK UP SOURCE DATA ONLY. NEVER THE LMDB ENVS.
#
# Learned 2026-07-26 by filling the disk. The original version of this script
# also copied dottalkpp\data\lmdb\COMMENTS "to be safe". Three things were
# wrong with that:
#
#   1. LMDB envs are DERIVED. BUILDLMDB CLEAN YES rebuilds every one of them
#      from the table in seconds -- and step 4 below does exactly that. Backing
#      up an artifact that the next step regenerates protects nothing.
#   2. Each env file is 1 GiB fully allocated. Eight tables = ~8 GB per copy,
#      against 22 MB of actual source data.
#   3. Worst: BUILDLMDB CLEAN ARCHIVES the previous envdir into
#      lmdb\COMMENTS\backups\ instead of deleting it, so that directory had
#      grown to 39 GB across 80 archives. Copy-Item -Recurse copied the
#      archive pile too, and each reload would have copied an ever-larger one.
#      Compounding backup of regenerable data. The disk filled mid-copy.
#
# Rollback is: restore these two directories, then re-run the reload (or open
# each table, SELECT its area, BUILDLMDB CLEAN YES) to rebuild the indexes.
#
Write-Host "--- backing up (source data only -- LMDB is derived, see comment)" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
foreach ($p in @("dottalkpp\data\comments",
                 "dottalkpp\data\indexes\COMMENTS")) {
    if (Test-Path "$Repo\$p") {
        $dst = Join-Path $Backup ($p -replace '[\\/]','_')
        Copy-Item "$Repo\$p" $dst -Recurse -Force
        $mb = [math]::Round((Get-ChildItem $dst -Recurse -File | Measure-Object Length -Sum).Sum / 1MB, 1)
        Write-Host ("    {0,-38} {1,8} MB" -f $p, $mb)
    }
}
Copy-Item $Staging (Join-Path $Backup "staging_csv_previous") -Recurse -Force
Write-Host "    staging CSVs (previous)"

# Guard the guard: if this backup is ever more than a few hundred MB, something
# regenerable has crept back into the list. Fail loudly rather than fill a disk.
$backupMb = [math]::Round((Get-ChildItem $Backup -Recurse -File | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host "    backup total: $backupMb MB"
if ($backupMb -gt 500) {
    throw "backup is $backupMb MB -- expected well under 500. Something derived is being copied. Aborting before the destructive step."
}

# --- 3. stage the candidate --------------------------------------------------
Write-Host "--- staging candidate" -ForegroundColor Cyan
Get-ChildItem "$Cand\*.csv" | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $Staging $_.Name) -Force
    Write-Host ("    {0,-46} {1,9:N0} bytes" -f $_.Name, $_.Length)
}

# --- 4. reload ---------------------------------------------------------------
Write-Host "--- RESET RELOAD (destructive)" -ForegroundColor Yellow
& "$Repo\datarun.ps1" -CommandLines "DOTSCRIPT $Reload" | Tee-Object "$Repo\tmp\reload_src_$Stamp.txt"

# --- 5. readback -------------------------------------------------------------
Write-Host "--- readback validation" -ForegroundColor Cyan
& "$Repo\datarun.ps1" -CommandLines "DOTSCRIPT $Verify" | Tee-Object "$Repo\tmp\reload_verify_$Stamp.txt"

# --- 6. verify the readback counts against the manifest ----------------------
# The readback prints "Recs: N" per table. Check them instead of eyeballing.
Write-Host "--- count check (readback vs manifest)" -ForegroundColor Cyan
$verifyText = Get-Content "$Repo\tmp\reload_verify_$Stamp.txt" -Raw
$bad = 0
foreach ($k in $Expect.Keys) {
    $m = [regex]::Match($verifyText, "$k\.dbf\s+Recs:\s+(\d+)")
    if (-not $m.Success) {
        Write-Host ("    {0,-12} NOT FOUND in readback" -f $k) -ForegroundColor Red; $bad++
    } elseif ([int]$m.Groups[1].Value -ne $Expect[$k]) {
        Write-Host ("    {0,-12} {1,7} != expected {2,7}  MISMATCH" -f $k, $m.Groups[1].Value, $Expect[$k]) -ForegroundColor Red; $bad++
    } else {
        Write-Host ("    {0,-12} {1,7}  OK" -f $k, $Expect[$k]) -ForegroundColor Green
    }
}
if ($bad -gt 0) { Write-Host "COUNT CHECK FAILED ($bad table(s)). Do NOT promote." -ForegroundColor Red }

# --- 7. drift re-check -------------------------------------------------------
Write-Host "--- stack audit (SRCFILE_DRIFT should clear)" -ForegroundColor Cyan
python "$Repo\tools\fullstack_docs\stack_audit_v1.py" --root $Repo

Write-Host ""
Write-Host "Transcripts: tmp\reload_src_$Stamp.txt , tmp\reload_verify_$Stamp.txt" -ForegroundColor Green
Write-Host "Backup:      $Backup" -ForegroundColor Green
Write-Host ""
Write-Host "AFTER THIS: Gates 2/3/4 must be re-run -- their prior PASS used the older catalog." -ForegroundColor Yellow
