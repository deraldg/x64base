# start-ai.ps1 -- bring up the local AI views + maintenance console on :3000.
#
# Companion to tools/reports/run_reports.py. The difference that matters:
# run_reports REUSES whatever already listens on :3000 / :3002, so a stale
# `next dev` on :3000 gets adopted AS the gateway and /AI/ + /AI/console 404.
# This script refuses occupied ports rather than terminating an unverified process.
#
# What it does, in order:
#   1. verify ports 3000 / 3002 / 8770 are free (never kill an unknown listener)
#   2. start the website on :3002                      (its own window)
#         default   : `next dev`  -- live editing/HMR, BUT SEE THE WARNING BELOW.
#                     Site SEARCH does not work (Pagefind has no index under dev)
#                     and NOTHING CLIENT-SIDE WORKS THROUGH :3000 EITHER.
#
#   *** DEV MODE THROUGH THE GATEWAY DOES NOT HYDRATE. Measured 2026-08-15. ***
#
#   The gateway proxies GET/HEAD through urllib and cannot carry a WebSocket
#   upgrade, so `next dev`'s HMR socket never connects and React never hydrates
#   behind :3000. Measured: 3 of 490 elements had a React fiber via :3000,
#   against 445 of 493 on :3002 direct. Every client component is then INERT --
#   menus do not open, useEffect never fires, the theme control does nothing,
#   the release stamp and visitor counter never render.
#
#   Nothing errors. The HTML arrives byte-identical, every chunk loads, the
#   console is clean, and the page LOOKS perfect. The only tell is that
#   "[HMR] connected" appears on :3002 and never on :3000.
#
#   This cost five rounds of "fixing" a theme button that had never been able to
#   run a click handler, and two more rounds after that. The warning here used
#   to say only that SEARCH was inert -- true, and far too narrow.
#
#   FIXED AND VERIFIED LIVE 2026-08-16 (AIF-118, 57de30b35).
#   tools/reports/ws_proxy.py carries the upgrade. Measured in the browser
#   against this gateway, 19:32 local: **436 of 493 elements hydrated on :3000**
#   (was 3 of 490), and **`[HMR] connected` appeared in the console on :3000**
#   -- the one line that used to appear only on :3002. Confirmed `next dev` with
#   Turbopack, not a -Built static serve, because a static build hydrates with no
#   socket and would have proved nothing. Attribution confirmed by clock: the
#   gateway process started 18:59:56, three minutes AFTER the commit at 18:56:57,
#   so it is not a stale process passing for a fixed one.
#   Everything above is kept: it is the diagnosis, and it is how you recognise
#   this shape the next time something looks perfect and does nothing.
#   Note for the next reader: Turbopack does NOT use /_next/webpack-hmr, so
#   probing that path proves nothing here. Read the console, not your guess at
#   the endpoint. Use :3000 for /AI/ and the console, served by the gateway.
#         -Built    : `npm run build` + `serve out` -- production-like; SEARCH WORKS
#   3. start the reports gateway on :3000              (its own window, preview by default)
#         -> /AI/         live reports, rebuilt per request (needs pyyaml -> venv)
#         -> /AI/console  maintenance UI (-EnableWrite allows Execute)
#         -> everything else proxied to :3002 (so /search rides the built site)
#   4. open http://localhost:3000/AI/console
#
# Stop everything by closing the two spawned windows (or Ctrl+C in each).
#
# Run:
#   powershell -ExecutionPolicy Bypass -File <repo>\start-ai.ps1            (dev)
#   powershell -ExecutionPolicy Bypass -File <repo>\start-ai.ps1 -Built     (search works)
#   powershell -ExecutionPolicy Bypass -File <repo>\start-ai.ps1 -EnableWrite
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

param(
  [switch]$Built,
  [switch]$EnableWrite
)

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

