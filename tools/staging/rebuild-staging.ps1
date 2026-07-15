<#
.SYNOPSIS
    Regenerate the disposable staging repo (C:\x64base) from development
    (D:\code\ccode) + PROMOTE.manifest.

.DESCRIPTION
    Staging is not precious. It is a build output: github/main (the published
    baseline) overlaid with development's current version of the promoted set.
    Because it is regenerated, an AI -- or anyone -- wiping C:\x64base costs
    nothing. Run this and it is back.

    THE RECIPE
        1. Ensure C:\x64base is a clean clone of github/main.
        2. Overlay every file matched by D:\code\ccode\PROMOTE.manifest,
           applying the .gitignore deny-list as a hard guard.
        3. You review the git diff, commit, and push.

    This script does the file work. It does NOT commit or push -- that stays a
    deliberate, reviewed human step. It also never touches development; the
    authority tree is read-only here.

    REPORT-ONLY by default. Copies nothing without -Execute.

.PARAMETER Fresh
    Reset the staging working tree to origin/main before overlaying (discards
    any uncommitted staging state -- which is fine, staging is disposable). Use
    after an AI has left staging in an unknown state.

.EXAMPLE
    .\tools\staging\rebuild-staging.ps1
    # report: what would be overlaid, and any deny-list violation

.EXAMPLE
    .\tools\staging\rebuild-staging.ps1 -Fresh -Execute
    # reset staging to main, overlay the manifest, ready to commit
#>

[CmdletBinding()]
param(
    [string] $Dev      = "D:\code\ccode",
    [string] $Staging  = "C:\x64base",
    [string] $Remote   = "https://github.com/deraldg/x64base.git",
    [string] $Branch   = "main",
    [switch] $Fresh,
    [switch] $Execute
)

$ErrorActionPreference = "Stop"

$dev = (Resolve-Path -LiteralPath $Dev).Path.TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $dev "PROMOTE.manifest"))) {
    throw "No PROMOTE.manifest in development root: $dev"
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
            git fetch origin $Branch
            git checkout $Branch
            git reset --hard "origin/$Branch"
            git clean -fdx -e ".git"    # remove untracked cruft an AI may have left
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

Write-Host "Overlaid $copied files ($mb MB) onto $Staging" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT -- review and publish (staging git, your call):" -ForegroundColor Cyan
Write-Host "  cd $Staging"
Write-Host "  git status --short"
Write-Host "  git add -A"
Write-Host "  git diff --cached --name-only | Select-String '\.cdx\.d|[/\\]lmdb[/\\]|\.mdb`$|[/\\]og[/\\]|\.exe`$'"
Write-Host "  #   ^ MUST print nothing"
Write-Host "  git commit -m '<what changed>'"
Write-Host "  git push origin $Branch"
