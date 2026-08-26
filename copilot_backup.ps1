<#
.SYNOPSIS
  Bundle only source + build scripts into a lean ZIP.
  Includes:  *.cpp, *.hpp, CMakeLists.txt, Makefile/makefile, *.ps1
  Excludes:  build artifacts and VCS folders.
  Output:    D:\backups by default (override with -OutDir).
  Scans:     root, src, includes, tests, data, tools, results
#>

[CmdletBinding()]
param(
  [string]$OutDir = "D:\backups",
  [string]$Label  = "alpha-4.2"
)

$ErrorActionPreference = "Stop"

# Resolve an absolute output path. An absolute -OutDir is honoured as given;
# a relative one still resolves under the current repo. Join-Path does NOT
# special-case a rooted second argument, so testing first is required --
# otherwise "D:\backups" would become "<repo>\D:\backups".
$repoRoot = (Get-Location).Path
$absOut   = if ([System.IO.Path]::IsPathRooted($OutDir)) {
    [System.IO.Path]::GetFullPath($OutDir)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutDir))
}

# Ensure output directory exists
if (-not (Test-Path -LiteralPath $absOut)) {
  New-Item -ItemType Directory -Path $absOut | Out-Null
}

# Timestamp and zip name
$ts      = Get-Date -Format "yyyyMMdd-HHmmss"
$zipName = "ccode-sources-$Label-$ts.zip"
$zipPath = Join-Path $absOut $zipName

# Patterns to include
$includePatterns = @(
  "*.cpp","*.hpp",
  "CMakeLists.txt",
  "Makefile","makefile",
  "*.ps1"
)

# Directories to scan
$scanDirs = @(
  $repoRoot,
  (Join-Path $repoRoot "src"),
  (Join-Path $repoRoot "includes"),
  (Join-Path $repoRoot "tests"),
  (Join-Path $repoRoot "data"),
  (Join-Path $repoRoot "tools"),
  (Join-Path $repoRoot "results")
)

# Directories to exclude (regex, case-insensitive)
$excludeDirRegex = '(?i)\\(?:\.git|\.vs|build|_ccode_build|_pcode_build|x64|x86|Debug|Release|CMakeFiles|out|bin|obj)(\\|$)'

# Collect files per pattern from each directory
$files = @()
foreach ($dir in $scanDirs) {
  foreach ($pat in $includePatterns) {
    $files += Get-ChildItem -Path $dir -Recurse -File -Include $pat -ErrorAction SilentlyContinue
  }
}

# De-duplicate and exclude unwanted directories
$files = $files |
  Sort-Object FullName -Unique |
  Where-Object { $_.FullName -notmatch $excludeDirRegex }

if (-not $files) {
  Write-Warning "No matching files found."
  return
}

# Optional: Warn if no CMakeLists.txt found
if (-not ($files | Where-Object { $_.Name -eq "CMakeLists.txt" })) {
  Write-Warning "No CMakeLists.txt found in the bundle."
}

# Create the zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

$zip = [System.IO.Compression.ZipFile]::Open($zipPath, 'Create')
try {
  foreach ($f in $files) {
    # store path relative to repo root
    $rel = $f.FullName.Substring($repoRoot.Length).TrimStart('\','/')
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
      $zip, $f.FullName, $rel, [System.IO.Compression.CompressionLevel]::Optimal
    ) | Out-Null
  }
}
finally {
  $zip.Dispose()
}

Write-Host "Created bundle:" -ForegroundColor Green
Write-Host "  $zipPath"
Write-Host ("  Files included: {0}" -f $files.Count)