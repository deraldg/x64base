<#
.SYNOPSIS
  Curated local backup of source, scripts, schemas, contracts, and other
  non-recreatable project assets.

.DESCRIPTION
  Creates a timestamped backup under C:\Users\deral\OneDrive\ccode_drops by default.

  This is wider than backup_source_drop.ps1 but still curated. It avoids build
  directories, generated DBF/index/LMDB data, logs, repo-local drops, and bulky
  generated manual/dist artifacts unless explicitly added later.
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path,
    [string]$DevRoot = "D:\dev",
    [string]$DropRoot = "C:\Users\deral\OneDrive\ccode_drops",
    [string]$Label = "essential",
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

function Add-TreeFiles {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string[]]$Extensions,
        [string]$BaseRoot = $RepoRoot,
        [string]$Prefix = ""
    )

    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return }
    Get-ChildItem -LiteralPath $Root -Recurse -File -Force |
        Where-Object {
            $_.FullName -notmatch $script:excludePathRegex -and
            $Extensions -contains $_.Extension.ToLowerInvariant()
        } |
        ForEach-Object {
            $script:filesByPath[$_.FullName] = $_
            $relative = $_.FullName.Substring($BaseRoot.Length).TrimStart('\')
            if (-not [string]::IsNullOrWhiteSpace($Prefix)) {
                $relative = Join-Path $Prefix $relative
            }
            $script:relativeByPath[$_.FullName] = $relative
        }
}

function Add-RootFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string]$BaseRoot = $RepoRoot,
        [string]$Prefix = ""
    )

    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $item = Get-Item -LiteralPath $Path
        $script:filesByPath[$item.FullName] = $item
        $relative = $item.FullName.Substring($BaseRoot.Length).TrimStart('\')
        if (-not [string]::IsNullOrWhiteSpace($Prefix)) {
            $relative = Join-Path $Prefix $relative
        }
        $script:relativeByPath[$item.FullName] = $relative
    }
}

$RepoRoot = Resolve-ExistingDirectory $RepoRoot
$DevRoot = if (Test-Path -LiteralPath $DevRoot -PathType Container) { Resolve-ExistingDirectory $DevRoot } else { $DevRoot }
$DropRoot = [System.IO.Path]::GetFullPath($DropRoot)

