<#
    prune_lmdb_archives.ps1  --  reclaim BUILDLMDB CLEAN archive directories

    WHY THIS EXISTS
      BUILDLMDB CLEAN YES does not delete the previous LMDB envdir -- it
      ARCHIVES it, into <lmdb-dir>\backups\<TABLE>.cdx.d_<yyyymmdd_hhmmss>.
      Each env file is 1 GiB fully allocated. Eight tables per reload, ten
      reloads, and dottalkpp\data\lmdb\COMMENTS\backups reached 39 GB with
      80 archives dating back to 2026-06-25. Across the whole lmdb tree the
      archives totalled roughly 50 GB and filled the disk on 2026-07-26.

    IS IT SAFE TO DELETE THEM?
      Yes. LMDB envs are DERIVED data -- they are rebuilt from the DBF by:
          USE <table>
          SELECT <area>
          BUILDLMDB CLEAN YES
      Nothing in an archived envdir is authoritative. The DBF is the source.

    WHAT IT DOES NOT TOUCH
      Only directories under a `backups\` folder are ever considered. The live
      <TABLE>.cdx.d envdirs beside them are never candidates.

    USAGE
      .\tools\fullstack_docs\prune_lmdb_archives.ps1                 # dry run, all lanes
      .\tools\fullstack_docs\prune_lmdb_archives.ps1 -Keep 1         # keep newest 1 per table
      .\tools\fullstack_docs\prune_lmdb_archives.ps1 -Execute
      .\tools\fullstack_docs\prune_lmdb_archives.ps1 -Lane COMMENTS -Keep 0 -Execute

    -Keep N   how many archives to retain PER TABLE PER LANE (default 1).
              0 removes every archive.
#>
param(
    [switch]$Execute,
    [int]$Keep = 1,
    [string]$Lane = "*"
)

$ErrorActionPreference = "Stop"
$LmdbRoot = "D:\code\ccode\dottalkpp\data\lmdb"

if (-not (Test-Path $LmdbRoot)) { throw "not found: $LmdbRoot" }

Write-Host "=== LMDB archive prune ===" -ForegroundColor Cyan
Write-Host "  root : $LmdbRoot"
Write-Host "  lane : $Lane      keep: $Keep per table"
Write-Host ""

$totalBytes = 0L
$totalDirs  = 0
$doomed     = @()

Get-ChildItem $LmdbRoot -Directory | Where-Object { $_.Name -like $Lane } | ForEach-Object {
    $laneName = $_.Name
    $backups  = Join-Path $_.FullName "backups"
    if (-not (Test-Path $backups)) { return }

    # Group by table name: SRCFILE.cdx.d_20260726_201241 -> SRCFILE.cdx.d
    $groups = Get-ChildItem $backups -Directory |
              Group-Object { ($_.Name -replace '_\d{8}_\d{6}$','') }

    foreach ($g in $groups) {
        $ordered = $g.Group | Sort-Object Name -Descending    # timestamp suffix sorts correctly
        $drop    = if ($Keep -gt 0) { $ordered | Select-Object -Skip $Keep } else { $ordered }
        foreach ($d in $drop) {
            $bytes = (Get-ChildItem $d.FullName -Recurse -File -ErrorAction SilentlyContinue |
                      Measure-Object Length -Sum).Sum
            if (-not $bytes) { $bytes = 0 }
            $totalBytes += $bytes
            $totalDirs++
            $doomed += [pscustomobject]@{ Lane = $laneName; Path = $d.FullName; Bytes = $bytes }
        }
    }
}

if ($totalDirs -eq 0) { Write-Host "nothing to prune." -ForegroundColor Green; exit 0 }

$doomed | Group-Object Lane | ForEach-Object {
    $gb = [math]::Round(($_.Group | Measure-Object Bytes -Sum).Sum / 1GB, 2)
    Write-Host ("  {0,-14} {1,4} archive(s)   {2,8} GB" -f $_.Name, $_.Count, $gb)
}
Write-Host ""
Write-Host ("  TOTAL: {0} directories, {1} GB" -f $totalDirs, [math]::Round($totalBytes/1GB,2)) -ForegroundColor Yellow

if (-not $Execute) {
    Write-Host ""
    Write-Host "DRY RUN. Re-run with -Execute to delete." -ForegroundColor Yellow
    Write-Host "Sample of what would go:" -ForegroundColor Yellow
    $doomed | Select-Object -First 5 | ForEach-Object { Write-Host "    $($_.Path)" }
    if ($totalDirs -gt 5) { Write-Host "    ... and $($totalDirs - 5) more" }
    exit 0
}

Write-Host ""
$n = 0
foreach ($d in $doomed) {
    Remove-Item $d.Path -Recurse -Force -ErrorAction Continue
    $n++
    if ($n % 10 -eq 0) { Write-Host "    removed $n / $totalDirs" }
}
Write-Host ""
Write-Host ("Reclaimed {0} GB across {1} directories." -f [math]::Round($totalBytes/1GB,2), $n) -ForegroundColor Green
Write-Host "Live envdirs untouched. Rebuild any index with: USE <t> / SELECT <area> / BUILDLMDB CLEAN YES"
