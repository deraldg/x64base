<#
.SYNOPSIS
  Drift-audit gate: compares the public staging tree (main) against development
  by CONTENT (SHA-256), cross-references differences against PROMOTE.manifest,
  and flags junk / non-publish lanes that must not be in the public repo.

.DESCRIPTION
  Complements tools/staging/prepush_gate.py. prepush_gate inspects the staged
  CHANGE SET; this inspects RESULTING TREE PARITY between development and main.
  Run it after a staging rebuild and before push.

  PASS (exit 0) requires all of:
    * zero DIFF files that are OFF the PROMOTE.manifest allow-list
    * no __pycache__ / *.pyc in staging
    * no files under a non-publish lane (messaging / metadata / sandbox)

  Classifications:
    DIFF  content differs between staging and dev at the same path
    GONE  present in staging, absent in dev (may be legitimately staging-
          authored, e.g. CHANGELOG.md) — reported, non-fatal unless -StrictGone
    OK    identical

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

$diffOn=@(); $diffOff=@(); $gone=@(); $junk=@(); $nonpub=@(); $ok=0
$nonpubRegex = '(^|/)(messaging|metadata|sandbox)/'
$junkRegex   = '(^|/)__pycache__/|\.pyc$'

# Enumerate the PUBLISHED set = git-tracked files in staging, NOT the working
# tree. This is what a `git clone` gets; on-disk-only artifacts (gitignored
# local LMDB rebuilds, __pycache__, scratch) are correctly ignored here.
$rels = & git -C $Stage ls-files
foreach ($rel in $rels) {
  $rel = $rel.Trim()
  if (-not $rel) { continue }

  if ($rel -match $junkRegex)   { $junk   += $rel }
  if ($rel -match $nonpubRegex) { $nonpub += $rel }

  $stagePath = Join-Path $Stage ($rel -replace '/','\')
  if (-not (Test-Path -LiteralPath $stagePath)) { continue }  # tracked, deleted on disk
  $devPath = Join-Path $Dev ($rel -replace '/','\')
  if (-not (Test-Path -LiteralPath $devPath)) { $gone += $rel; continue }

  $hs = (Get-FileHash -LiteralPath $stagePath -Algorithm SHA256).Hash
  $hd = (Get-FileHash -LiteralPath $devPath   -Algorithm SHA256).Hash
  if ($hs -eq $hd) { $ok++; continue }

  if (Test-OnAllowList $rel) { $diffOn += $rel } else { $diffOff += $rel }
}

function Show-Group([string]$title, [array]$items, [string]$color) {
  Write-Host ""
  Write-Host "$title : $($items.Count)" -ForegroundColor $color
  $items | Sort-Object | Select-Object -First 40 | ForEach-Object { Write-Host "    $_" }
  if ($items.Count -gt 40) { Write-Host "    ... and $($items.Count - 40) more" }
}

Write-Host ""
Write-Host "==== SUMMARY ====" -ForegroundColor Cyan
Write-Host "  identical                         : $ok"
Write-Host "  DIFF on allow-list (promote OK)   : $($diffOn.Count)"
Write-Host "  DIFF OFF allow-list (GATE)        : $($diffOff.Count)"
Write-Host "  GONE (staging-only)               : $($gone.Count)"
Write-Host "  __pycache__/*.pyc (GATE)          : $($junk.Count)"
Write-Host "  non-publish lane files (GATE)     : $($nonpub.Count)"

if ($diffOff.Count) { Show-Group "OFF-allow-list DIFF (add to manifest or purge)" $diffOff Yellow }
if ($junk.Count)    { Show-Group "Bytecode junk in staging (git rm --cached + gitignore)" $junk Red }
if ($nonpub.Count)  { Show-Group "Non-publish lane files in staging (remove from main)" $nonpub Red }
if ($gone.Count)    { Show-Group "GONE (confirm intentionally staging-authored)" $gone DarkGray }

$fail = ($diffOff.Count -gt 0) -or ($junk.Count -gt 0) -or ($nonpub.Count -gt 0)
if ($StrictGone -and $gone.Count -gt 0) { $fail = $true }

Write-Host ""
if ($ReportOnly) {
  Write-Host "REPORT-ONLY: gate would $([string]($(if($fail){'FAIL'}else{'PASS'})))." -ForegroundColor Cyan
  exit 0
}
if ($fail) {
  Write-Host "DRIFT GATE: FAIL" -ForegroundColor Red
  exit 1
} else {
  Write-Host "DRIFT GATE: PASS" -ForegroundColor Green
  exit 0
}
