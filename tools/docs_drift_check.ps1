param(
    [string]$IndexPath = "docs/DOC_AUTHORITY_INDEX.json",
    [switch]$Json,
    [switch]$FailOnDrift
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Resolve-RepoPath {
    param(
        [string]$RepoRoot,
        [string]$RelativePath
    )

    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        return $RelativePath
    }
    return (Join-Path $RepoRoot $RelativePath)
}

function Resolve-AuthorityPath {
    param(
        [string]$RepoRoot,
        [pscustomobject]$Index,
        [string]$RelativeOrAbsolutePath,
        [string]$RootKey = "repo_root"
    )

    if ([string]::IsNullOrWhiteSpace($RelativeOrAbsolutePath)) {
        return ""
    }

    if ([System.IO.Path]::IsPathRooted($RelativeOrAbsolutePath)) {
        return $RelativeOrAbsolutePath
    }

    $rootValue = $null
    if ($Index.PSObject.Properties.Name -contains "roots" -and $Index.roots) {
        $rootValue = $Index.roots.$RootKey
    }

    if ([string]::IsNullOrWhiteSpace($rootValue)) {
        $rootValue = "."
    }

    if ([System.IO.Path]::IsPathRooted([string]$rootValue)) {
        return (Join-Path ([string]$rootValue) $RelativeOrAbsolutePath)
    }

    return (Join-Path (Join-Path $RepoRoot ([string]$rootValue)) $RelativeOrAbsolutePath)
}

function Add-Finding {
    param(
        [System.Collections.Generic.List[object]]$Findings,
        [string]$LaneId,
        [string]$Severity,
        [string]$Code,
        [string]$Message,
        [string]$Path = ""
    )

    $Findings.Add([pscustomobject]@{
        lane_id   = $LaneId
        severity  = $Severity
        code      = $Code
        message   = $Message
        path      = $Path
    }) | Out-Null
}

$repoRoot = Get-RepoRoot
$indexAbsolute = Resolve-RepoPath -RepoRoot $repoRoot -RelativePath $IndexPath
if (-not (Test-Path -LiteralPath $indexAbsolute)) {
    throw "Authority index not found: $indexAbsolute"
}

$index = Get-Content -LiteralPath $indexAbsolute -Raw | ConvertFrom-Json
$findings = [System.Collections.Generic.List[object]]::new()
$summaries = [System.Collections.Generic.List[object]]::new()

