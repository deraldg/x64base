<#
.SYNOPSIS
  Safely sync tracked DotTalk++ source changes from a dev repo to a clean staging repo.

.DESCRIPTION
  This script is meant to replace extension-based copy/sync tools for the path:

      D:\code\ccode  -->  C:\dottalkpp

  It copies ONLY files that Git already tracks in the source repo by default.
  That means it will not accidentally pull in build outputs, runtime data,
  generated scripts, logs, _drops, third_party folders, or random .txt/.json files
  just because their extension matches.

  New untracked files are NOT copied unless you explicitly name them with
  -ExtraRelativePath.

  Default mode is PREVIEW ONLY. Nothing is copied or deleted unless -Apply is used.

.PARAMETER SourceRepo
  Developer repo. Default: D:\code\ccode

.PARAMETER StageRepo
  Clean staging repo. Default: C:\dottalkpp

.PARAMETER Apply
  Actually copy/delete files. Without this, preview only.

.PARAMETER MirrorTrackedDeletes
  If a tracked source file is missing/deleted in SourceRepo, delete the matching
  file in StageRepo. Without this, missing source files are reported but not deleted.

.PARAMETER ExtraRelativePath
  Explicit additional relative paths to copy, useful for intentional new files
  that are not yet tracked in SourceRepo. Example:
      -ExtraRelativePath src\cli\cmd_autodbf.cpp

.PARAMETER AllowDirtyStage
  By default, StageRepo must be clean before sync. Use this only if you know why.

.PARAMETER LogRoot
  External log/manifest folder. Default: sibling folder next to StageRepo:
      C:\dottalkpp_sync_logs

.EXAMPLE
  Preview tracked changes:
      pwsh .\sync_dottalk_dev_to_stage.ps1

.EXAMPLE
  Apply tracked changes:
      pwsh .\sync_dottalk_dev_to_stage.ps1 -Apply

.EXAMPLE
  Apply tracked changes and tracked deletes:
      pwsh .\sync_dottalk_dev_to_stage.ps1 -Apply -MirrorTrackedDeletes

.EXAMPLE
  Include one intentional new file:
      pwsh .\sync_dottalk_dev_to_stage.ps1 -Apply -ExtraRelativePath src\cli\cmd_autodbf.cpp
#>

[CmdletBinding()]
param(
    [string]$SourceRepo = "D:\code\ccode",
    [string]$StageRepo  = "C:\dottalkpp",

    [switch]$Apply,
    [switch]$MirrorTrackedDeletes,
    [string[]]$ExtraRelativePath = @(),
    [switch]$AllowDirtyStage,

    [string]$LogRoot
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory=$true)][string]$Repo,
        [Parameter(Mandatory=$true)][string[]]$GitArgs,
        [switch]$AllowFailure
    )

    $output = & git -C $Repo @GitArgs 2>&1
    $code = $LASTEXITCODE

    if ($code -ne 0 -and -not $AllowFailure) {
        Write-Host ""
        Write-Host "git -C $Repo $($GitArgs -join ' ') failed:" -ForegroundColor Red
        $output | ForEach-Object { Write-Host $_ }
        throw "Git command failed."
    }

    return @($output | ForEach-Object { "$_" })
}

function Resolve-GitRoot {
    param([Parameter(Mandatory=$true)][string]$Repo)
    if (!(Test-Path -LiteralPath $Repo)) {
        throw "Repo path does not exist: $Repo"
    }
    $root = (Invoke-Git -Repo $Repo -GitArgs @("rev-parse", "--show-toplevel"))[0]
    return (Resolve-Path -LiteralPath $root).Path
}

