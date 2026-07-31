<# 
deep_find_legacy.ps1  (Win PowerShell 5.1 compatible)

Scans folders (depth-limited) AND inside .zip/.tar/.tgz/.tar.gz archives
for target filenames and an optional phrase.

Run from the directory ABOVE ccode:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\ccode\tools\deep_find_legacy.ps1
#>

[CmdletBinding()]
param(
  [string]$StartPath = ".",
  [int]$MaxDepth = 4,
  [string[]]$Patterns = @(
    "index_legacy.hpp",
    "index_legacy.cpp",
    "*inx*loader*.cpp",
    "cmd_set_legacy.cpp",
    "cmd_set_shim.cpp",
    "cmd_set.cpp"
  ),
  [string]$Phrase = "load_inx_recnos(",
  [string[]]$CodeExts = @("*.cpp","*.c","*.hpp","*.h"),
  [int]$MaxBytesToRead = 8MB
)

$ErrorActionPreference = "Stop"

# --- Helpers ---
$sep = [IO.Path]::DirectorySeparatorChar
function Get-BaseDepth([string]$p){ (($p.TrimEnd($sep)) -split [regex]::Escape("$sep")).Count }
function Get-Depth([string]$base, [string]$path){
  $b = Get-BaseDepth $base
  $d = Get-BaseDepth (Split-Path -Parent $path)
  return ($d - $b)
}
function NameMatches([string]$leafName, [string[]]$patterns){
  foreach($pat in $patterns){
    if ([System.Management.Automation.WildcardPattern]::new($pat,'IgnoreCase').IsMatch($leafName)) { return $true }
  }
  return $false
}
function Show-Hit([string]$where, [string]$container, [string]$name, [string]$rel, [int]$line=0){
  $loc = if ($line -gt 0) { "$($rel):$line" } else { $rel }   # <-- PS 5.1 safe
  Write-Host ("[{0}] {1}  ->  {2}" -f $where, $container, $loc) -ForegroundColor Green
}

# Detect 'tar' availability (PS 5.1 safe)
$TarCmd = $null
$tarCmdObj = Get-Command tar -ErrorAction SilentlyContinue
if ($tarCmdObj) { $TarCmd = $tarCmdObj.Source }
$HasTar = [bool]$TarCmd

$root = (Resolve-Path $StartPath).Path
Write-Host "== Root: $root" -ForegroundColor Cyan
Write-Host "   Depth: $MaxDepth  |  Tar available: $HasTar" -ForegroundColor Cyan
Write-Host "   Patterns: $($Patterns -join ', ')" -ForegroundColor Cyan
Write-Host "   Phrase:   $Phrase" -ForegroundColor Cyan

# --- Filesystem scan (within depth) ---
$fsFiles = Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
           Where-Object { (Get-Depth $root $_.FullName) -le $MaxDepth }

# Name hits
foreach($f in $fsFiles){
  if (NameMatches $f.Name $Patterns) {
    $rel = $f.FullName.Substring($root.Length).TrimStart($sep)
    Show-Hit "FS" "<dir>" $f.Name $rel
  }
}

# Phrase hits in code files
if ($Phrase){
  $codeFiles = $fsFiles | Where-Object {
    $leaf = $_.Name
    $ok = $false
    foreach($e in $CodeExts){ if ([WildcardPattern]::new($e,'IgnoreCase').IsMatch($leaf)) { $ok = $true; break } }
    $ok
  }
  foreach($f in $codeFiles){
    try{
      if ($f.Length -gt $MaxBytesToRead) { continue }
      $hit = Select-String -Path $f.FullName -Pattern ([regex]::Escape($Phrase)) -AllMatches -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($hit){
        $rel = $f.FullName.Substring($root.Length).TrimStart($sep)
        Show-Hit "FS+TXT" "<dir>" $f.Name $rel $hit.LineNumber
      }
    } catch {}
  }
}

# --- ZIP/TAR scan ---
Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
$archives = Get-ChildItem -Path $root -Recurse -File -Include *.zip,*.tar,*.tgz,*.tar.gz -ErrorAction SilentlyContinue |
            Where-Object { (Get-Depth $root $_.FullName) -le $MaxDepth }

foreach($arc in $archives){
  $relArc = $arc.FullName.Substring($root.Length).TrimStart($sep)
  if ($arc.Extension.ToLower() -eq '.zip') {
    try{
      $zip = [System.IO.Compression.ZipFile]::OpenRead($arc.FullName)
      foreach($entry in $zip.Entries){
        $leaf = [IO.Path]::GetFileName($entry.FullName)
        if (-not $leaf) { continue }
        if (NameMatches $leaf $Patterns){ Show-Hit "ZIP" $relArc $leaf $entry.FullName }
        if ($Phrase -and $entry.Length -le $MaxBytesToRead -and $leaf -match '\.(cpp|c|hpp|h)$'){
          $sr = New-Object System.IO.StreamReader($entry.Open())
          $text = $sr.ReadToEnd()
          $sr.Dispose()
          if ($text -like "*$Phrase*"){
            $idx = $text.IndexOf($Phrase, [StringComparison]::Ordinal)
            $line = ($text.Substring(0,[Math]::Max(0,$idx)) -split "`r?`n").Count
            Show-Hit "ZIP+TXT" $relArc $leaf $entry.FullName $line
          }
        }
      }
      $zip.Dispose()
    } catch {
      Write-Host ("[WARN] Could not open ZIP: {0}  ({1})" -f $relArc, $_.Exception.Message) -ForegroundColor DarkYellow
    }
  } else {
    if (-not $HasTar){ 
      Write-Host ("[SKIP] No 'tar' to read {0}" -f $relArc) -ForegroundColor DarkGray
      continue
    }
    try{
      # list entries (try -t, then -tzf for gz)
      $list = & $TarCmd -tf $arc.FullName 2>$null
      if (-not $list){ $list = & $TarCmd -tzf $arc.FullName 2>$null }
      foreach($line in $list){
        $leaf = [IO.Path]::GetFileName($line)
        if (-not $leaf) { continue }
        if (NameMatches $leaf $Patterns){ Show-Hit "TAR" $relArc $leaf $line }
        if ($Phrase -and $leaf -match '\.(cpp|c|hpp|h)$'){
          try{
            $content = & $TarCmd -xOf $arc.FullName $line 2>$null
            if ($content -and ($content -like "*$Phrase*")){
              $lnum = 0
              foreach($ln in ($content -split "`r?`n")){
                $lnum++
                if ($ln -like "*$Phrase*"){ Show-Hit "TAR+TXT" $relArc $leaf $line $lnum; break }
              }
            }
          } catch {}
        }
      }
    } catch {
      Write-Host ("[WARN] Could not read TAR: {0}  ({1})" -f $relArc, $_.Exception.Message) -ForegroundColor DarkYellow
    }
  }
}

Write-Host "`n== Done ==" -ForegroundColor Cyan
