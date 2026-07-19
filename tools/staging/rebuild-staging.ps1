<#
.SYNOPSIS
    Regenerate the recoverable staging repo (C:\x64base) from its verified
    public baseline plus development's PROMOTE.manifest.

.DESCRIPTION
    Staging is a build output, but it is not assumed to be valueless. Its
    committed public baseline can contain packaging, download, build, and
    historical artifacts that are intentionally absent from development, and
    its dirty layer can contain not-yet-reconciled work. A destructive fresh
    rebuild therefore requires a verified offline recovery escrow.

    THE RECIPE
        1. Verify a recovery manifest containing the exact public baseline,
           dirty-worktree preservation, and publication plan.
        2. Ensure C:\x64base is a clean clone of github/main at that baseline.
        3. Overlay every file matched by D:\code\ccode\PROMOTE.manifest,
           applying the .gitignore deny-list as a hard guard.
        4. You review the git diff, commit, and push.

    This script does the file work. It does NOT commit or push -- that stays a
    deliberate, reviewed human step. It also never touches development; the
    authority tree is read-only here.

    REPORT-ONLY by default. Copies nothing without -Execute.

.PARAMETER Fresh
    Reset the staging working tree to origin/main before overlaying (discards
    the current working state). With -Execute, this is rejected unless
    -RecoveryManifest supplies a verified public-baseline escrow whose HEAD
    matches both staging and origin/main.

.PARAMETER RecoveryManifest
    Path to a dottalk.staging.public_baseline_escrow.v1 JSON manifest. Required
    for -Fresh -Execute. The bundle, archive, ledgers, dirty-state preservation,
    and Gate 5 overlay plan named by it are hash-verified before any reset.

.EXAMPLE
    .\tools\staging\rebuild-staging.ps1
    # report: what would be overlaid, and any deny-list violation