function Normalize-RelPath {
    param([Parameter(Mandatory=$true)][string]$Rel)
    $r = $Rel -replace "/", "\"
    $r = $r.Trim()
    while ($r.StartsWith(".\")) { $r = $r.Substring(2) }
    if ($r.Contains("..\")) {
        throw "Refusing relative path containing '..\': $Rel"
    }
    if ([System.IO.Path]::IsPathRooted($r)) {
        throw "Refusing rooted ExtraRelativePath: $Rel"
    }
    return $r
}

function Ensure-ParentDir {
    param([Parameter(Mandatory=$true)][string]$Path)
    $parent = Split-Path -Parent $Path
    if ($parent -and !(Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
}

function File-Bytes-Equal {
    param(
        [Parameter(Mandatory=$true)][string]$A,
        [Parameter(Mandatory=$true)][string]$B
    )
    if (!(Test-Path -LiteralPath $A -PathType Leaf)) { return $false }
    if (!(Test-Path -LiteralPath $B -PathType Leaf)) { return $false }

    $fa = Get-Item -LiteralPath $A
    $fb = Get-Item -LiteralPath $B
    if ($fa.Length -ne $fb.Length) { return $false }

    $ha = (Get-FileHash -Algorithm SHA256 -LiteralPath $A).Hash
    $hb = (Get-FileHash -Algorithm SHA256 -LiteralPath $B).Hash
    return ($ha -eq $hb)
}

if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git.exe was not found on PATH."
}

$SourceRepo = Resolve-GitRoot $SourceRepo
$StageRepo  = Resolve-GitRoot $StageRepo

if ($SourceRepo.TrimEnd('\') -ieq $StageRepo.TrimEnd('\')) {
    throw "SourceRepo and StageRepo resolve to the same path. Refusing to sync."
}

if (-not $LogRoot -or -not $LogRoot.Trim()) {
    $stageParent = Split-Path -Parent $StageRepo
    $LogRoot = Join-Path $stageParent "dottalkpp_sync_logs"
}
if (!(Test-Path -LiteralPath $LogRoot)) {
    New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$runLog = Join-Path $LogRoot ("sync_dev_to_stage_" + $timestamp)
New-Item -ItemType Directory -Force -Path $runLog | Out-Null

Write-Host "DotTalk++ dev-to-stage sync" -ForegroundColor Cyan
Write-Host "SourceRepo : $SourceRepo"
Write-Host "StageRepo  : $StageRepo"
Write-Host "Mode       : $(if ($Apply) { 'APPLY' } else { 'PREVIEW ONLY' })"
Write-Host "Run log    : $runLog"
Write-Host ""

$sourceBranch = Invoke-Git -Repo $SourceRepo -GitArgs @("status", "--short", "--branch")
$stageBranch  = Invoke-Git -Repo $StageRepo  -GitArgs @("status", "--short", "--branch")

$sourceHead = (Invoke-Git -Repo $SourceRepo -GitArgs @("rev-parse", "--short", "HEAD"))[0]
$stageHead  = (Invoke-Git -Repo $StageRepo  -GitArgs @("rev-parse", "--short", "HEAD"))[0]

Write-Host "Source HEAD: $sourceHead" -ForegroundColor Cyan
Write-Host "Stage HEAD : $stageHead" -ForegroundColor Cyan
Write-Host ""

$stageDirty = @($stageBranch | Where-Object { $_ -notmatch '^## ' })
if ($stageDirty.Count -gt 0 -and -not $AllowDirtyStage) {
    Write-Host "Stage repo is not clean:" -ForegroundColor Red
    $stageBranch | ForEach-Object { Write-Host $_ }
    Write-Host ""
    throw "Refusing to sync into dirty StageRepo. Clean/reset C:\dottalkpp first, or use -AllowDirtyStage deliberately."
}

# Tracked source file universe.
$trackedRaw = Invoke-Git -Repo $SourceRepo -GitArgs @("ls-files")
$trackedRel = @(
    $trackedRaw |
    Where-Object { $_ -and $_.Trim() -ne "" } |
    ForEach-Object { Normalize-RelPath $_ }
)

# Add explicit extras only.
$extraRel = @()
foreach ($e in $ExtraRelativePath) {
    if ($e -and $e.Trim()) {
        $extraRel += Normalize-RelPath $e
    }
}

$allRel = @($trackedRel + $extraRel | Sort-Object -Unique)

$copyList = New-Object System.Collections.Generic.List[object]
$sameList = New-Object System.Collections.Generic.List[object]
$missingSourceList = New-Object System.Collections.Generic.List[object]
$deleteList = New-Object System.Collections.Generic.List[object]
$missingExtraList = New-Object System.Collections.Generic.List[object]

foreach ($rel in $allRel) {
    $src = Join-Path $SourceRepo $rel
    $dst = Join-Path $StageRepo $rel
    $isExtra = $extraRel -contains $rel

    if (!(Test-Path -LiteralPath $src -PathType Leaf)) {
        if ($isExtra) {
            $missingExtraList.Add([PSCustomObject]@{ Relative = $rel; Source = $src; Destination = $dst }) | Out-Null
        } else {
            $missingSourceList.Add([PSCustomObject]@{ Relative = $rel; Source = $src; Destination = $dst }) | Out-Null
            if ($MirrorTrackedDeletes -and (Test-Path -LiteralPath $dst)) {
                $deleteList.Add([PSCustomObject]@{ Relative = $rel; Destination = $dst }) | Out-Null
            }
        }
        continue
    }

    if (File-Bytes-Equal -A $src -B $dst) {
        $sameList.Add([PSCustomObject]@{ Relative = $rel; Source = $src; Destination = $dst }) | Out-Null
    } else {
        $copyList.Add([PSCustomObject]@{ Relative = $rel; Source = $src; Destination = $dst; Extra = $isExtra }) | Out-Null
    }
}

# Write manifests before action.
$copyList | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runLog "copy_list.csv")
$sameList | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runLog "same_list.csv")
$missingSourceList | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runLog "missing_source_tracked.csv")
$deleteList | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runLog "delete_list.csv")
$missingExtraList | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $runLog "missing_extra.csv")
$sourceBranch | Set-Content -Encoding UTF8 -Path (Join-Path $runLog "source_status_before.txt")
$stageBranch  | Set-Content -Encoding UTF8 -Path (Join-Path $runLog "stage_status_before.txt")

@"
DotTalk++ dev-to-stage sync manifest
Timestamp: $timestamp
SourceRepo: $SourceRepo
StageRepo:  $StageRepo
SourceHead: $sourceHead
StageHead:  $stageHead
Apply:      $Apply
MirrorTrackedDeletes: $MirrorTrackedDeletes

Tracked source files considered: $($trackedRel.Count)
Explicit extra files requested:  $($extraRel.Count)
Files to copy/update:           $($copyList.Count)
Files already same:             $($sameList.Count)
Tracked source files missing:   $($missingSourceList.Count)
Stage files to delete:          $($deleteList.Count)
Missing explicit extras:        $($missingExtraList.Count)
"@ | Set-Content -Encoding UTF8 -Path (Join-Path $runLog "manifest.txt")

Write-Host "Plan:" -ForegroundColor Cyan
Write-Host "  tracked source files considered: $($trackedRel.Count)"
Write-Host "  explicit extras requested       : $($extraRel.Count)"
Write-Host "  files to copy/update            : $($copyList.Count)"
Write-Host "  files already same              : $($sameList.Count)"
Write-Host "  tracked source files missing    : $($missingSourceList.Count)"
Write-Host "  stage files to delete           : $($deleteList.Count)"
Write-Host "  missing explicit extras         : $($missingExtraList.Count)"
Write-Host ""

if ($missingExtraList.Count -gt 0) {
    Write-Host "Missing explicit extra files:" -ForegroundColor Red
    $missingExtraList | ForEach-Object { Write-Host "  $($_.Relative)" }
    throw "One or more -ExtraRelativePath files do not exist in SourceRepo."
}

if ($missingSourceList.Count -gt 0 -and -not $MirrorTrackedDeletes) {
    Write-Host "Tracked source files are missing/deleted in SourceRepo." -ForegroundColor Yellow
    Write-Host "They will NOT be deleted in StageRepo unless -MirrorTrackedDeletes is supplied."
    Write-Host "See: $(Join-Path $runLog 'missing_source_tracked.csv')"
    Write-Host ""
}

if (-not $Apply) {
    Write-Host "Preview complete. Nothing was changed." -ForegroundColor Yellow
    Write-Host "Inspect:"
    Write-Host "  $(Join-Path $runLog 'copy_list.csv')"
    Write-Host "  $(Join-Path $runLog 'delete_list.csv')"
    Write-Host ""
    Write-Host "Apply with:"
    Write-Host "  pwsh $PSCommandPath -SourceRepo `"$SourceRepo`" -StageRepo `"$StageRepo`" -Apply"
    exit 0
}

foreach ($row in $deleteList) {
    if (Test-Path -LiteralPath $row.Destination) {
        Remove-Item -LiteralPath $row.Destination -Force
    }
}

foreach ($row in $copyList) {
    Ensure-ParentDir -Path $row.Destination
    Copy-Item -LiteralPath $row.Source -Destination $row.Destination -Force
}

$stageAfter = Invoke-Git -Repo $StageRepo -GitArgs @("status", "--short", "--branch")
$stageAfter | Set-Content -Encoding UTF8 -Path (Join-Path $runLog "stage_status_after.txt")

Write-Host "Sync complete." -ForegroundColor Green
Write-Host "Stage status:"
$stageAfter | ForEach-Object { Write-Host $_ }
Write-Host ""
Write-Host "Run log:"
Write-Host "  $runLog"