foreach ($lane in $index.lanes) {
    $laneId = [string]$lane.id
    switch ([string]$lane.kind) {
        "primary_reader_publication" {
            $pointerPath = Resolve-AuthorityPath -RepoRoot $repoRoot -Index $index -RelativeOrAbsolutePath $lane.active_pointer_path
            $pointerMetadataPath = Resolve-AuthorityPath -RepoRoot $repoRoot -Index $index -RelativeOrAbsolutePath $lane.active_pointer_metadata_path
            $manifestPath = Resolve-AuthorityPath -RepoRoot $repoRoot -Index $index -RelativeOrAbsolutePath $lane.accepted_manifest_path
            $canonicalPath = Resolve-AuthorityPath -RepoRoot $repoRoot -Index $index -RelativeOrAbsolutePath $lane.canonical_publication_path

            if (-not (Test-Path -LiteralPath $pointerPath)) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "POINTER_MISSING" -Message "Active pointer file is missing." -Path $pointerPath
                continue
            }
            if (-not (Test-Path -LiteralPath $pointerMetadataPath)) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "POINTER_METADATA_MISSING" -Message "Primary reader metadata file is missing." -Path $pointerMetadataPath
                continue
            }
            if (-not (Test-Path -LiteralPath $manifestPath)) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "MANIFEST_MISSING" -Message "Accepted manifest is missing." -Path $manifestPath
                continue
            }
            if (-not (Test-Path -LiteralPath $canonicalPath)) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "CANONICAL_PUBLICATION_MISSING" -Message "Canonical publication path is missing." -Path $canonicalPath
                continue
            }

            $pointerTargetRelative = (Get-Content -LiteralPath $pointerPath -Raw).Trim()
            $metadata = Get-Content -LiteralPath $pointerMetadataPath -Raw | ConvertFrom-Json
            $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

            $actualHash = (Get-FileHash -LiteralPath $canonicalPath -Algorithm $lane.hash_algorithm).Hash.ToLowerInvariant()
            $actualLines = (Get-Content -LiteralPath $canonicalPath | Measure-Object -Line).Lines
            $actualHeadingCount = (rg -n '^#' $canonicalPath | Measure-Object).Count
            $actualFirstHeading = ((Get-Content -LiteralPath $canonicalPath -TotalCount 1).TrimStart('#', ' ')).Trim()
            $canonicalAbsoluteNormalized = (Resolve-Path -LiteralPath $canonicalPath).Path

            if ($pointerTargetRelative -ne [string]$lane.canonical_publication_path) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "POINTER_TARGET_MISMATCH" -Message "Active pointer target does not match canonical publication path." -Path $pointerPath
            }

            if ($metadata.primary_reader_artifact -ne [string]$lane.canonical_publication_path) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "POINTER_METADATA_TARGET_MISMATCH" -Message "Primary reader metadata points to a different artifact than the authority index." -Path $pointerMetadataPath
            }

            if ([string]$metadata.artifact_sha256 -ne $actualHash) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "POINTER_METADATA_HASH_MISMATCH" -Message "Primary reader metadata hash does not match the current canonical publication." -Path $pointerMetadataPath
            }

            if ([int]$metadata.artifact_lines -ne [int]$actualLines) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "POINTER_METADATA_LINECOUNT_MISMATCH" -Message "Primary reader metadata line count does not match the current canonical publication." -Path $pointerMetadataPath
            }

            if ([int]$metadata.artifact_heading_count -ne [int]$actualHeadingCount) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "POINTER_METADATA_HEADINGCOUNT_MISMATCH" -Message "Primary reader metadata heading count does not match the current canonical publication." -Path $pointerMetadataPath
            }

            if ([string]$metadata.first_heading -ne [string]$lane.expected_first_heading) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "POINTER_METADATA_FIRST_HEADING_MISMATCH" -Message "Primary reader metadata first heading does not match the authority index." -Path $pointerMetadataPath
            }

            if ($actualFirstHeading -ne [string]$lane.expected_first_heading) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "CANONICAL_FIRST_HEADING_MISMATCH" -Message "Canonical publication first heading does not match the authority index." -Path $canonicalPath
            }

            if ($lane.check_manifest_current_reference -and ([string]$manifest.current_reference_combined -ne $canonicalAbsoluteNormalized)) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "MANIFEST_CURRENT_REFERENCE_MISMATCH" -Message "Accepted manifest current_reference_combined does not match the canonical publication." -Path $manifestPath
            }

            if ($lane.check_manifest_current_reference_hash -and ([string]$manifest.current_reference_sha256).ToLowerInvariant() -ne $actualHash) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "MANIFEST_CURRENT_REFERENCE_HASH_MISMATCH" -Message "Accepted manifest current_reference_sha256 does not match the canonical publication." -Path $manifestPath
            }

            $summaries.Add([pscustomobject]@{
                lane_id               = $laneId
                kind                  = $lane.kind
                canonical_publication = $lane.canonical_publication_path
                current_hash          = $actualHash
                current_lines         = $actualLines
                current_heading_count = $actualHeadingCount
                current_first_heading = $actualFirstHeading
            }) | Out-Null
        }
        "text_expectation" {
            $targetPath = Resolve-AuthorityPath -RepoRoot $repoRoot -Index $index -RelativeOrAbsolutePath $lane.target_path -RootKey ([string]$lane.target_root_key)
            if (-not (Test-Path -LiteralPath $targetPath)) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "TARGET_MISSING" -Message "Expected text target is missing." -Path $targetPath
                continue
            }

            $content = Get-Content -LiteralPath $targetPath -Raw
            foreach ($needle in @($lane.required_contains)) {
                if ($content -notlike "*$needle*") {
                    Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "REQUIRED_TEXT_MISSING" -Message "Required text is missing: $needle" -Path $targetPath
                }
            }
            foreach ($needle in @($lane.forbidden_contains)) {
                if (-not [string]::IsNullOrWhiteSpace([string]$needle) -and $content -like "*$needle*") {
                    Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "FORBIDDEN_TEXT_PRESENT" -Message "Forbidden text is present: $needle" -Path $targetPath
                }
            }

            $summaries.Add([pscustomobject]@{
                lane_id      = $laneId
                kind         = $lane.kind
                target_path  = $targetPath
                required_cnt = @($lane.required_contains).Count
            }) | Out-Null
        }
        "download_bundle" {
            $bundleRootPath = Resolve-AuthorityPath -RepoRoot $repoRoot -Index $index -RelativeOrAbsolutePath $lane.bundle_root_path -RootKey ([string]$lane.bundle_root_key)
            $bundleManifestPath = Resolve-AuthorityPath -RepoRoot $repoRoot -Index $index -RelativeOrAbsolutePath $lane.bundle_manifest_path -RootKey ([string]$lane.bundle_manifest_root_key)

            if (-not (Test-Path -LiteralPath $bundleRootPath)) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "BUNDLE_ROOT_MISSING" -Message "Bundle root path is missing." -Path $bundleRootPath
                continue
            }
            if (-not (Test-Path -LiteralPath $bundleManifestPath)) {
                Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "BUNDLE_MANIFEST_MISSING" -Message "Bundle manifest is missing." -Path $bundleManifestPath
                continue
            }

            $bundleManifest = Get-Content -LiteralPath $bundleManifestPath -Raw | ConvertFrom-Json
            $manifestItems = @($bundleManifest.items)
            $itemNames = @($manifestItems | ForEach-Object { $_.file })

            foreach ($requiredItem in @($lane.required_items)) {
                if ($itemNames -notcontains $requiredItem) {
                    Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "BUNDLE_REQUIRED_ITEM_MISSING" -Message "Required bundle manifest item is missing: $requiredItem" -Path $bundleManifestPath
                }
            }

            foreach ($item in $manifestItems) {
                $bundleFilePath = Join-Path $bundleRootPath ([string]$item.file)
                $sourcePath = Resolve-AuthorityPath -RepoRoot $repoRoot -Index $index -RelativeOrAbsolutePath ([string]$item.source)

                if (-not (Test-Path -LiteralPath $bundleFilePath)) {
                    Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "BUNDLE_FILE_MISSING" -Message "Bundled file is missing: $($item.file)" -Path $bundleFilePath
                    continue
                }
                if (-not (Test-Path -LiteralPath $sourcePath)) {
                    Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "BUNDLE_SOURCE_MISSING" -Message "Source-side artifact is missing for bundled file: $($item.file)" -Path $sourcePath
                    continue
                }

                $bundleHash = (Get-FileHash -LiteralPath $bundleFilePath -Algorithm SHA256).Hash.ToLowerInvariant()
                $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
                if ($bundleHash -ne $sourceHash) {
                    Add-Finding -Findings $findings -LaneId $laneId -Severity "ERROR" -Code "BUNDLE_HASH_MISMATCH" -Message "Bundled file does not match source-side artifact: $($item.file)" -Path $bundleFilePath
                }
            }

            $summaries.Add([pscustomobject]@{
                lane_id       = $laneId
                kind          = $lane.kind
                bundle_root   = $bundleRootPath
                manifest_path = $bundleManifestPath
                item_count    = $manifestItems.Count
            }) | Out-Null
        }
        default {
            Add-Finding -Findings $findings -LaneId $laneId -Severity "WARN" -Code "UNKNOWN_LANE_KIND" -Message "Unknown lane kind '$($lane.kind)' was skipped."
        }
    }
}

