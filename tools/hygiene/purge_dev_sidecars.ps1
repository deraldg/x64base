<#
.SYNOPSIS
    Remove development-tree editing sidecars from D:\code\ccode.

.DESCRIPTION
    Maintainer-declared 2026-07-14:

      ".save files are a local trick of mine. I rename the file I am working on
       to .save and work on a copy I can compile with. If I screw up it's a fast
       recall. They can be removed. Things under backup, bak can go too."

    These artifacts are working state, never publishable, and were observed
    leaking into the C:\x64base staging repository as untracked noise.

    This script is REPORT-ONLY by default. It deletes nothing unless you pass
    -Execute. Per docs/agents/CURRENT_TARGET.md and the DotTalk++ mutation
    guard, a destructive pass must be preceded by a reviewed report pass.

    Safety properties:
      - Refuses to run outside the development root (never touches C:\x64base).
      - Never deletes a file that is TRACKED in git. If a sidecar was ever
        committed, it is reported and skipped -- removing it becomes a
        reviewed git operation, not a filesystem sweep.
      - Skips build output directories entirely.
      - Writes a manifest of everything it removed, so the pass is auditable
        and reversible from git history where applicable.

.PARAMETER Root
    Development root. Defaults to D:\code\ccode. Must be the dev tree.

.PARAMETER Execute
    Actually delete. Without this, the script only reports.

.EXAMPLE
    .\tools\hygiene\purge_dev_sidecars.ps1
    # report only -- shows what would go, deletes nothing

.EXAMPLE
    .\tools\hygiene\purge_dev_sidecars.ps1 -Execute
    # performs the deletion and writes a manifest
#>

[CmdletBinding()]
param(
    [string] $Root = "D:\code\ccode",
    [switch] $Execute
)

$ErrorActionPreference = "Stop"

# --- Guard: never run this against staging or anywhere but the dev tree ------
$resolved = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
if ($resolved -ieq "C:\x64base") {
    throw "REFUSING: C:\x64base is the clean staging repository, not a workspace. Sidecars are purged in the development tree and never promoted. See AI_PORTAL.md."
}
if ($resolved -inotlike "*\ccode") {
    throw "REFUSING: '$resolved' does not look like the development root (expected D:\code\ccode). Pass -Root explicitly if this is intentional."
}

Write-Host "Root:  $resolved"
Write-Host "Mode:  $(if ($Execute) { 'EXECUTE (destructive)' } else { 'REPORT-ONLY' })"
Write-Host ""

# --- Patterns ---------------------------------------------------------------
# Sidecar filename patterns. Anchored so we do not catch, say, a legitimate
# source file that merely contains the word 'backup'.
$namePatterns = @(
    '\.save$'            # working-copy trick: foo.cpp.save
    '\.SAVE$'
    '\.save\.txt$'
    '\.bak$'
    '\.bak_.*$'          # dotref.hpp.bak_phase5_dotref_curation_batch10
    '\.before_mdo_.*$'   # cmd_export.cpp.before_mdo_050
    '\.orig$'
    '\.rej$'
)
$nameRegex = ($namePatterns -join '|')

# Directories whose entire contents are disposable working state.
$dirPatterns = @(
    '\\backup\\'
    '\\\.backup-rename-cli\\'
)
$dirRegex = ($dirPatterns -join '|')

# Never descend into build output or vendored dependencies.
$excludeRegex = '\\(build|build-[^\\]+|\.git|node_modules|_deps|vcpkg_installed)\\'

# --- Collect ----------------------------------------------------------------
Write-Host "Scanning..."
$all = Get-ChildItem -LiteralPath $resolved -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch $excludeRegex } |
    Where-Object { $_.Name -match $nameRegex -or $_.FullName -match $dirRegex }

if (-not $all) {
    Write-Host "Nothing to do. No sidecars found."
    return
}

