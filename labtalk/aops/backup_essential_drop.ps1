<#
.SYNOPSIS
  Everything needed to rebuild this environment: the whole tracked tree, plus
  new work not yet added, plus anything you name explicitly.

.DESCRIPTION
  Covers THIS REPOSITORY ONLY. D:\dev has its own backups and is not reached
  from here.

  WHY THIS IS SHORT. The previous version carried a hand-written allowlist of
  directories and a hand-written exclusion regex, and both drifted. It missed
  labtalk (the AI portal, registries, proofs), tests, coordination, selfdoc,
  gui, and docs/maintenance -- 608 tracked files holding every lane record and
  session closeout. It also named six root files that no longer exist and
  skipped them SILENTLY, while printing a healthy count.

  THE FILTER IS GIT. A tracked file is one you already decided to keep; that
  decision does not need restating in a second list that can fall behind it.
  Nothing gitignored can arrive by accident -- no .venv, no build tree, no
  node_modules, no vcpkg_installed -- so there is no exclusion regex to
  maintain and no walk to prune.

  Three sources, in order:
    1. every tracked file, copied FROM THE WORKING TREE so uncommitted edits
       are preserved;
    2. every untracked file Git would not ignore -- new work that has not been
       added yet, which is exactly what a backup taken mid-session must not
       lose;
    3. anything given with -ExtraPath, for an ignored asset or seed database
       that cannot be regenerated.

  Git metadata rides along: HEAD, status, and binary patches of both the
  worktree and the index, so a restore can reproduce the exact working state
  rather than just the files.

.EXAMPLE
  .\backup_essential_drop.ps1 -Plan
  .\backup_essential_drop.ps1 -Zip
  .\backup_essential_drop.ps1 -ExtraPath D:\data\seed.sqlite -Zip
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepoRoot = "",
    [string]$DropRoot = "D:\backups",
    [string]$Label = "essential",
    [string[]]$ExtraPath = @(),
    [switch]$Plan,
    [switch]$Zip
)

$ErrorActionPreference = "Stop"
$IsWhatIf = [bool]$WhatIfPreference

