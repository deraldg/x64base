<# 
tools\scan_phrase_and_cmdset.ps1

Usage examples:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\scan_phrase_and_cmdset.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\scan_phrase_and_cmdset.ps1 -Phrase "load_inx_recnos(" -FileName "cmd_list.cpp"

Notes:
- Works in Windows PowerShell 5.1 (no reliance on -Depth param).
- Limits effective recursion to 3 directory levels below the start path.
#>

[CmdletBinding()]
param(
  [string]$Phrase = 'load_inx_recnos(',
  # If provided, only files with this *name* (not path) are scanned for the phrase (e.g., "cmd_list.cpp").
  [string]$FileName,
  # Max directory levels below current dir to consider
  [int]$MaxDepth = 3
)

$ErrorActionPreference = "Stop"
$root = (Get-Location).Path
$sep  = [IO.Path]::DirectorySeparatorChar

Write-Host "== Scan root: $root" -ForegroundColor Cyan
Write-Host "   Max depth: $MaxDepth" -ForegroundColor Cyan
Write-Host "   Phrase   : $Phrase" -ForegroundColor Cyan
if ($FileName) { Write-Host "   FileName : $FileName" -ForegroundColor Cyan }

function Get-Depth([string]$p) {
  # directory depth = count of separators in full dir path (normalized)
  $dir = Split-Path -Parent $p
  if (-not $dir) { return 0 }
  $norm = $dir.TrimEnd($sep)
  return ($norm -split [regex]::Escape("$sep")).Count
}

$rootDepth = ( ($root.TrimEnd($sep)) -split [regex]::Escape("$sep") ).Count

# Candidate file list (code-y extensions)
$exts = @('*.cpp','*.c','*.hpp','*.h')

$all = @()
foreach ($pat in $exts) {
  $all += Get-ChildItem -Path $root -Recurse -File -Include $pat -ErrorAction SilentlyContinue
}

# Enforce depth limit
$scoped = $all | Where-Object { (Get-Depth $_.FullName) -le ($rootDepth + $MaxDepth) }

# If FileName is provided, restrict phrase scan to that exact leaf-name
if ($FileName) {
  $scanFiles = $scoped | Where-Object { $_.Name -ieq $FileName }
} else {
  $scanFiles = $scoped
}

Write-Host "`n-- Phrase scan --" -ForegroundColor Yellow
$hits = @()
foreach ($f in $scanFiles) {
  $m = Select-String -Path $f.FullName -Pattern [regex]::Escape($Phrase) -AllMatches -ErrorAction SilentlyContinue
  if ($m) {
    foreach ($h in $m) {
      $rel = $f.FullName.Substring($root.Length).TrimStart($sep)
      $preview = $h.Line.Trim()
      Write-Host ("  {0}:{1}  {2}" -f $rel, $h.LineNumber, $preview) -ForegroundColor Green
      $hits += [PSCustomObject]@{
        File      = $f.FullName
        Rel       = $rel
        Line      = $h.LineNumber
        LineText  = $preview
      }
    }
  }
}
if ($hits.Count -eq 0) {
  Write-Host "  (no matches within depth $MaxDepth)" -ForegroundColor DarkGray
}

Write-Host "`n-- cmd_set.cpp discovery --" -ForegroundColor Yellow
$cmdSetAll = $scoped | Where-Object { $_.Name -ieq 'cmd_set.cpp' }
if ($cmdSetAll.Count -gt 0) {
  foreach ($f in $cmdSetAll) {
    $rel = $f.FullName.Substring($root.Length).TrimStart($sep)
    Write-Host ("  found: {0}" -f $rel) -ForegroundColor Green
  }
} else {
  Write-Host "  (no cmd_set.cpp within depth $MaxDepth)" -ForegroundColor DarkGray
}

Write-Host "`n-- Sibling check: does each host dir contain cmd_set.cpp? --" -ForegroundColor Yellow
if ($hits.Count -gt 0) {
  # Group hits by directory (host file directory)
  $byDir = $hits | Group-Object { Split-Path -Parent $_.File }
  foreach ($g in $byDir) {
    $dir = $g.Name
    $relDir = $dir.Substring($root.Length).TrimStart($sep)
    $hasCmdSet = Test-Path (Join-Path $dir 'cmd_set.cpp')
    $status = $(if ($hasCmdSet) { "YES" } else { "NO" })
    Write-Host ("  {0,-40} cmd_set.cpp: {1}" -f $relDir, $status) -ForegroundColor $(if ($hasCmdSet) { "Green" } else { "Red" })
  }
} else {
  Write-Host "  (skipped: no phrase hosts found)" -ForegroundColor DarkGray
}

Write-Host "`n== Summary ==" -ForegroundColor Cyan
Write-Host ("  Phrase matches : {0}" -f $hits.Count)
Write-Host ("  cmd_set.cpp    : {0}" -f $cmdSetAll.Count)
Write-Host ""
