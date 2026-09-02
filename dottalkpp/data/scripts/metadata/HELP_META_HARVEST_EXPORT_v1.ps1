# HELP_META_HARVEST_EXPORT_v1.ps1
#
# Rebuild the manualgen HELP/META harvest for the 10 CURRENT tables, then stamp
# and hash them into a fresh, self-describing export run.
#
# LANE: MAINT (maintenance/SDLC). BBOX only TEACHES the manualgen lane; MAINT is
# the maintenance EXECUTION surface this belongs to. MAINT is read-only first
# wave and notes "PowerShell is MDO scaffolding only; the permanent maintenance
# app is native C++" -- so this .ps1 IS that scaffolding, the executable feeder
# BBOX/MAINT/MANUAL describe but that was mostly never committed.
#
# Steps:
#   1. Run HELP_META_HARVEST_EXPORT_v1.dts -> 10 CSVs under dottalkpp\data\tmp.
#   2. Promote them into harvested\export_runs\HELPMETA-<utc-stamp>\.
#   3. Carry the four stale May META_* forward, LABELLED, so manualgen sees all
#      14 required files without pretending the stale four are current.
#   4. Write a filled manifest (row counts + SHA-256), replacing the
#      PENDING_EXPORT scaffold with real EXPORTED / CARRIED_STALE evidence.
#
# Read-only w.r.t. tables/indexes/LMDB. Writes only tmp\ and the new run dir.
# No em-dashes (maintainer preference); uses -- and ->.
#
# Run from anywhere:
#   pwsh -File dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1

$ErrorActionPreference = 'Stop'

# metadata -> scripts -> data -> dottalkpp -> repo root
$repo      = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$dts       = Join-Path $PSScriptRoot 'HELP_META_HARVEST_EXPORT_v1.dts'
$datarun   = Join-Path $repo 'datarun.ps1'
$tmp       = Join-Path $repo 'dottalkpp\data\tmp'
$oldHarv   = Join-Path $repo 'docs\manuals\developer\manualgen\harvested'
$stamp     = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$run       = "HELPMETA-$stamp"
$dest      = Join-Path $oldHarv "export_runs\$run"

# table.dbf -> harvest csv name, for the 10 CURRENT surfaces
$current = @(
  'HELP_COMMANDS.csv','HELP_CMD_ARGS.csv','HELP_HELP_ARTIFACTS.csv',
  'HELP_HELP_LINE.csv','HELP_HELP_SECTION.csv','HELP_HELP_TOPIC.csv',
  'META_SYSCMD.csv','META_SYSFUNC.csv','META_SYSARGS.csv','META_SYSSUBCMD.csv'
)
# stale sources -- carried from the prior May harvest, never re-exported here
$stale = @('META_SYSENTVAR.csv','META_SYSFLDDIC.csv','META_SYSHELP.csv','META_SYSMSG.csv')

function Csv-RowCount([string]$path) {
  # COUNT CSV RECORDS, NOT LINES.
  #
  # This was `(Get-Content | Measure-Object -Line).Lines - 1`, which counts
  # PHYSICAL LINES. That is correct only while no field contains a newline.
  #
  # Measured 2026-09-02 (DOCFLUSH-20260901-002), run HELPMETA-20260902T012620Z:
  #
  #     HELP_HELP_TOPIC.csv   manifest said  1196
  #                           actual records   666   <- and the engine agrees,
  #                                                     "Exported 666 records"
  #                           physical lines  1356
  #
  # The bug APPEARED THE MOMENT THE EXPORT STARTED BEING RIGHT: memo TEXT now
  # resolves through `EXPORT ... CSV`, so quoted fields carry newlines. While
  # the interim Python exporter blanked memo, every field was single-line and
  # line-counting happened to agree with record-counting.
  #
  # Note 1196 is neither 666 nor 1356-1, so plain physical-line counting does
  # not explain it either -- Get-Content/Measure-Object line semantics (CRLF,
  # embedded CR, trailing-line handling) are involved. The exact arithmetic was
  # never established and does not need to be: Import-Csv parses the CSV
  # grammar, honours quoted embedded newlines, and treats row 1 as the header,
  # so no subtraction is required.
  $rows = @(Import-Csv -LiteralPath $path)
  return $rows.Count
}

Write-Host "HELP/META harvest export -- run $run"
Write-Host "repo: $repo"

# 1. export the 10 current tables to data\tmp
& $datarun -CommandLines "DOTSCRIPT $dts" | Out-Host

# 2 + 3. promote current, carry stale, build manifest
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$manifest = @()

foreach ($f in $current) {
  $src = Join-Path $tmp $f
  if (-not (Test-Path -LiteralPath $src)) {
    Write-Warning "MISSING export: $f -- the DotScript did not produce it"
    $manifest += [pscustomobject]@{ target_csv=$f; status='EXPORT_MISSING'; row_count=''; sha256=''; source='HELP/META current'; export_method='DOTSCRIPT+EXPORT CSV' }
    continue
  }
  Copy-Item -LiteralPath $src -Destination (Join-Path $dest $f) -Force
  $manifest += [pscustomobject]@{
    target_csv=$f; status='EXPORTED'; row_count=(Csv-RowCount $src);
    sha256=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash;
    source='HELP/META current'; export_method='DOTSCRIPT+EXPORT CSV'
  }
}

foreach ($f in $stale) {
  $src = Join-Path $oldHarv $f
  if (Test-Path -LiteralPath $src) {
    Copy-Item -LiteralPath $src -Destination (Join-Path $dest $f) -Force
    $manifest += [pscustomobject]@{
      target_csv=$f; status='CARRIED_STALE_MAY'; row_count=(Csv-RowCount $src);
      sha256=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash;
      source='stale May seed/stub'; export_method='(carried forward -- source not yet current)'
    }
  } else {
    Write-Warning "No prior CSV to carry for $f"
    $manifest += [pscustomobject]@{ target_csv=$f; status='MISSING_STALE'; row_count=''; sha256=''; source='stale May seed/stub'; export_method='(no prior export to carry)' }
  }
}

# 4. write the filled manifest
$manifestPath = Join-Path $dest 'HELP_META_EXPORT_MANIFEST_v1.csv'
$manifest | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8

Write-Host ''
Write-Host "Exported 10 current + carried 4 stale -> $dest"
Write-Host "Manifest: $manifestPath"
Write-Host ''
Write-Host "Next -- point manualgen at this run (Python 3.12):"
Write-Host "  manualgen.py --repo-root $repo --manual developer \"
Write-Host "    --publication-workspace developer_manual_publication_v1_media_section_v1 \"
Write-Host "    --harvest-workspace $dest inventory"
Write-Host "  then: validate  ->  build-dry-run  ->  build-reference-candidate  ->  parity-review"
