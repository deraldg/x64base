# start-ai.ps1 -- bring up the local AI views + maintenance console on :3000.
#
# Companion to tools/reports/run_reports.py. The difference that matters:
# run_reports REUSES whatever already listens on :3000 / :3002, so a stale
# `next dev` on :3000 gets adopted AS the gateway and /AI/ + /AI/console 404.
# This script FREES those ports first, so the gateway always really starts.
#
# What it does, in order:
#   1. free ports 3000 / 3002 / 8770 (stop any stale listener)
#   2. start the website on :3002                      (its own window)
#         default   : `next dev`  -- live editing/HMR; site SEARCH does NOT work
#                     (Pagefind has no index under dev)
#         -Built    : `npm run build` + `serve out` -- production-like; SEARCH WORKS
#   3. start the reports gateway on :3000              (its own window, writes ON)
#         -> /AI/         live reports, rebuilt per request (needs pyyaml -> venv)
#         -> /AI/console  maintenance UI (--enable-write allows Execute)
#         -> everything else proxied to :3002 (so /search rides the built site)
#   4. open http://localhost:3000/AI/console
#
# Stop everything by closing the two spawned windows (or Ctrl+C in each).
#
# Run:
#   powershell -ExecutionPolicy Bypass -File <repo>\start-ai.ps1            (dev)
#   powershell -ExecutionPolicy Bypass -File <repo>\start-ai.ps1 -Built     (search works)
#
# Overridable:
#   $env:X64BASE_SITE    website source dir   [default: D:/dev/x64base-site]
#   $env:X64BASE_PYTHON  python launcher      [default: system python -- carries the gateway deps]
#
# Which python: the gateway runs under the default `python` (system), which has the
# imports it needs -- maint_server / schema_registry / crud, plus yaml for the
# build_reports it re-runs -- verified running in the foreground (2026-08-08). Use the
# full system python here, not $py12 / .venv312 (that venv is for yaml-only standalone
# tools; the gateway's import set is broader). Override via $env:X64BASE_PYTHON.
# NOTE: the ":3000 refused" seen during setup was NOT the interpreter -- it was a
# cmd /k quoting mistake in THIS script, since fixed at the gateway launch below.

param([switch]$Built)

$ErrorActionPreference = 'Continue'

# Repo root = the directory this script lives in (no hard-coded path).
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$site = if ($env:X64BASE_SITE)   { $env:X64BASE_SITE }   else { 'D:/dev/x64base-site' }
$py   = if ($env:X64BASE_PYTHON) { $env:X64BASE_PYTHON } else { 'python' }

# Pre-flight: fail loud here rather than into a 404 / ModuleNotFoundError later.
if (-not (Test-Path $site)) { Write-Host ("  WARNING: website dir not found: {0} (set `$env:X64BASE_SITE)" -f $site) }
if (($py -match '[\\/]') -and -not (Test-Path $py)) {
  Write-Host ("  WARNING: python not found: {0} -- the gateway needs pyyaml; set `$env:X64BASE_PYTHON" -f $py)
}

function Stop-Port([int]$port) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
      Write-Host ("  stopping PID {0} holding :{1}" -f $_, $port)
      Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
}

function Test-Port([int]$port) {
  try {
    $c = New-Object Net.Sockets.TcpClient
    $c.Connect('127.0.0.1', $port); $c.Close(); return $true
  } catch { return $false }
}

function Wait-Port([int]$port, [string]$label, [int]$tries = 60) {
  for ($i = 0; $i -lt $tries; $i++) {
    if (Test-Port $port) { Write-Host ("  {0} up on :{1}" -f $label, $port); return $true }
    Start-Sleep -Seconds 1
  }
  Write-Host ("  WARNING: {0} never came up on :{1} -- check its window" -f $label, $port)
  return $false
}

Write-Host 'freeing ports 3000 / 3002 / 8770 ...'
Stop-Port 3000; Stop-Port 3002; Stop-Port 8770
Start-Sleep -Seconds 1

if ($Built) {
  Write-Host ("building + serving the STATIC site on :3002 in {0} (search works in this mode) ..." -f $site)
  # `npm run build` runs the Pagefind index step; `serve out` serves the built tree with the index.
  Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/k', 'npm run build && npx serve out -l 3002' `
    -WorkingDirectory $site
  Wait-Port 3002 'website (built)' 300   # build + Pagefind index can take a couple of minutes
} else {
  Write-Host ("starting website (Next.js dev) on :3002 in {0} -- note: site SEARCH is inert under dev ..." -f $site)
  Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/k', 'npx next dev -p 3002' `
    -WorkingDirectory $site
  Wait-Port 3002 'website'
}

Write-Host 'starting reports gateway on :3000 (console Execute enabled) ...'
# Keep {0} ($py) UNQUOTED. `cmd /k` strips the first and last quote off the whole
# line, so an extra pair around the exe mangles the command into "The filename,
# directory name, or volume label syntax is incorrect" and the gateway never binds.
# The default 'python' has no spaces; if X64BASE_PYTHON is a spaced path, set an
# 8.3 short path or a symlink rather than quoting here.
$gwArgs = ('/k {0} "{1}\tools\reports\serve_dynamic_reports.py" --bind 127.0.0.1 --port 3000 --upstream http://127.0.0.1:3002 --enable-write' -f $py, $repo)
Start-Process -FilePath 'cmd.exe' -ArgumentList $gwArgs -WorkingDirectory $repo
Wait-Port 3000 'gateway'

Write-Host ''
Write-Host 'READY:'
Write-Host '  AI views:  http://localhost:3000/AI/'
Write-Host '  Console:   http://localhost:3000/AI/console'
if ($Built) {
  Write-Host '  Search:    http://localhost:3000/search   (built mode -- index present)'
} else {
  Write-Host '  Search:    inert under `next dev` -- relaunch with -Built to test /search'
}
Write-Host ''
Write-Host ('(Standalone console with writes, no gateway:  "{0}" tools\dbf\maint_server.py  -> http://127.0.0.1:8770/ )' -f $py)
Start-Process 'http://localhost:3000/AI/console'
