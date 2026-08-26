<#
.SYNOPSIS
  Tiny offsite code backup: C++ and Python source only, one rotated ZIP.

.DESCRIPTION
  The offsite leg. The bulk backups go to D:\backups, which lives on the same
  physical disk as the repository -- a drive failure would take both. This one
  is deliberately small enough to sit in OneDrive without filling C:.

  It carries SOURCE ONLY: C/C++ translation units and headers, and Python.
  No documents, media, DBF data, manuals, binaries or generated output.

  THE FILTER IS GIT, not a directory walk. Only tracked files are considered,
  so anything gitignored -- .venv, .venv312, build trees, node_modules,
  vcpkg_installed, runtime data -- is excluded by construction rather than by
  a regex someone has to remember to update. That is the whole reason this
  script is short and the essential-drop scripts are not.

  Output is a single ZIP. One file syncs to OneDrive far better than thousands
  of small ones, and -Keep prunes old drops so the folder cannot grow back into
  the problem it was written to avoid.

.EXAMPLE
  .\backup_code_offsite.ps1 -Plan
  .\backup_code_offsite.ps1
  .\backup_code_offsite.ps1 -DropRoot E:\offsite -Keep 20
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepoRoot = "",
    [string]$DropRoot = "",
    [string]$Label = "code",
    [int]$Keep = 10,
    [switch]$Plan
)

$ErrorActionPreference = "Stop"

function Resolve-RepositoryRoot {
    param([string]$RequestedRoot)
    $start = if ([string]::IsNullOrWhiteSpace($RequestedRoot)) { $PSScriptRoot } else { $RequestedRoot }
    $start = (Resolve-Path -LiteralPath $start).Path
    $root = (& git -C $start rev-parse --show-toplevel 2>$null | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
        throw "Not a Git working tree: $start. This script filters by 'git ls-files' and cannot run without it."
    }
    return (Resolve-Path -LiteralPath ($root.Trim())).Path
}

function Resolve-DropRoot {
    param([string]$RequestedRoot)
    if (-not [string]::IsNullOrWhiteSpace($RequestedRoot)) {
        return [System.IO.Path]::GetFullPath($RequestedRoot)
    }
    $oneDrive = $env:OneDrive
    if ([string]::IsNullOrWhiteSpace($oneDrive)) { $oneDrive = Join-Path $HOME 'OneDrive' }
    return [System.IO.Path]::GetFullPath((Join-Path $oneDrive 'ccode_code'))
}

$codeExtensions = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
@(
    '.c', '.cc', '.cpp', '.cxx',
    '.h', '.hh', '.hpp', '.hxx',
    '.ipp', '.inl', '.tpp',
    '.py', '.pyi'
) | ForEach-Object { [void]$codeExtensions.Add($_) }

$RepoRoot = Resolve-RepositoryRoot $RepoRoot
$DropRoot = Resolve-DropRoot $DropRoot

$tracked = @(& git -C $RepoRoot ls-files)
if ($LASTEXITCODE -ne 0) { throw 'git ls-files failed.' }

$selected = [System.Collections.Generic.List[object]]::new()
$totalBytes = 0L
foreach ($relative in $tracked) {
    if ([string]::IsNullOrWhiteSpace($relative)) { continue }
    if (-not $codeExtensions.Contains([System.IO.Path]::GetExtension($relative))) { continue }
    $full = Join-Path $RepoRoot $relative
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { continue }
    $item = Get-Item -LiteralPath $full
    $selected.Add([pscustomobject]@{ Relative = $relative; Full = $item.FullName; Bytes = $item.Length }) | Out-Null
    $totalBytes += $item.Length
}

if ($selected.Count -eq 0) { throw "No tracked C++/Python source found under $RepoRoot." }

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$safeLabel = ($Label -replace '[^A-Za-z0-9_.-]+', '_').Trim('_')
if ([string]::IsNullOrWhiteSpace($safeLabel)) { $safeLabel = 'code' }
$zipPath = Join-Path $DropRoot ("ccode_${safeLabel}_${timestamp}.zip")

if ($Plan -or $WhatIfPreference) {
    Write-Host 'Offsite code drop plan'
    Write-Host "  RepoRoot : $RepoRoot"
    Write-Host "  DropRoot : $DropRoot"
    Write-Host "  Files    : $($selected.Count)"
    Write-Host ("  Raw size : {0:N2} MB (zipped is typically a quarter of this)" -f ($totalBytes / 1MB))
    Write-Host "  Keep     : $Keep most recent zip(s)"
    $selected |
        Group-Object { [System.IO.Path]::GetExtension($_.Relative).ToLowerInvariant() } |
        Sort-Object Name |
        ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
    return
}

if (-not (Test-Path -LiteralPath $DropRoot)) {
    New-Item -ItemType Directory -Path $DropRoot -Force | Out-Null
}

# Stage into a temp tree, zip it, then drop the tree. Compress-Archive cannot
# take an explicit file list and preserve relative paths, and a staging copy of
# 20 MB of text is cheap.
$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("ccode_code_" + [System.Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage -Force | Out-Null
try {
    foreach ($entry in $selected) {
        $destination = Join-Path $stage $entry.Relative
        $destinationDir = Split-Path -Parent $destination
        if (-not (Test-Path -LiteralPath $destinationDir)) {
            New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        }
        Copy-Item -LiteralPath $entry.Full -Destination $destination -Force
    }

    (& git -C $RepoRoot rev-parse HEAD) | Set-Content -Encoding UTF8 (Join-Path $stage 'GIT_HEAD.txt')
    $selected |
        Select-Object Relative, Bytes |
        Sort-Object Relative |
        Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $stage 'MANIFEST.csv')

    if ($PSCmdlet.ShouldProcess($zipPath, 'Create offsite code zip')) {
        if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
        Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zipPath -CompressionLevel Optimal -Force
    }
} finally {
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
}

# Rotation. Without this the offsite folder becomes the problem it replaced.
$pruned = 0
if ($Keep -gt 0) {
    $existing = @(Get-ChildItem -LiteralPath $DropRoot -File -Filter "ccode_${safeLabel}_*.zip" |
                  Sort-Object LastWriteTime -Descending)
    if ($existing.Count -gt $Keep) {
        foreach ($old in $existing[$Keep..($existing.Count - 1)]) {
            if ($PSCmdlet.ShouldProcess($old.FullName, 'Prune old offsite zip')) {
                Remove-Item -LiteralPath $old.FullName -Force
                $pruned++
            }
        }
    }
}

$zipBytes = if (Test-Path -LiteralPath $zipPath) { (Get-Item -LiteralPath $zipPath).Length } else { 0 }
Write-Host 'Offsite code drop complete'
Write-Host "  RepoRoot : $RepoRoot"
Write-Host "  Zip      : $zipPath"
Write-Host "  Files    : $($selected.Count)"
Write-Host ("  Raw      : {0:N2} MB" -f ($totalBytes / 1MB))
Write-Host ("  Zipped   : {0:N2} MB" -f ($zipBytes / 1MB))
if ($pruned -gt 0) { Write-Host "  Pruned   : $pruned old zip(s), keeping $Keep" }