.EXAMPLE
.\tools\staging\rebuild-staging.ps1 -Fresh -Execute `
  -RecoveryManifest <public_baseline_escrow_manifest.json>
    # verify recovery, reset staging to main, overlay the manifest
#>

[CmdletBinding()]
param(
    [string] $Dev      = "D:\code\ccode",
    [string] $Staging  = "C:\x64base",
    [string] $Remote   = "https://github.com/deraldg/x64base.git",
    [string] $Branch   = "main",
    [string] $RecoveryManifest,
    [switch] $Fresh,
    [switch] $Execute
)

$ErrorActionPreference = "Stop"

$dev = (Resolve-Path -LiteralPath $Dev).Path.TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $dev "PROMOTE.manifest"))) {
    throw "No PROMOTE.manifest in development root: $dev"
}

function Get-VerifiedEscrow {
    param([string] $ManifestPath)

    if (-not $ManifestPath) {
        throw "-Fresh -Execute requires -RecoveryManifest; staging recovery must be proven before reset."
    }
    $resolved = (Resolve-Path -LiteralPath $ManifestPath).Path
    $escrow = Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json
    if ($escrow.schema -ne 'dottalk.staging.public_baseline_escrow.v1') {
        throw "Unsupported recovery manifest schema: $($escrow.schema)"
    }
    if ($escrow.status -ne 'RECOVERY_VERIFIED_RESET_AUTHORIZATION_SEPARATE') {
        throw "Recovery manifest is not in the verified recovery state: $($escrow.status)"
    }
    $base = Split-Path -Parent $resolved
    $checks = @(
        @($escrow.artifacts.archive, $escrow.artifacts.archive_sha256, 'archive'),
        @($escrow.artifacts.bundle, $escrow.artifacts.bundle_sha256, 'bundle'),
        @($escrow.artifacts.baseline_ledger, $escrow.artifacts.baseline_ledger_sha256, 'baseline ledger'),
        @($escrow.artifacts.public_only_ledger, $escrow.artifacts.public_only_ledger_sha256, 'public-only ledger'),
        @($escrow.artifacts.dirty_preservation, $escrow.artifacts.dirty_preservation_sha256, 'dirty-state preservation'),
        @($escrow.artifacts.gate5_overlay_plan, $escrow.artifacts.gate5_overlay_plan_sha256, 'Gate 5 overlay plan')
    )
    if ($escrow.artifacts.ignored_preservation) {
        $checks += ,@($escrow.artifacts.ignored_preservation, $escrow.artifacts.ignored_preservation_sha256, 'ignored-state preservation')
    }
    foreach ($check in $checks) {
        $path = Join-Path $base $check[0]
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Recovery $($check[2]) is missing: $path"
        }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
        if ($actual -ne $check[1]) {
            throw "Recovery $($check[2]) hash mismatch: expected $($check[1]), found $actual"
        }
    }

    $dirtyManifestPath = Join-Path $base $escrow.artifacts.dirty_preservation
    $dirtyManifest = Get-Content -LiteralPath $dirtyManifestPath -Raw | ConvertFrom-Json
    if ($dirtyManifest.schema -ne 'dottalk.staging.dirty_worktree_preservation.v1') {
        throw "Unsupported dirty-state preservation schema: $($dirtyManifest.schema)"
    }
    $dirtyRoot = Split-Path -Parent $dirtyManifestPath
    $dirtyLedgerPath = Join-Path $dirtyRoot $dirtyManifest.file_manifest
    $dirtyLedgerHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $dirtyLedgerPath).Hash
    if ($dirtyLedgerHash -ne $dirtyManifest.file_manifest_sha256) {
        throw "Dirty-state file ledger hash mismatch."
    }
    $dirtyRows = @(Import-Csv -LiteralPath $dirtyLedgerPath)
    if ($dirtyRows.Count -ne $dirtyManifest.dirty_paths) {
        throw "Dirty-state row count mismatch: expected $($dirtyManifest.dirty_paths), found $($dirtyRows.Count)"
    }
    foreach ($row in $dirtyRows) {
        $backup = Join-Path $dirtyRoot $row.backup_path
        $backupHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $backup).Hash
        if ($backupHash -ne $row.backup_sha256) {
            throw "Dirty-state backup hash mismatch: $($row.path)"
        }
    }

    $publicOnlyPath = Join-Path $base $escrow.artifacts.public_only_ledger
    $publicOnlyRows = @(Import-Csv -LiteralPath $publicOnlyPath)
    if ($publicOnlyRows.Count -ne $escrow.counts.public_baseline_only) {
        throw "Public-baseline-only row count mismatch."
    }

    $ignoredRoot = $null
    $ignoredRows = @()
    if ($escrow.artifacts.ignored_preservation) {
        $ignoredManifestPath = Join-Path $base $escrow.artifacts.ignored_preservation
        $ignoredManifest = Get-Content -LiteralPath $ignoredManifestPath -Raw | ConvertFrom-Json
        if ($ignoredManifest.schema -ne 'dottalk.staging.ignored_worktree_preservation.v1') {
            throw "Unsupported ignored-state preservation schema: $($ignoredManifest.schema)"
        }
        $ignoredRoot = Split-Path -Parent $ignoredManifestPath
        $ignoredLedgerPath = Join-Path $ignoredRoot $ignoredManifest.file_manifest
        $ignoredLedgerHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ignoredLedgerPath).Hash
        if ($ignoredLedgerHash -ne $ignoredManifest.file_manifest_sha256) {
            throw "Ignored-state file ledger hash mismatch."
        }
        $ignoredRows = @(Import-Csv -LiteralPath $ignoredLedgerPath)
        if ($ignoredRows.Count -ne $ignoredManifest.ignored_files) {
            throw "Ignored-state row count mismatch."
        }
        foreach ($row in $ignoredRows) {
            $backup = Join-Path $ignoredRoot $row.backup_path
            if ((Get-FileHash -Algorithm SHA256 -LiteralPath $backup).Hash -ne $row.backup_sha256) {
                throw "Ignored-state backup hash mismatch: $($row.path)"
            }
        }
    }

    return [pscustomobject]@{
        Manifest = $escrow
        Path = $resolved
        DirtyRoot = $dirtyRoot
        DirtyRows = $dirtyRows
        IgnoredRoot = $ignoredRoot
        IgnoredRows = $ignoredRows
        PublicOnlyRows = $publicOnlyRows
    }
}

$verifiedEscrow = $null
if ($Fresh -and $Execute) {
    $verifiedEscrow = Get-VerifiedEscrow -ManifestPath $RecoveryManifest
    if (-not (Test-Path -LiteralPath (Join-Path $Staging '.git'))) {
        throw "Recovery-bound -Fresh requires the existing staging Git repository for HEAD verification."
    }
    $gitSafeDirectory = $Staging.Replace('\', '/')
    $currentHead = git -c "safe.directory=$gitSafeDirectory" -C $Staging rev-parse HEAD
    if ($currentHead -ne $verifiedEscrow.Manifest.head) {
        throw "Staging HEAD does not match recovery manifest: expected $($verifiedEscrow.Manifest.head), found $currentHead"
    }
    Write-Host "Recovery escrow verified: $($verifiedEscrow.Path)" -ForegroundColor Green
    Write-Host "Recovery baseline:        $currentHead" -ForegroundColor Green
}

Write-Host "Development (read-only): $dev"
Write-Host "Staging (rebuild):       $Staging"
Write-Host "Mode:                    $(if ($Execute) { 'EXECUTE' } else { 'REPORT-ONLY' })"
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Baseline: staging must be a clone of github/<branch>.
# ---------------------------------------------------------------------------
$hasGit = Test-Path -LiteralPath (Join-Path $Staging ".git")

if (-not $hasGit) {
    Write-Host "Staging has no .git -- it must be cloned from the remote." -ForegroundColor Yellow
    Write-Host "  git clone $Remote `"$Staging`""
    if ($Execute) {
        if (Test-Path -LiteralPath $Staging) {
            throw "$Staging exists but is not a git repo. Move or remove it, then re-run; the script will not overwrite an unknown directory."
        }
        git clone $Remote $Staging
    } else {
        Write-Host "  (report-only: not cloned)"
        Write-Host ""
        Write-Host "Re-run with -Execute to clone, or clone by hand, then re-run." -ForegroundColor Yellow
        # Continue into the manifest report so you can still see the plan.
    }
} elseif ($Fresh) {
    Write-Host "-Fresh: resetting staging working tree to origin/$Branch (discards uncommitted staging state)." -ForegroundColor Yellow
    if ($Execute) {
        Push-Location $Staging
        try {
            git -c "safe.directory=$gitSafeDirectory" fetch origin $Branch
            $fetchedHead = git -c "safe.directory=$gitSafeDirectory" rev-parse "origin/$Branch"
            if ($fetchedHead -ne $verifiedEscrow.Manifest.head) {
                throw "Fetched origin/$Branch moved beyond the recovery baseline. Create a new escrow before reset. Expected $($verifiedEscrow.Manifest.head), found $fetchedHead"
            }
            git -c "safe.directory=$gitSafeDirectory" checkout $Branch
            git -c "safe.directory=$gitSafeDirectory" reset --hard "origin/$Branch"
            git -c "safe.directory=$gitSafeDirectory" clean -fdx -e ".git"    # remove untracked cruft an AI may have left

            $restoredDirty = 0
            foreach ($row in $verifiedEscrow.DirtyRows) {
                $src = Join-Path $verifiedEscrow.DirtyRoot $row.backup_path
                $dst = Join-Path $Staging $row.path
                $dstDir = Split-Path -Parent $dst
                if (-not (Test-Path -LiteralPath $dstDir)) {
                    New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
                }
                Copy-Item -LiteralPath $src -Destination $dst -Force
                $restoredDirty++
            }
            Write-Host "Restored $restoredDirty preserved dirty-layer files before publication overlay." -ForegroundColor Green

            $restoredIgnored = 0
            foreach ($row in $verifiedEscrow.IgnoredRows) {
                $src = Join-Path $verifiedEscrow.IgnoredRoot $row.backup_path
                $dst = Join-Path $Staging $row.path
                $dstDir = Split-Path -Parent $dst
                if (-not (Test-Path -LiteralPath $dstDir)) {
                    New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
                }
                Copy-Item -LiteralPath $src -Destination $dst -Force
                $restoredIgnored++
            }
            Write-Host "Restored $restoredIgnored preserved ignored-layer files before publication overlay." -ForegroundColor Green
        } finally { Pop-Location }
    } else {
        Write-Host "  (report-only: not reset)"
    }
}