# --- Never delete anything git is tracking ----------------------------------
Push-Location $resolved
try {
    $tracked = @{}
    git ls-files | ForEach-Object {
        $tracked[(Join-Path $resolved ($_ -replace '/', '\')).ToLowerInvariant()] = $true
    }
} finally {
    Pop-Location
}

$toDelete = @()
$trackedHits = @()
foreach ($f in $all) {
    if ($tracked.ContainsKey($f.FullName.ToLowerInvariant())) {
        $trackedHits += $f
    } else {
        $toDelete += $f
    }
}

# --- Report -----------------------------------------------------------------
$bytes = ($toDelete | Measure-Object -Property Length -Sum).Sum
$mb    = if ($bytes) { [math]::Round($bytes / 1MB, 1) } else { 0 }

Write-Host ""
Write-Host "Disposable sidecars (untracked): $($toDelete.Count)  [$mb MB]"
Write-Host "Tracked in git -- SKIPPED:        $($trackedHits.Count)"
Write-Host ""

$toDelete |
    Group-Object { if ($_.Name -match '\.before_mdo_') { 'before_mdo snapshots' }
                   elseif ($_.Name -match '\.bak')     { 'bak sidecars' }
                   elseif ($_.Name -match '\.save|\.SAVE') { 'save working copies' }
                   elseif ($_.FullName -match $dirRegex)   { 'backup directories' }
                   else { 'other (orig/rej)' } } |
    Sort-Object Count -Descending |
    Format-Table @{L='Category';E={$_.Name}}, Count -AutoSize

if ($trackedHits.Count -gt 0) {
    Write-Warning "These sidecars are TRACKED in git and were NOT deleted."
    Write-Warning "Removing them is a reviewed git operation, not a filesystem sweep:"
    $trackedHits | Select-Object -First 20 | ForEach-Object {
        Write-Warning "  $($_.FullName.Substring($resolved.Length + 1))"
    }
    if ($trackedHits.Count -gt 20) { Write-Warning "  ... and $($trackedHits.Count - 20) more" }
    Write-Host ""
}

# --- Execute ----------------------------------------------------------------
if (-not $Execute) {
    Write-Host "REPORT-ONLY. Nothing deleted."
    Write-Host "Re-run with -Execute to remove the $($toDelete.Count) untracked sidecars above."
    return
}

$stamp    = Get-Date -Format "yyyyMMdd-HHmmss"
$manifest = Join-Path $resolved "docs\maintenance\SIDECAR_PURGE_$stamp.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $manifest) | Out-Null

$header = @(
    "Sidecar purge manifest"
    "Timestamp: $stamp"
    "Root:      $resolved"
    "Removed:   $($toDelete.Count) files, $mb MB"
    "Skipped:   $($trackedHits.Count) tracked files"
    "Authority: maintainer instruction 2026-07-14 (.save/.bak/backup are disposable)"
    ""
    "--- REMOVED ---"
)
$header | Set-Content -LiteralPath $manifest -Encoding UTF8

$removed = 0
foreach ($f in $toDelete) {
    try {
        $rel = $f.FullName.Substring($resolved.Length + 1)
        Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
        Add-Content -LiteralPath $manifest -Value $rel -Encoding UTF8
        $removed++
    } catch {
        Add-Content -LiteralPath $manifest -Value "FAILED: $rel -- $($_.Exception.Message)" -Encoding UTF8
        Write-Warning "Could not remove: $rel"
    }
}

# Remove now-empty backup directories, deepest first.
Get-ChildItem -LiteralPath $resolved -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match $dirRegex -and $_.FullName -notmatch $excludeRegex } |
    Sort-Object { $_.FullName.Length } -Descending |
    ForEach-Object {
        if (-not (Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue)) {
            Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
        }
    }

Write-Host ""
Write-Host "Removed $removed files ($mb MB)."
Write-Host "Manifest: $manifest"
Write-Host ""
Write-Host "Next: git status --short   (expect substantially reduced noise)"