Write-Host 'verifying ports 3000 / 3002 / 8770 are free ...'
foreach ($port in @(3000, 3002, 8770)) {
  if (Test-Port $port) {
    Write-Error ("port :{0} is already occupied; refusing to stop an unverified process" -f $port)
    exit 2
  }
}

if ($Built) {
  Write-Host ("building + serving the STATIC site on :3002 in {0} (search works in this mode) ..." -f $site)
  # `npm run build` runs the Pagefind index step; `serve out` serves the built tree with the index.
  Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/k', 'npm run build && npx serve out -l 3002' `
    -WorkingDirectory $site
  if (-not (Wait-Port 3002 'website (built)' 300)) {
    Write-Error 'website startup failed; READY will not be announced'
    exit 3
  }
} else {
  Write-Host ("starting website (Next.js dev) on :3002 in {0} ..." -f $site)
  Write-Host "  WARNING: dev mode. Through :3000 the site does NOT hydrate --" -ForegroundColor Yellow
  Write-Host "  no menus, no theme control, no counter, no search. Nothing errors." -ForegroundColor Yellow
  Write-Host "  Use http://localhost:3002 for site work, or relaunch with -Built." -ForegroundColor Yellow
  Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/k', 'npx next dev -p 3002' `
    -WorkingDirectory $site
  if (-not (Wait-Port 3002 'website')) {
    Write-Error 'website startup failed; READY will not be announced'
    exit 3
  }
}

if ($EnableWrite) {
  Write-Host 'starting reports gateway on :3000 (console Execute enabled by explicit request) ...' -ForegroundColor Yellow
  $writeArg = ' --enable-write'
} else {
  Write-Host 'starting reports gateway on :3000 (read + preview; use -EnableWrite to allow Execute) ...'
  $writeArg = ''
}
# Keep {0} ($py) UNQUOTED. `cmd /k` strips the first and last quote off the whole
# line, so an extra pair around the exe mangles the command into "The filename,
# directory name, or volume label syntax is incorrect" and the gateway never binds.
# The default 'python' has no spaces; if X64BASE_PYTHON is a spaced path, set an
# 8.3 short path or a symlink rather than quoting here.
$gwArgs = ('/k {0} "{1}\tools\reports\serve_dynamic_reports.py" --bind 127.0.0.1 --port 3000 --upstream http://127.0.0.1:3002{2}' -f $py, $repo, $writeArg)
Start-Process -FilePath 'cmd.exe' -ArgumentList $gwArgs -WorkingDirectory $repo
if (-not (Wait-Port 3000 'gateway')) {
  Write-Error 'gateway startup failed; READY will not be announced'
  exit 4
}

try {
  $health = Invoke-RestMethod -Uri 'http://127.0.0.1:3000/AI/health' -TimeoutSec 30
  if ($health.mode -ne 'live-development' -or -not $health.upstream.ok) {
    throw 'gateway health payload did not identify a healthy live-development stack'
  }
  if ([bool]$health.execute_enabled -ne [bool]$EnableWrite) {
    throw 'gateway write posture does not match the requested startup mode'
  }
} catch {
  Write-Error ("gateway readiness validation failed: {0}" -f $_.Exception.Message)
  exit 5
}

Write-Host ''
Write-Host 'READY:'
Write-Host '  AI views:  http://localhost:3000/AI/'
Write-Host '  Console:   http://localhost:3000/AI/console'
Write-Host ('  Writes:    {0}' -f $(if ($EnableWrite) { 'ENABLED (explicit)' } else { 'disabled; previews only' }))
if ($Built) {
  Write-Host '  Search:    http://localhost:3000/search   (built mode -- index present)'
} else {
  Write-Host '  Search:    inert under `next dev` -- relaunch with -Built to test /search'
}
Write-Host ''
Write-Host ('(Standalone console with writes, no gateway:  "{0}" tools\dbf\maint_server.py  -> http://127.0.0.1:8770/ )' -f $py)
Start-Process 'http://localhost:3000/AI/'