# ---------------------------------------------------------------------------
# 2. Read the manifest, expand globs against development.
# ---------------------------------------------------------------------------
$manifest = Get-Content -LiteralPath (Join-Path $dev "PROMOTE.manifest") |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ -and -not $_.StartsWith('#') }

# The .gitignore deny-list, as a hard guard. Mirrors the patterns that must
# never publish, regardless of what a manifest glob happens to sweep in.
$deny = '(\.cdx\.d[\\/])|([\\/]lmdb[\\/])|([\\/]og[\\/])|(\.exe$)|([\\/]backups?[\\/])|(\.bak)|(\.save)|(\.before_mdo_)|(\.mdb$)|([\\/]zz_)|([\\/]table\.cnx$)|([\\/]table\.cdx$)|(mixed\.workspace)'

$plan   = New-Object System.Collections.ArrayList
$misses = New-Object System.Collections.ArrayList

foreach ($entry in $manifest) {
    $full = Join-Path $dev $entry
    $hits = @(Get-ChildItem -Path $full -File -Recurse:$false -ErrorAction SilentlyContinue)
    # '**' or directory entries: recurse
    if ($entry -match '\*\*' -or (Test-Path -LiteralPath $full -PathType Container)) {
        $hits = @(Get-ChildItem -Path $full -File -Recurse -ErrorAction SilentlyContinue)
    }
    if (-not $hits) { [void]$misses.Add($entry); continue }
    foreach ($h in $hits) {
        $rel = $h.FullName.Substring($dev.Length + 1)
        if ($rel -match $deny) { continue }   # guard: never publish
        [void]$plan.Add([pscustomobject]@{ Rel = $rel; Bytes = $h.Length })
    }
}

