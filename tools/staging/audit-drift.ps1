<#
.SYNOPSIS
  Projection audit gate: verifies main's PROMOTE.manifest projection against
  development, and flags off-projection / junk / non-publish-lane files that
  should not be tracked on main.

.DESCRIPTION
  Complements tools/staging/prepush_gate.py (which inspects the staged CHANGE
  SET). This inspects the git-tracked tree of main. Run after a staging rebuild
  and before push.

  As of 2026-09-12 PROMOTE.manifest governs the WHOLE projection, engine SOURCE
  and BUILD CONFIG included. This gate no longer has a git-managed blind spot:
  every tracked file on main is in scope. The build certification that used to
  justify the exemption is now PROMOTION_PROCESS.md section 5 step 3, a GATING
  staging build, and it runs on the tree this gate audits.

  PASS (exit 0) requires all of:
    * projection DRIFT = 0   (every manifest-matched file on main equals dev)
    * OFF-projection tracked on main = 0   (no metalevel/leftover to purge)
    * no __pycache__ / *.pyc tracked
    * no non-publish MDO lane (messaging / metadata / sandbox) tracked

  Classifications:
    projection drift  manifest-matched file differs between main and dev
    off-projection    tracked on main, not source, not on the manifest -> purge
    (no exempt class)  every tracked file on main is audited; see 2026-09-12
    GONE              projection file on main, absent in dev (e.g. staging-
                      authored CHANGELOG.md) -- non-fatal unless -StrictGone

.PARAMETER Dev        Development root (source of truth). Default D:\code\ccode
.PARAMETER Stage      Public staging root (main). Default C:\x64base
.PARAMETER Manifest   PROMOTE.manifest path. Default <Dev>\PROMOTE.manifest
.PARAMETER ReportOnly Never exit nonzero; just print the report.
.PARAMETER StrictGone Treat GONE files as a failure.

.EXAMPLE
  pwsh tools/staging/audit-drift.ps1
.EXAMPLE
  pwsh tools/staging/audit-drift.ps1 -ReportOnly
#>
[CmdletBinding()]
param(
  [string]$Dev      = 'D:\code\ccode',
  [string]$Stage    = 'C:\x64base',
  [string]$Manifest = '',
  [switch]$ReportOnly,
  [switch]$StrictGone
)

$ErrorActionPreference = 'Stop'
if (-not $Manifest) { $Manifest = Join-Path $Dev 'PROMOTE.manifest' }
if (-not (Test-Path $Dev))      { throw "Dev root not found: $Dev" }
if (-not (Test-Path $Stage))    { throw "Staging root not found: $Stage" }
if (-not (Test-Path $Manifest)) { throw "Manifest not found: $Manifest" }

# Directories excluded when enumerating the staging tree (never part of parity).
$excludeRegex = '[\\/](\.git|build[^\\/]*|\.venv[^\\/]*|lmdb|node_modules|_tmp|\.pytest_cache|\.tmp)[\\/]|\.cdx\.d[\\/]'

function Convert-GlobToRegex([string]$glob) {
  # Faithful shell-globstar semantics:
  #   **/  matches zero-or-more directory segments (so include/**/*.hpp also
  #        matches a file directly in include/) -> (?:.*/)?
  #   **   (not followed by /) matches across segments -> .*
  #   *    matches within a single path segment       -> [^/]*
  $SS = [char]0xE000   # placeholder for bare **
  $GS = [char]0xE001   # placeholder for **/
  $g = [Regex]::Escape($glob)              # escapes * . / etc.
  $g = $g -replace '\\\*\\\*/', $GS        # **/ -> optional dir segments
  $g = $g -replace '\\\*\\\*', $SS         # **  -> across segments
  $g = $g -replace '\\\*', '[^/]*'         # *   -> within a path segment
  $g = $g -replace ([Regex]::Escape($SS)), '.*'
  $g = $g -replace ([Regex]::Escape($GS)), '(?:.*/)?'
  return "^$g$"
}

# --- load manifest globs ---
$patterns = Get-Content $Manifest |
  ForEach-Object { $_.Trim() } |
  Where-Object { $_ -and -not $_.StartsWith('#') }
$rx = $patterns | ForEach-Object { [Regex]::new((Convert-GlobToRegex $_)) }

function Test-OnAllowList([string]$rel) {
  foreach ($r in $rx) { if ($r.IsMatch($rel)) { return $true } }
  return $false
}

Write-Host "Drift audit" -ForegroundColor Cyan
Write-Host "  dev      : $Dev"
Write-Host "  staging  : $Stage"
Write-Host "  manifest : $Manifest ($($patterns.Count) globs)"
Write-Host ""

