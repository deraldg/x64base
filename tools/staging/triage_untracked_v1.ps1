# triage_untracked_v1.ps1
# Classify the CURRENT untracked tree into three buckets and (optionally) age out the
# high-confidence scratch into D:\code\ccode.sidecar, preserving relative paths.
#
# House context: this generalizes move_to_sidecar_first_pass.ps1 (which moved a hand-built
# quarantine_files.txt list). Instead of a hand list, it reads the LIVE `git status` so it
# always sees the complete, current untracked set -- no stale or partial manifest.
#
# SAFETY (deliberate):
#   * DRY-RUN by default. Add -Execute to actually move.
#   * Moves ONLY the SIDECAR bucket (high-confidence scratch). Never REVIEW or UNSURE.
#   * It is a filesystem MOVE into ccode.sidecar (recoverable), never `git rm`, never delete.
#   * It never runs `git add`. Committing real work stays a human, per-path decision.
#   * REVIEW (looks like real source/docs) and UNSURE are only LISTED, never touched.
#
# Output: three manifests next to this script (SIDECAR / REVIEW / UNSURE) plus a summary.
# Recover anything by moving it back from ccode.sidecar.

param(
  [switch]$Execute,
  [string]$Repo    = 'D:\code\ccode',
  [string]$Sidecar = 'D:\code\ccode.sidecar'
)

Push-Location $Repo
try {
  # Untracked files only ('??'), complete (--untracked-files=all). NUL-safe not needed here.
  $untracked = & git status --porcelain --untracked-files=all |
               Where-Object { $_ -match '^\?\? ' } |
               ForEach-Object { ($_ -replace '^\?\? ', '').Trim('"') }

  if (-not $untracked) { Write-Host 'No untracked files. Tree is clean.'; return }

  # --- classification rules ---------------------------------------------------------
  # SIDECAR = high-confidence scratch/one-offs/dumps. Conservative: only obvious debris.
  $sidecarRules = @(
    '(^|/)[^/]*_transcript[0-9]*\.txt$',      # *_transcript.txt, keymeta_transcript2.txt
    '(^|/)rdb_truth_(report|transcript)[^/]*$',
    '(^|/)homegrown_[^/]*\.ps1$',
    '(^|/)metacollect_(compare|facts)\.csv$',
    '(^|/)sidecar_[^/]*\.txt$',               # the triage input lists themselves
    '(^|/)quarantine_files\.txt$',
    '(^|/)move_to_sidecar[^/]*\.ps1$',
    '(^|/)sort_source_by_size\.ps1$',
    '\.patch$',                                # loose patch files (not in a package dir)
    ' \([0-9]+\)\.',                           # " (1)." duplicate-copy marker
    '(^|/)package_manifest[^/]*\.json$'
  )
  # REVIEW = likely real work; LIST ONLY, never move. Bias toward keeping.
  $reviewRules = @(
    '^src/.*\.(cpp|hpp|h|py)$',
    '^tools/.*\.py$', '^dottalkpp/tools/.*\.py$',
    '(^|/)docs/.*\.md$', '^dottalkpp/docs/.*\.md$',
    '^labtalk/.*\.(md|mmd|svg|yaml)$',
    '^selfdoc/.*\.(md|json)$'
  )

  function Test-Any([string]$path, [string[]]$rules) {
    foreach ($r in $rules) { if ($path -match $r) { return $true } }
    return $false
  }

  $sidecar = @(); $review = @(); $unsure = @()
  foreach ($p in $untracked) {
    if     (Test-Any $p $sidecarRules) { $sidecar += $p }
    elseif (Test-Any $p $reviewRules)  { $review  += $p }
    else                                { $unsure  += $p }
  }

  # --- write manifests --------------------------------------------------------------
  $sidecar | Set-Content -Encoding UTF8 (Join-Path $PSScriptRoot 'triage_SIDECAR.txt')
  $review  | Set-Content -Encoding UTF8 (Join-Path $PSScriptRoot 'triage_REVIEW.txt')
  $unsure  | Set-Content -Encoding UTF8 (Join-Path $PSScriptRoot 'triage_UNSURE.txt')

  # --- move (SIDECAR bucket only, and only with -Execute) ---------------------------
  $moved = 0; $missing = 0
  foreach ($rel in $sidecar) {
    $r   = $rel -replace '/', '\'
    $src = Join-Path $Repo $r
    if (-not (Test-Path -LiteralPath $src)) { $missing++; continue }
    if ($Execute) {
      $dst = Join-Path $Sidecar $r
      New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
      Move-Item -LiteralPath $src -Destination $dst -Force
    }
    Write-Host ("{0}  {1}" -f $(if ($Execute) { 'MOVED ' } else { 'DRYRUN' }), $rel)
    $moved++
  }

  Write-Host ''
  Write-Host ("untracked total : {0}" -f $untracked.Count)
  Write-Host ("SIDECAR (scratch): {0}   -> {1}{2}" -f $sidecar.Count, $Sidecar,
              $(if ($Execute) { '  [MOVED]' } else { '  [dry-run; add -Execute]' }))
  Write-Host ("REVIEW  (keep?)  : {0}   -> triage_REVIEW.txt (commit as scoped slices; NOT moved)" -f $review.Count)
  Write-Host ("UNSURE           : {0}   -> triage_UNSURE.txt (eyeball; move or keep by hand)" -f $unsure.Count)
  Write-Host ''
  Write-Host 'Next: read triage_REVIEW.txt (real work to commit) and triage_UNSURE.txt (judgement calls).'
  Write-Host 'Recover any sidecar move by copying back from ccode.sidecar.'
}
finally { Pop-Location }