$plan = @($plan | Sort-Object Rel -Unique)

# ---------------------------------------------------------------------------
# Hard guard: nothing deny-listed may survive.
# ---------------------------------------------------------------------------
$leak = @($plan | Where-Object { $_.Rel -match $deny })
if ($leak.Count) {
    $leak | ForEach-Object { Write-Error "DENY-LIST LEAK: $($_.Rel)" }
    throw "Refusing to overlay: deny-list guard caught $($leak.Count) file(s)."
}

# ---------------------------------------------------------------------------
# 3. Report / execute the overlay.
# ---------------------------------------------------------------------------
$mb = [math]::Round((($plan | Measure-Object Bytes -Sum).Sum) / 1MB, 2)
Write-Host ""
Write-Host "Overlay plan: $($plan.Count) files, $mb MB" -ForegroundColor Cyan
$plan | Group-Object { ($_.Rel -split '[\\/]')[0] } | Sort-Object Count -Desc |
    Format-Table @{L='Top-level';E={$_.Name}}, Count -AutoSize | Out-String | Write-Host

if ($misses.Count) {
    Write-Warning "Manifest entries that matched nothing in development:"
    $misses | ForEach-Object { Write-Warning "    $_" }
    Write-Host ""
}

if (-not $Execute) {
    Write-Host "REPORT-ONLY. Nothing copied. Re-run with -Execute." -ForegroundColor Yellow
    return
}

if (-not (Test-Path -LiteralPath (Join-Path $Staging ".git"))) {
    throw "Staging is not a git clone yet. Re-run with -Execute after the clone step, or clone by hand."
}

$copied = 0
foreach ($item in $plan) {
    $src = Join-Path $dev     $item.Rel
    $dst = Join-Path $Staging $item.Rel
    $dir = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $copied++
}

$publicOnlyFindings = @()
if ($verifiedEscrow) {
    foreach ($row in $verifiedEscrow.PublicOnlyRows) {
        $path = Join-Path $Staging $row.path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            $publicOnlyFindings += "MISSING $($row.path)"
            continue
        }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
        if ($actual -ne $row.baseline_sha256) {
            $publicOnlyFindings += "DRIFT $($row.path)"
        }
    }
}
if ($publicOnlyFindings.Count) {
    $publicOnlyFindings | ForEach-Object { Write-Error "PUBLIC-BASELINE RECOVERY FAILURE: $_" }
    throw "Public-baseline-only verification failed for $($publicOnlyFindings.Count) file(s)."
}

Write-Host "Overlaid $copied files ($mb MB) onto $Staging" -ForegroundColor Green
if ($verifiedEscrow) {
    Write-Host "Verified $($verifiedEscrow.PublicOnlyRows.Count) public-baseline-only files after overlay." -ForegroundColor Green
}
Write-Host ""
Write-Host "NEXT -- review and publish (staging git, your call):" -ForegroundColor Cyan
Write-Host "  cd $Staging"
Write-Host "  git status --short"
Write-Host "  git add -A"
Write-Host "  git diff --cached --name-only | Select-String '\.cdx\.d|[/\\]lmdb[/\\]|\.mdb`$|[/\\]og[/\\]|\.exe`$'"
Write-Host "  #   ^ MUST print nothing"
Write-Host "  git commit -m '<what changed>'"
Write-Host "  git push origin $Branch"