if (Test-UnderPath -Child $DropRoot -Parent $RepoRoot) {
    throw "DropRoot must be outside the repo. Refusing: $DropRoot"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$safeLabel = ($Label -replace '[^A-Za-z0-9_.-]+', '_').Trim('_')
if ([string]::IsNullOrWhiteSpace($safeLabel)) { $safeLabel = "essential" }
$dropName = "ccode_${safeLabel}_${timestamp}"
$outDir = Join-Path $DropRoot $dropName

$script:excludePathRegex = @(
    '\\.git($|\\)',
    '\\.vs($|\\)',
    '\\.vscode($|\\)',
    '\\build[-\w]*($|\\)',
    '\\vcpkg_installed($|\\)',
    '\\_drops($|\\)',
    '\\logs($|\\)',
    '\\tmp($|\\)',
    '\\__pycache__($|\\)',
    '\\docs\\manuals\\dist($|\\)',
    '\\docs\\manuals\\developer\\manualgen\\generated($|\\)',
    '\\dottalkpp\\data\\dbf($|\\)',
    '\\dottalkpp\\data\\indexes($|\\)',
    '\\dottalkpp\\data\\lmdb($|\\)',
    '\\dottalkpp\\data\\tmp($|\\)',
    '\\dottalkpp\\data\\logs($|\\)',
    '\\node_modules($|\\)',
    '\\.next($|\\)',
    '\\out($|\\)',
    '\\.gh-pages-deploy($|\\)',
    '\\.sites-artifact($|\\)',
    '\\.next-dev\.(stdout|stderr)\.log$',
    '\\x64base-sites-artifact\.tar\.gz$',
    '\\x64base-IIS($|\\)',
    '\\_github_scan($|\\)'
) -join '|'

$script:filesByPath = [ordered]@{}
$script:relativeByPath = [ordered]@{}

$sourceExt = @(
    ".c", ".cc", ".cpp", ".cxx",
    ".h", ".hh", ".hpp", ".hxx",
    ".ipp", ".inl", ".tpp",
    ".cmake", ".rc", ".def",
    ".py", ".ps1", ".psm1", ".sh",
    ".json", ".toml", ".txt", ".md", ".csv", ".tsv", ".yaml", ".yml"
)

$scriptExt = @(".dts", ".erz", ".dtschema", ".ps1", ".sh", ".bat", ".cmd", ".json", ".md", ".csv", ".txt")
$docExt = @(".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".svg", ".drawio")
$devEssentialExt = @(
    ".docx", ".pptx", ".pdf", ".md", ".txt", ".drawio", ".dts",
    ".ps1", ".py", ".json", ".diff", ".patch", ".png",
    ".cpp", ".hpp", ".h", ".csv", ".yaml", ".yml"
)
$siteExt = @(
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".css", ".md", ".mdx",
    ".json", ".yml", ".yaml", ".toml", ".html", ".txt", ".ps1",
    ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
    ".xml", ".csv", ".drawio"
)

foreach ($dirName in @("src", "include", "bindings", "cmake", ".github")) {
    Add-TreeFiles -Root (Join-Path $RepoRoot $dirName) -Extensions $sourceExt
}

foreach ($dirName in @(
    "tools\contracts",
    "tools\datadict",
    "tools\gui",
    "tools\gui_preview",
    "tools\locale",
    "tools\maintenance",
    "tools\manualgen"
)) {
    Add-TreeFiles -Root (Join-Path $RepoRoot $dirName) -Extensions $sourceExt
}

Get-ChildItem -LiteralPath (Join-Path $RepoRoot "tools") -File -Filter "*.ps1" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $script:filesByPath[$_.FullName] = $_
        $script:relativeByPath[$_.FullName] = $_.FullName.Substring($RepoRoot.Length).TrimStart('\')
    }

foreach ($dirName in @(
    "docs\contracts",
    "docs\database",
    "docs\gui",
    "docs\ui",
    "docs\messaging\active",
    "docs\messaging\contracts",
    "docs\messaging\scripts",
    "docs\datadict\contracts",
    "docs\datadict\definitions",
    "docs\datadict\policies",
    "docs\datadict\policy",
    "docs\datadict\schemas",
    "docs\datadict\specs",
    "docs\datadict\templates"
)) {
    Add-TreeFiles -Root (Join-Path $RepoRoot $dirName) -Extensions $docExt
}

foreach ($dirName in @(
    "dottalkpp\data\scripts",
    "dottalkpp\data\schemas",
    "dottalkpp\data\workspaces"
)) {
    Add-TreeFiles -Root (Join-Path $RepoRoot $dirName) -Extensions $scriptExt
}

$rootFileNames = @(
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "CMakeLists.txt",
    "CMakePresets.json",
    "vcpkg.json",
    "vcpkg-wsl.json",
    "pyproject.toml",
    "Makefile",
    "README.md",
    "README_NEW.md",
    "MANIFEST.txt",
    "WORKFLOW_X64BASE.md",
    "X64BASE_DATA_STAGING_TRIAGE.md",
    "X64BASE_HYGIENE_INVENTORY.md",
    "X64BASE_REVERSE_NORMALIZATION_PLAN.md",
    "DOTTALKPP_DBF_PATH_POLICY.md",
    "DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md",
    "build.ps1",
    "datarun.ps1",
    "datarun_wsl.sh",
    "wslrun.sh",
    "wx.run.ps1",
    "wx.next.run.ps1",
    "arctictalk.datarun.ps1"
)

Get-ChildItem -LiteralPath $RepoRoot -File -Filter "homegrown*.ps1" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $script:filesByPath[$_.FullName] = $_
        $script:relativeByPath[$_.FullName] = $_.FullName.Substring($RepoRoot.Length).TrimStart('\')
    }

foreach ($name in $rootFileNames) {
    Add-RootFile -Path (Join-Path $RepoRoot $name)
}

if (-not $NoDev -and (Test-Path -LiteralPath $DevRoot -PathType Container)) {
    Add-TreeFiles -Root (Join-Path $DevRoot "x64base-site") -Extensions $siteExt -BaseRoot $DevRoot -Prefix "dev"
    Add-TreeFiles -Root (Join-Path $DevRoot "LabTalk_DotTalkpp_Systems_Storyboard_Deck") -Extensions $devEssentialExt -BaseRoot $DevRoot -Prefix "dev"

    Get-ChildItem -LiteralPath $DevRoot -File -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -notlike '~$*' -and
            $_.Extension.ToLowerInvariant() -ne ".exe" -and
            $devEssentialExt -contains $_.Extension.ToLowerInvariant() -and
            $_.FullName -notmatch $script:excludePathRegex
        } |
        ForEach-Object {
            $script:filesByPath[$_.FullName] = $_
            $script:relativeByPath[$_.FullName] = Join-Path "dev" $_.Name
        }
}

if ($Plan) {
    Write-Host "Essential drop plan"
    Write-Host "  RepoRoot : $RepoRoot"
    Write-Host "  DevRoot  : $DevRoot"
    Write-Host "  DropRoot : $DropRoot"
    Write-Host "  Files    : $($script:filesByPath.Count)"
    $script:filesByPath.Values |
        ForEach-Object { $script:relativeByPath[$_.FullName] } |
        ForEach-Object { ($_ -split '[\\/]')[0] } |
        Group-Object |
        Sort-Object Name |
        ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
    return
}

Ensure-Directory $DropRoot
Ensure-Directory $outDir

$manifestRows = New-Object System.Collections.Generic.List[object]
foreach ($file in $script:filesByPath.Values) {
    $relative = $script:relativeByPath[$file.FullName]
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
        Extension = $file.Extension.ToLowerInvariant()
        Bytes = $file.Length
        LastWriteTimeUtc = $file.LastWriteTimeUtc.ToString("o")
    }) | Out-Null
}