function Resolve-RepositoryRoot {
    param([string]$RequestedRoot)
    $start = if ([string]::IsNullOrWhiteSpace($RequestedRoot)) {
        (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
    } else { $RequestedRoot }
    $start = (Resolve-Path -LiteralPath $start).Path
    $root = (& git -C $start rev-parse --show-toplevel 2>$null | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
        throw "Not a Git working tree: $start. This script filters by 'git ls-files' and cannot run without it."
    }
    return (Resolve-Path -LiteralPath ($root.Trim())).Path
}

function Test-UnderPath {
    param([string]$Child, [string]$Parent)
    $c = [System.IO.Path]::GetFullPath($Child).TrimEnd('\', '/')
    $p = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    return $c.Equals($p, [System.StringComparison]::OrdinalIgnoreCase) -or
           $c.StartsWith($p + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)
}

function Convert-ToSafeRelativePath {
    param([string]$RelativePath)
    $parts = $RelativePath -split '[\\/]'
    for ($i = 0; $i -lt $parts.Count; $i++) {
        $name = $parts[$i].TrimEnd('.', ' ')
        $base = [System.IO.Path]::GetFileNameWithoutExtension($name)
        if ($base -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$') { $name = '_device_' + $name }
        $parts[$i] = $name
    }
    return ($parts -join [System.IO.Path]::DirectorySeparatorChar)
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force -WhatIf:$IsWhatIf | Out-Null
    }
}

$RepoRoot = Resolve-RepositoryRoot $RepoRoot
$DropRoot = [System.IO.Path]::GetFullPath($DropRoot)
if (Test-UnderPath -Child $DropRoot -Parent $RepoRoot) {
    throw "DropRoot must be outside the repository. Refusing: $DropRoot"
}

# Destination-relative path -> source absolute path.
$files = [ordered]@{}
function Add-RepositoryFile {
    param([string]$RelativePath)
    if ([string]::IsNullOrWhiteSpace($RelativePath)) { return }
    $source = Join-Path $RepoRoot $RelativePath
    if (Test-Path -LiteralPath $source -PathType Leaf) {
        $files[$RelativePath] = (Get-Item -LiteralPath $source).FullName
    }
}

$tracked = @(& git -C $RepoRoot ls-files)
if ($LASTEXITCODE -ne 0) { throw 'git ls-files failed.' }
foreach ($relative in $tracked) { Add-RepositoryFile $relative }
$trackedCount = $files.Count

# New work not yet added. A backup taken mid-session that drops these has
# missed the only copy that exists -- and in this repository that is most of
# the documentation: measured 2026-08-25, 869 untracked files under
# docs/maintenance and 1,914 under docs/datadict exist ONLY on disk.
#
# Two classes are withheld, and only from the UNTRACKED sweep. A tracked
# table or fixture was committed on purpose and still travels.
#
#   1. Runtime table data under dottalkpp/data -- the live DBF/index root,
#      regenerable and rewritten constantly (583 files). Evidence fixtures of
#      the same kinds elsewhere, notably the 231 under docs/maintenance, are
#      NOT withheld: those are attached to lane records and cannot be rebuilt.
#   2. CMake build artifacts, which are only untracked here because
#      scripts/build sits outside the ignore rule's anchor (22 files).
$untrackedSkip = '(?i)^dottalkpp/data/.*\.(dbf|cdx|dbt|dtx|idx|cnx)$|CMakeFiles/|CMakeCache\.txt$|\.tlog/|\.recipe$|\.lastbuildstate$'

$untracked = @(& git -C $RepoRoot ls-files --others --exclude-standard)
if ($LASTEXITCODE -ne 0) { throw 'git ls-files --others failed.' }
$untrackedSkipped = 0
foreach ($relative in $untracked) {
    if ($relative -match $untrackedSkip) { $untrackedSkipped++; continue }
    Add-RepositoryFile $relative
}
$untrackedCount = $files.Count - $trackedCount

# Explicit extras override every rule because the caller called them
# indispensable. Stored beneath extras/ so they cannot collide with the tree.
$extraNumber = 0
foreach ($requested in $ExtraPath) {
    if ([string]::IsNullOrWhiteSpace($requested)) { continue }
    if (-not (Test-Path -LiteralPath $requested)) { throw "ExtraPath not found: $requested" }
    $resolved = Get-Item -LiteralPath (Resolve-Path -LiteralPath $requested).Path
    $extraNumber++
    $prefix = Join-Path 'extras' ('{0:D2}_{1}' -f $extraNumber, $resolved.Name)
    if ($resolved.PSIsContainer) {
        Get-ChildItem -LiteralPath $resolved.FullName -Recurse -File -Force |
            ForEach-Object {
                $inside = [System.IO.Path]::GetRelativePath($resolved.FullName, $_.FullName)
                $files[(Join-Path $prefix $inside)] = $_.FullName
            }
    } else {
        $files[$prefix] = $resolved.FullName
    }
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$safeLabel = ($Label -replace '[^A-Za-z0-9_.-]+', '_').Trim('_')
if ([string]::IsNullOrWhiteSpace($safeLabel)) { $safeLabel = 'essential' }
$dropName = "ccode_${safeLabel}_${timestamp}"
$outDir = Join-Path $DropRoot $dropName

if ($Plan -or $IsWhatIf) {
    Write-Host 'Essential drop plan'
    Write-Host "  RepoRoot  : $RepoRoot"
    Write-Host "  DropRoot  : $DropRoot"
    Write-Host "  Tracked   : $trackedCount"
    Write-Host "  Untracked : $untrackedCount (not ignored by Git)"
    Write-Host "  Withheld  : $untrackedSkipped untracked runtime/build artifact(s)"
    Write-Host "  Extras    : $($files.Count - $trackedCount - $untrackedCount)"
    Write-Host "  Files     : $($files.Count)"
    $files.Keys |
        ForEach-Object { ($_ -split '[\\/]')[0] } |
        Group-Object | Sort-Object Count -Descending |
        Select-Object -First 20 |
        ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
    return
}

Ensure-Directory $DropRoot
Ensure-Directory $outDir

$manifestRows = [System.Collections.Generic.List[object]]::new()
foreach ($relative in ($files.Keys | Sort-Object)) {
    $source = $files[$relative]
    $storedRelative = Convert-ToSafeRelativePath $relative
    $destination = Join-Path $outDir $storedRelative
    Ensure-Directory (Split-Path -Parent $destination)
    if ($PSCmdlet.ShouldProcess($destination, "Copy $relative")) {
        Copy-Item -LiteralPath $source -Destination $destination -Force
    }
    $item = Get-Item -LiteralPath $source
    $manifestRows.Add([pscustomobject]@{
        Relative       = $relative
        StoredRelative = $storedRelative
        Source         = $item.FullName
        Bytes          = $item.Length
        LastWriteUtc   = $item.LastWriteTimeUtc.ToString('o')
        SHA256         = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    }) | Out-Null
}

$manifestRows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $outDir 'MANIFEST.csv')
# -Value, not the pipeline. Piping empty output to Set-Content never invokes
# it, so the file is simply not created -- and a MISSING patch file reads as
# "not captured" when it means "nothing was staged". Measured 2026-08-25: the
# first real drop had no GIT_STAGED.patch for exactly that reason. An explicit
# empty file says the question was asked and the answer was zero.
function Write-GitArtifact {
    param([string]$Name, [string[]]$GitArgs)
    $text = (& git -C $RepoRoot @GitArgs) -join "`r`n"
    Set-Content -Encoding UTF8 -Path (Join-Path $outDir $Name) -Value $text
}

Write-GitArtifact 'GIT_HEAD.txt'       @('rev-parse', 'HEAD')
Write-GitArtifact 'GIT_STATUS.txt'     @('status', '--short', '--branch', '-uall')
Write-GitArtifact 'GIT_WORKTREE.patch' @('diff', '--binary')
Write-GitArtifact 'GIT_STAGED.patch'   @('diff', '--cached', '--binary')

if ($Zip) {
    $zipPath = Join-Path $DropRoot ($dropName + '.zip')
    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    Compress-Archive -Path (Join-Path $outDir '*') -DestinationPath $zipPath -Force
}

Write-Host 'Essential drop complete'
Write-Host "  RepoRoot  : $RepoRoot"
Write-Host "  Drop      : $outDir"
Write-Host "  Tracked   : $trackedCount"
Write-Host "  Untracked : $untrackedCount"
Write-Host "  Withheld  : $untrackedSkipped untracked runtime/build artifact(s)"
Write-Host "  Files     : $($manifestRows.Count)"
if ($Zip) { Write-Host "  Zip       : $zipPath" }
