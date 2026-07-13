<#
.SYNOPSIS
  Fast local backup of source and build-control files.

.DESCRIPTION
  Creates a timestamped source backup under C:\Users\deral\OneDrive\ccode_drops by default.
  This is intentionally narrow: C++/CMake/Python source, headers, GUI source,
  build metadata, and a small set of root scripts/config files.

  It is a backup drop, not a staging sync and not a GitHub packaging tool.
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path,
    [string]$DevRoot = "D:\dev",
    [string]$DropRoot = "C:\Users\deral\OneDrive\ccode_drops",
    [string]$Label = "source",
    [switch]$NoDev,
    [switch]$Plan,
    [switch]$Zip
)

$ErrorActionPreference = "Stop"
$IsWhatIf = [bool]$WhatIfPreference

function Resolve-ExistingDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)
    $resolved = Resolve-Path -LiteralPath $Path
    $item = Get-Item -LiteralPath $resolved.Path
    if (-not $item.PSIsContainer) {
        throw "Not a directory: $Path"
    }
    return $item.FullName
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force -WhatIf:$IsWhatIf | Out-Null
    }
}

function Test-UnderPath {
    param(
        [Parameter(Mandatory = $true)][string]$Child,
        [Parameter(Mandatory = $true)][string]$Parent
    )
    $childFull = [System.IO.Path]::GetFullPath($Child).TrimEnd('\')
    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\')
    return $childFull.StartsWith($parentFull + '\', [System.StringComparison]::OrdinalIgnoreCase)
}

$RepoRoot = Resolve-ExistingDirectory $RepoRoot
$DevRoot = if (Test-Path -LiteralPath $DevRoot -PathType Container) { Resolve-ExistingDirectory $DevRoot } else { $DevRoot }
$DropRoot = [System.IO.Path]::GetFullPath($DropRoot)

if (Test-UnderPath -Child $DropRoot -Parent $RepoRoot) {
    throw "DropRoot must be outside the repo. Refusing: $DropRoot"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$safeLabel = ($Label -replace '[^A-Za-z0-9_.-]+', '_').Trim('_')
if ([string]::IsNullOrWhiteSpace($safeLabel)) { $safeLabel = "source" }
$dropName = "ccode_${safeLabel}_${timestamp}"
$outDir = Join-Path $DropRoot $dropName

$sourceDirs = @("src", "include", "bindings", "cmake") |
    ForEach-Object { Join-Path $RepoRoot $_ } |
    Where-Object { Test-Path -LiteralPath $_ -PathType Container }

$rootFiles = @(
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "CMakeLists.txt",
    "CMakePresets.json",
    "vcpkg.json",
    "vcpkg-wsl.json",
    "pyproject.toml",
    "Makefile",
    "build.ps1",
    "datarun.ps1",
    "datarun_wsl.sh",
    "wslrun.sh",
    "wx.run.ps1",
    "wx.next.run.ps1",
    "arctictalk.datarun.ps1"
) | ForEach-Object { Join-Path $RepoRoot $_ } |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }

$keepExt = @(
    ".c", ".cc", ".cpp", ".cxx",
    ".h", ".hh", ".hpp", ".hxx",
    ".ipp", ".inl", ".tpp",
    ".cmake", ".rc", ".def",
    ".py", ".ps1", ".psm1", ".sh",
    ".json", ".toml"
)

$excludePathRegex = @(
    '\\.git($|\\)',
    '\\.vs($|\\)',
    '\\.vscode($|\\)',
    '\\build[-\w]*($|\\)',
    '\\vcpkg_installed($|\\)',
    '\\_drops($|\\)',
    '\\logs($|\\)',
    '\\tmp($|\\)',
    '\\__pycache__($|\\)',
    '\\node_modules($|\\)',
    '\\.next($|\\)',
    '\\out($|\\)',
    '\\.gh-pages-deploy($|\\)',
    '\\.sites-artifact($|\\)',
    '\\.next-dev\.(stdout|stderr)\.log$',
    '\\x64base-sites-artifact\.tar\.gz$',
    '\\x64base-IIS($|\\)'
) -join '|'

$filesByPath = [ordered]@{}
$relativeByPath = [ordered]@{}
foreach ($dir in $sourceDirs) {
    Get-ChildItem -LiteralPath $dir -Recurse -File -Force |
        Where-Object {
            $_.FullName -notmatch $excludePathRegex -and
            $keepExt -contains $_.Extension.ToLowerInvariant()
        } |
        ForEach-Object {
            $filesByPath[$_.FullName] = $_
            $relativeByPath[$_.FullName] = $_.FullName.Substring($RepoRoot.Length).TrimStart('\')
        }
}
foreach ($file in $rootFiles) {
    $item = Get-Item -LiteralPath $file
    $filesByPath[$item.FullName] = $item
    $relativeByPath[$item.FullName] = $item.FullName.Substring($RepoRoot.Length).TrimStart('\')
}

if (-not $NoDev -and (Test-Path -LiteralPath (Join-Path $DevRoot "x64base-site") -PathType Container)) {
    $siteRoot = Join-Path $DevRoot "x64base-site"
    $siteExt = @(
        ".ts", ".tsx", ".js", ".jsx", ".mjs", ".css", ".md", ".mdx",
        ".json", ".yml", ".yaml", ".toml", ".html", ".txt", ".ps1",
        ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
        ".xml", ".csv", ".drawio"
    )
    Get-ChildItem -LiteralPath $siteRoot -Recurse -File -Force |
        Where-Object {
            $_.FullName -notmatch $excludePathRegex -and
            $siteExt -contains $_.Extension.ToLowerInvariant()
        } |
        ForEach-Object {
            $filesByPath[$_.FullName] = $_
            $relativeByPath[$_.FullName] = Join-Path "dev" ($_.FullName.Substring($DevRoot.Length).TrimStart('\'))
        }
}

if ($Plan) {
    Write-Host "Source drop plan"
    Write-Host "  RepoRoot : $RepoRoot"
    Write-Host "  DevRoot  : $DevRoot"
    Write-Host "  DropRoot : $DropRoot"
    Write-Host "  Files    : $($filesByPath.Count)"
    $filesByPath.Values |
        ForEach-Object { $relativeByPath[$_.FullName] } |
        ForEach-Object { ($_ -split '[\\/]')[0] } |
        Group-Object |
        Sort-Object Name |
        ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
    return
}

Ensure-Directory $DropRoot
Ensure-Directory $outDir

$manifestRows = New-Object System.Collections.Generic.List[object]
foreach ($file in $filesByPath.Values) {
    $relative = $relativeByPath[$file.FullName]
    $destination = Join-Path $outDir $relative
    $destinationDir = Split-Path -Parent $destination
    Ensure-Directory $destinationDir
    if ($PSCmdlet.ShouldProcess($destination, "Copy $relative")) {
        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force -WhatIf:$IsWhatIf
    }
    $manifestRows.Add([pscustomobject]@{
        Relative = $relative
        Source = $file.FullName
        Destination = $destination
        Bytes = $file.Length
        LastWriteTimeUtc = $file.LastWriteTimeUtc.ToString("o")
    }) | Out-Null
}

$manifest = Join-Path $outDir "MANIFEST.csv"
if ($PSCmdlet.ShouldProcess($manifest, "Write manifest")) {
    $manifestRows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $manifest -WhatIf:$IsWhatIf
}

if ($Zip -and -not $IsWhatIf) {
    $zipPath = Join-Path $DropRoot ($dropName + ".zip")
    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    Compress-Archive -Path (Join-Path $outDir "*") -DestinationPath $zipPath -Force
}

Write-Host "Source drop complete"
Write-Host "  RepoRoot : $RepoRoot"
Write-Host "  Drop     : $outDir"
Write-Host "  Files    : $($manifestRows.Count)"
if ($Zip -and -not $IsWhatIf) {
    Write-Host "  Zip      : $zipPath"
}