$manifestCsv = Join-Path $outDir "MANIFEST.csv"
$manifestTxt = Join-Path $outDir "MANIFEST.txt"
if ($PSCmdlet.ShouldProcess($manifestCsv, "Write manifest")) {
    $manifestRows | Sort-Object Relative | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $manifestCsv -WhatIf:$IsWhatIf
}
if ($PSCmdlet.ShouldProcess($manifestTxt, "Write summary")) {
    @(
        "DotTalk++ essential backup drop"
        "RepoRoot: $RepoRoot"
        "DevRoot: $DevRoot"
        "Drop: $outDir"
        "Created: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        "Files: $($manifestRows.Count)"
        "Excluded: builds, .git, repo-local drops, DBF/index/LMDB runtime data, logs/tmp, generated manual dist, node_modules, Next.js build output, old x64base-IIS copy"
        ""
        "Top-level counts:"
    ) | Out-File -FilePath $manifestTxt -Encoding utf8 -WhatIf:$IsWhatIf

    $manifestRows |
        Group-Object { ($_.Relative -split '[\\/]')[0] } |
        Sort-Object Name |
        ForEach-Object { "  $($_.Name): $($_.Count)" } |
        Out-File -FilePath $manifestTxt -Append -Encoding utf8 -WhatIf:$IsWhatIf
}

if ($Zip -and -not $IsWhatIf) {
    $zipPath = Join-Path $DropRoot ($dropName + ".zip")
    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    Compress-Archive -Path (Join-Path $outDir "*") -DestinationPath $zipPath -Force
}

Write-Host "Essential drop complete"
Write-Host "  RepoRoot : $RepoRoot"
Write-Host "  Drop     : $outDir"
Write-Host "  Files    : $($manifestRows.Count)"
if ($Zip -and -not $IsWhatIf) {
    Write-Host "  Zip      : $zipPath"
}