$projDrift=@(); $offProjection=@(); $gone=@(); $junk=@(); $nonpub=@(); $gitManaged=0; $ok=0
$nonpubRegex = '(^|/)(messaging|metadata|sandbox)/'
$junkRegex   = '(^|/)__pycache__/|\.pyc$'
# THE EXEMPT CLASS IS GONE (2026-09-12). Engine source and build config used to
# be skipped here because they reached main by a separate git route; they now
# travel in PROMOTE.manifest like everything else, so they are audited like
# everything else. The regex that used to skip them read:
#     '^(src|include|bindings|cmake)/|(^|/)CMakeLists\.txt$|^CMakePresets\.json$|^vcpkg(-wsl)?\.json$'
# It is kept here as a comment ONLY as a record of what was exempt and when.
# A gate with a blind spot cannot report what it cannot see: this one reported
# PASS on its source lane for five weeks while main sat 71 source files behind.

# Enumerate what a `git clone` of main actually gets = git-tracked files.
$rels = & git -C $Stage ls-files
foreach ($rel in $rels) {
  $rel = $rel.Trim()
  if (-not $rel) { continue }

  if ($rel -match $junkRegex)       { $junk   += $rel; continue }
  if ($rel -match $nonpubRegex)     { $nonpub += $rel; continue }
  # (no git-managed skip: source is projection now)

  if (-not (Test-OnAllowList $rel)) { $offProjection += $rel; continue }  # off-projection -> should be purged

  # on-manifest projection file: it must match development after a rebuild
  $stagePath = Join-Path $Stage ($rel -replace '/','\')
  if (-not (Test-Path -LiteralPath $stagePath)) { continue }
  $devPath = Join-Path $Dev ($rel -replace '/','\')
  if (-not (Test-Path -LiteralPath $devPath)) { $gone += $rel; continue }
  $hs = (Get-FileHash -LiteralPath $stagePath -Algorithm SHA256).Hash
  $hd = (Get-FileHash -LiteralPath $devPath   -Algorithm SHA256).Hash
  if ($hs -eq $hd) { $ok++ } else { $projDrift += $rel }
}

function Show-Group([string]$title, [array]$items, [string]$color) {
  Write-Host ""
  Write-Host "$title : $($items.Count)" -ForegroundColor $color
  $items | Sort-Object | Select-Object -First 40 | ForEach-Object { Write-Host "    $_" }
  if ($items.Count -gt 40) { Write-Host "    ... and $($items.Count - 40) more" }
}

Write-Host ""
Write-Host "==== SUMMARY (projection audit) ====" -ForegroundColor Cyan
Write-Host "  projection files matching dev      : $ok"
Write-Host "  projection DRIFT (stale on main)   : $($projDrift.Count)   [GATE]"
Write-Host "  OFF-projection tracked on main     : $($offProjection.Count)   [GATE -> purge]"
Write-Host "  git-managed engine/build (skipped) : $gitManaged   (exempt class removed 2026-09-12; expect 0)"
Write-Host "  GONE (projection file absent in dev): $($gone.Count)"
Write-Host "  __pycache__/*.pyc                  : $($junk.Count)   [GATE]"
Write-Host "  non-publish MDO lanes on main      : $($nonpub.Count)   [GATE -> purge]"

if ($projDrift.Count)     { Show-Group "Projection DRIFT (rebuild main from manifest)" $projDrift Yellow }
if ($offProjection.Count) { Show-Group "OFF-projection on main (metalevel etc. -- git rm --cached)" $offProjection Yellow }
if ($junk.Count)          { Show-Group "Bytecode junk (gitignore + git rm --cached)" $junk Red }
if ($nonpub.Count)        { Show-Group "Non-publish MDO lanes on main (git rm --cached)" $nonpub Red }
if ($gone.Count)          { Show-Group "GONE (confirm intentionally staging-authored)" $gone DarkGray }

$fail = ($projDrift.Count -gt 0) -or ($offProjection.Count -gt 0) -or ($junk.Count -gt 0) -or ($nonpub.Count -gt 0)
if ($StrictGone -and $gone.Count -gt 0) { $fail = $true }

Write-Host ""
if ($ReportOnly) {
  Write-Host "REPORT-ONLY: projection gate would $([string]($(if($fail){'FAIL'}else{'PASS'})))." -ForegroundColor Cyan
  exit 0
}
if ($fail) {
  Write-Host "PROJECTION GATE: FAIL" -ForegroundColor Red
  exit 1
} else {
  Write-Host "PROJECTION GATE: PASS" -ForegroundColor Green
  exit 0
}