$errorCount = @($findings | Where-Object { $_.severity -eq "ERROR" }).Count
$warningCount = @($findings | Where-Object { $_.severity -eq "WARN" }).Count
$result = [pscustomobject]@{
    repo_root      = $repoRoot
    authority_index = $IndexPath
    lane_count     = @($index.lanes).Count
    error_count    = $errorCount
    warning_count  = $warningCount
    summaries      = $summaries
    findings       = $findings
}

if ($Json) {
    $result | ConvertTo-Json -Depth 6
} else {
    Write-Host "DOC DRIFT CHECK"
    Write-Host "  Repo root   : $repoRoot"
    Write-Host "  Authority   : $IndexPath"
    Write-Host "  Lanes       : $(@($index.lanes).Count)"
    Write-Host "  Errors      : $errorCount"
    Write-Host "  Warnings    : $warningCount"
    Write-Host ""

    foreach ($summary in $summaries) {
        Write-Host "Lane: $($summary.lane_id)"
        Write-Host "  Publication : $($summary.canonical_publication)"
        Write-Host "  Hash        : $($summary.current_hash)"
        Write-Host "  Lines       : $($summary.current_lines)"
        Write-Host "  Headings    : $($summary.current_heading_count)"
        Write-Host "  First #     : $($summary.current_first_heading)"
        Write-Host ""
    }

    if ($findings.Count -gt 0) {
        Write-Host "Findings:"
        $findings | ForEach-Object {
            Write-Host "  [$($_.severity)] $($_.code): $($_.message)"
            if ($_.path) {
                Write-Host "    Path: $($_.path)"
            }
        }
    } else {
        Write-Host "No authority drift detected."
    }
}

if ($FailOnDrift -and $errorCount -gt 0) {
    exit 1
}
