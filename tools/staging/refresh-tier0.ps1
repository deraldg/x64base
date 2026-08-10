# refresh-tier0.ps1 -- regenerate labtalk/ai_portal/TIER0_STATE.md so its stamped
# HEAD matches the current HEAD (fixes the "generated but never regenerated" drift,
# critique F-2). The generator is pure Python (stdlib only) -- no engine build.
#
#   .\tools\staging\refresh-tier0.ps1                       # regenerate now
#   .\tools\staging\refresh-tier0.ps1 -InstallHook          # + pre-commit auto-refresh
#   .\tools\staging\refresh-tier0.ps1 -Python "C:\py\python.exe"   # force an interpreter
#
# -InstallHook appends (or REPLACES, if already present) an idempotent block in
# .git/hooks/pre-commit that regenerates + stages Tier 0 on every commit. It does
# not clobber an existing hook (e.g. prepush_gate's); it lives in a marked region.

param([switch]$InstallHook, [string]$Python)
$ErrorActionPreference = 'Stop'

$repo = 'D:\code\ccode'
Set-Location -LiteralPath $repo

# --- pick a Python that ACTUALLY RUNS (not just one whose launcher exists) -------
function Test-Py([string]$cmd) {
  try { & ([scriptblock]::Create("$cmd --version")) *> $null; return ($LASTEXITCODE -eq 0) }
  catch { return $false }
}
$candidates = @()
if ($Python) { $candidates += "`"$Python`"" }
$candidates += @(
  "`"$repo\.venv312\Scripts\python.exe`"",
  "`"$repo\build-labtalk\vcpkg_installed\x64-windows\tools\python3\python.exe`"",
  'python', 'python3', 'py -3', 'py'
)
$py = $null
foreach ($c in $candidates) { if (Test-Py $c) { $py = $c; break } }
if (-not $py) { throw 'No working Python found. Pass -Python "C:\path\to\python.exe".' }
Write-Host "python : $py"

$gen = 'labtalk\ai_portal\generate_tier0_state.py'
if (-not (Test-Path $gen)) { throw "generator not found: $gen" }
$head = (git rev-parse --short HEAD).Trim()
Write-Host "HEAD   : $head"

# --- regenerate ------------------------------------------------------------------
& ([scriptblock]::Create("$py `"$gen`" --write"))
if ($LASTEXITCODE -ne 0) { throw "generator failed (exit $LASTEXITCODE)." }

# --- verify the stamp now matches HEAD -------------------------------------------
$stateFile = 'labtalk\ai_portal\TIER0_STATE.md'
$m = Select-String -Path $stateFile -Pattern 'HEAD\s*:\s*([0-9a-f]{7,})' | Select-Object -First 1
$stamped = if ($m) { $m.Matches.Groups[1].Value } else { '(none)' }
if ($stamped -and ($head.StartsWith($stamped) -or $stamped.StartsWith($head))) {
  Write-Host "OK: TIER0_STATE.md now stamped at $stamped (matches HEAD)." -ForegroundColor Green
} else {
  Write-Host "WARN: stamped '$stamped' != HEAD '$head' -- inspect generator output." -ForegroundColor Yellow
}

# --- optional: wire the pre-commit auto-refresh ----------------------------------
if ($InstallHook) {
  $hook = Join-Path $repo '.git\hooks\pre-commit'
  $begin = '# >>> tier0-refresh >>>'
  $end   = '# <<< tier0-refresh <<<'
  # POSIX sh hook: forward slashes, and a shell-usable python invocation.
  $pyForHook = ($py -replace '\\','/')
  $genFwd    = 'labtalk/ai_portal/generate_tier0_state.py'
  # The refresh must ANNOUNCE itself when it stages a change: a silent add here
  # put an unexplained third file into cf5caa7bb (2026-08-10) and was initially
  # misread as another session's stray staging. By design it rides the commit;
  # by design it now says so.
  $block = @"
$begin
$pyForHook "$genFwd" --write >/dev/null 2>&1 || true
git add labtalk/ai_portal/TIER0_STATE.md >/dev/null 2>&1 || true
git diff --cached --quiet -- labtalk/ai_portal/TIER0_STATE.md 2>/dev/null || echo "tier0-refresh: TIER0_STATE.md regenerated -- rides in this commit (by design)"
$end
"@
  if (-not (Test-Path $hook)) { "#!/bin/sh`n" | Set-Content -Encoding ascii $hook }
  $text = Get-Content -Raw $hook
  # Match ANY prior tier0-refresh block (old or new begin marker) so a stale one is
  # replaced, never duplicated. Old marker had a "(refresh-tier0.ps1)" suffix.
  $detect = '(?s)# >>> tier0-refresh.*?# <<< tier0-refresh <<<'
  if ($text -match $detect) {
    $text = [regex]::Replace($text, $detect, { param($x) $block })
    Set-Content -Encoding ascii $hook $text
    Write-Host "hook   : replaced the existing tier0-refresh block (working Python, POSIX sh)." -ForegroundColor Green
  } else {
    Add-Content -Encoding ascii $hook "`n$block"
    Write-Host "hook   : appended tier0-refresh to .git/hooks/pre-commit." -ForegroundColor Green
  }
  Write-Host "         (Hooks are not version-controlled; re-run -InstallHook per clone/worktree.)"
}

Write-Host "`nDone. Review 'git diff -- $stateFile', then commit it (or let the hook stage it)."
