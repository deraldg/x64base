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

# 'Continue', not 'Stop'. Every failure this script cares about is checked
# EXPLICITLY below and exits with its own distinct code (2 ports, 3 website,
# 4 gateway, 5 readiness). Under 'Stop' an incidental non-terminating error --
# a Get-Process race, a transient socket refusal inside Test-Port -- would
# abort the run with no code and no diagnosis, which is strictly worse than a
# checked failure that says which stage died.
$ErrorActionPreference = 'Continue'

# THREE INPUTS, AND ONLY ONE OF THEM IS ALLOWED TO BE HARD-CODED ANYWHERE.
#
#   $repo  derived from this script's OWN location. Never a literal: the script
#          lives at the repo root, so the root is wherever the script is, and a
#          clone at another path works untouched.
#   $site  the WEBSITE tree, a separate working tree of the same git repository
#          on branch codex/lean-sites-publish. The default is a literal because
#          there is nothing to derive it from -- it is not under $repo.
#   $py    the interpreter for the GATEWAY. See the header: this is the SYSTEM
#          python, not .venv312, because the gateway imports maint_server,
#          schema_registry and crud on top of yaml, and the 312 venv carries
#          yaml only. Getting this wrong fails as ModuleNotFoundError in a
#          window that has already scrolled.
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$site = if ($env:X64BASE_SITE)   { $env:X64BASE_SITE }   else { 'D:/dev/x64base-site' }
$py   = if ($env:X64BASE_PYTHON) { $env:X64BASE_PYTHON } else { 'python' }

# WARN, DO NOT EXIT. Both of these are recoverable by the person reading, and a
# hard exit here would block the half of the stack that does not need the missing
# piece: a bad $site still lets the gateway serve /AI/, which is often the only
# reason someone ran this. The point is to fail LOUD AND EARLY IN WORDS rather
# than late and silently as a 404 or an import error in a spawned window.
if (-not (Test-Path $site)) { Write-Host ("  WARNING: website dir not found: {0} (set `$env:X64BASE_SITE)" -f $site) }
# Only path-shaped values are checked for existence. A bare name like 'python'
# is resolved by PATH at spawn time and Test-Path would report a false absence
# for every correct value, so the `-match` guard is load-bearing, not tidiness.
if (($py -match '[\\/]') -and -not (Test-Path $py)) {
  Write-Host ("  WARNING: python not found: {0} -- the gateway needs pyyaml; set `$env:X64BASE_PYTHON" -f $py)
}

# Test-Port answers ONE question: is something LISTENING on this port right now.
#
# It is deliberately used for both of the opposite things this script needs --
# "refuse, the port is taken" before a spawn, and "good, it came up" after one --
# because those are the same measurement read with different intent. Keeping one
# function means the two can never disagree about what "occupied" means.
#
# A real TCP connect, not Get-NetTCPConnection: a bound-but-not-accepting socket
# is not a service, and connect() is the only probe that distinguishes them. This
# is also what makes it portable enough to be the refusal's authority, while the
# process-naming below is Windows-only and merely advisory.
#
# 127.0.0.1 and never 'localhost': on a dual-stack host localhost may resolve to
# ::1 first, and a server bound to IPv4 only would read as absent.
function Test-Port([int]$port) {
  try {
    $c = New-Object Net.Sockets.TcpClient
    $c.Connect('127.0.0.1', $port); $c.Close(); return $true
  } catch { return $false }
}

# Wait-Port polls for up to $tries seconds and RETURNS A BOOLEAN rather than
# exiting, so each caller can choose its own exit code and message. The callers
# do exit; this does not decide for them.
#
# A BOUND PORT IS NOT A READY SERVICE, and this function cannot tell the
# difference. `next dev` binds :3002 immediately and compiles the first request
# on demand, so this returns $true while the site is still building. That is why
# the readiness gate further down polls /AI/health instead of trusting these two
# calls -- see the long note there, which was written after a cold start was
# reported as a failure.
#
# 60 tries is the default; the -Built path passes 300 because `npm run build`
# plus the Pagefind index is minutes, not seconds. On timeout this WARNS rather
# than erroring, because the diagnosis lives in the spawned window and the
# caller is about to say so.
function Wait-Port([int]$port, [string]$label, [int]$tries = 60) {
  for ($i = 0; $i -lt $tries; $i++) {
    if (Test-Port $port) { Write-Host ("  {0} up on :{1}" -f $label, $port); return $true }
    Start-Sleep -Seconds 1
  }
  Write-Host ("  WARNING: {0} never came up on :{1} -- check its window" -f $label, $port)
  return $false
}

# 8770 WAS IN THIS LIST AND IS NOT ANY MORE (fixed 2026-09-25). Measured:
# `grep 8770` across tools/reports/serve_dynamic_reports.py and ws_proxy.py
# returns NOTHING. This script binds 3000 and 3002 and never 8770 -- that port
# belongs to the STANDALONE maint_server.py named in the closing hint, which this
# script does not start. So a console the owner left running on 8770 used to
# hard-refuse a launch that had no use for the port. A preflight may only refuse
# a port the thing it is starting actually needs.
Write-Host 'verifying ports 3000 / 3002 are free ...'
foreach ($port in @(3000, 3002)) {
  if (Test-Port $port) {
    # NAME THE LISTENER. "refusing to stop an unverified process" is the right
    # posture and was not actionable: it never said WHICH process, so the owner
    # had to go find it. Verifying it is the whole point, so hand over what is
    # needed to verify. Best-effort -- Get-NetTCPConnection is Windows-only and
    # the refusal must not depend on it.
    $who = ''
    try {
      # NOT $pid: that is a read-only automatic variable in PowerShell (this
      # process's own id) and assigning to it throws.
      $ownerPid = (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop |
                   Select-Object -First 1).OwningProcess
      $proc = Get-Process -Id $ownerPid -ErrorAction Stop
      $who = (" -- held by {0} (pid {1}), started {2}" -f $proc.ProcessName, $ownerPid, $proc.StartTime)
    } catch { $who = ' -- could not identify the listener' }
    Write-Error ("port :{0} is already occupied; refusing to stop an unverified process{1}" -f $port, $who)
    exit 2
  }
}

# 8770 is REPORTED, never enforced: knowing the standalone console is already up
# is useful, and it is not this script's business.
if (Test-Port 8770) {
  Write-Host '  note: something is listening on :8770 (the standalone maint console port).'
  Write-Host '        Not used by this script and not a reason to stop.'
}

# ===========================================================================
# STEP 2 -- the website on :3002, in its OWN window, from $site
# ===========================================================================
#
# WHY A SEPARATE WINDOW AND NOT A BACKGROUND JOB. These two processes are
# long-lived and their output IS the diagnosis when something goes wrong: the
# Next compile errors, the Pagefind counts, the gateway's request log. A
# PowerShell job swallows all of it into a buffer nobody reads. `cmd /k` keeps
# the window open after the command ends, so a process that DIED still shows why.
# Closing the window is the documented stop.
#
# WHY :3002 IS THE SITE AND :3000 IS NOT. The site is served here, directly, from
# $site. :3000 is the reports gateway, which owns /AI/* and /reports/* and proxies
# everything else here. So :3002 is the authoritative view of the website and
# :3000 is the same bytes through a proxy plus the AI views. For SITE work, use
# :3002; there is nothing between you and the answer.
if ($Built) {
  Write-Host ("building + serving the STATIC site on :3002 in {0} (search works in this mode) ..." -f $site)
  # TWO COMMANDS, CHAINED WITH && ON PURPOSE. `npm run build` ends with
  # `pagefind --site out`, which writes the search index into out/pagefind; then
  # `serve out` serves that built tree. The && means a FAILED build never gets
  # served: no port opens, Wait-Port times out, and this exits 3 rather than
  # serving a stale out/ from a previous run as though the build had succeeded.
  # That is the difference between this mode and dev mode -- here the artifact is
  # real, so search works and what you see is what publishes.
  Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/k', 'npm run build && npx serve out -l 3002' `
    -WorkingDirectory $site
  # 300 tries, not the default 60: the build chain runs five checks, a Next
  # production compile and the Pagefind index. Minutes, not seconds.
  if (-not (Wait-Port 3002 'website (built)' 300)) {
    Write-Error 'website startup failed; READY will not be announced'
    exit 3
  }
} else {
  Write-Host ("starting website (Next.js dev) on :3002 in {0} ..." -f $site)
  # THIS WARNING IS KEPT DELIBERATELY OVERSTATED, and the header explains why at
  # length. The no-hydration defect it describes WAS FIXED on 2026-08-16 by
  # ws_proxy.py and verified live (436 of 493 elements, `[HMR] connected` on
  # :3000). What remains true in dev mode on EITHER port is that SEARCH is inert,
  # because Pagefind has no index until a build runs. The warning stays because
  # the shape it teaches -- a page that looks perfect and does nothing, with a
  # clean console -- cost seven rounds of debugging, and a reader who meets it
  # again should recognise it in one line rather than five.
  Write-Host "  WARNING: dev mode. Through :3000 the site does NOT hydrate --" -ForegroundColor Yellow
  Write-Host "  no menus, no theme control, no counter, no search. Nothing errors." -ForegroundColor Yellow
  Write-Host "  Use http://localhost:3002 for site work, or relaunch with -Built." -ForegroundColor Yellow
  # npx, not a bare `next`: the binary lives in the site tree's node_modules and
  # is not on PATH. -WorkingDirectory is what makes npx find it.
  Start-Process -FilePath 'cmd.exe' `
    -ArgumentList '/k', 'npx next dev -p 3002' `
    -WorkingDirectory $site
  if (-not (Wait-Port 3002 'website')) {
    Write-Error 'website startup failed; READY will not be announced'
    exit 3
  }
}

# ===========================================================================
# STEP 3 -- the reports gateway on :3000, in its own window, from $repo
# ===========================================================================
#
# WRITES ARE OFF UNLESS ASKED FOR, IN WORDS, ON THE COMMAND LINE. The console can
# Execute maintenance actions against real DBFs, so the safe posture is the
# default and the dangerous one costs a flag. The yellow line is not decoration:
# it is the only on-screen evidence of which posture a running window is in, and
# the readiness gate below re-checks the SERVER's answer against this intent so a
# mismatch cannot be announced as READY.
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
# -WorkingDirectory $repo is required, not cosmetic: the gateway does
# `import ws_proxy` as a same-directory module and resolves the registries it
# reads relative to the repo root.
Start-Process -FilePath 'cmd.exe' -ArgumentList $gwArgs -WorkingDirectory $repo
# Port first, health second. This only proves something BOUND :3000; whether it
# is healthy is the next block's job, and the two are separate questions.
if (-not (Wait-Port 3000 'gateway')) {
  Write-Error 'gateway startup failed; READY will not be announced'
  exit 4
}

# Readiness is POLLED, not asked once, and a failure PRINTS THE PAYLOAD.
#
# WHY POLLED (measured 2026-08-17): a bound port is not a ready service. The
# gateway's health check does a HEAD to the upstream, while `next dev` binds
# :3002 immediately and compiles the first request on demand. So both Wait-Port
# calls can succeed, the health check fire, the upstream still be compiling, and
# the gateway CORRECTLY answer 503. A cold start exited 5 that way while both
# processes were fine and healthy one second later (started_at 21:53:42Z,
# last_render_at 21:53:43Z). The old single attempt turned a startup race into a
# reported failure.
#
# WHY THE BODY IS PRINTED: health_payload() reports three separate conditions --
# upstream.ok, registries.ok, last_render_error -- and returns them in the
# response body. Invoke-RestMethod throws on 503, so the old catch printed only
# "Response status code does not indicate success" and discarded the diagnosis
# the server had already made. In PowerShell 7 the body survives on
# $_.ErrorDetails.Message; use it.
#
# The strict posture is UNCHANGED: this still refuses to announce READY for a
# genuinely unhealthy stack. It just stops calling a cold start a failure.
# ===========================================================================
# STEP 3b -- READINESS. Two ports up is not a working stack.
# ===========================================================================
#
# 90 seconds against Wait-Port's 60: this window must outlast a FIRST-REQUEST
# COMPILE, which begins only once the gateway's health check touches the upstream.
# So the clock effectively starts after both spawns, not with them.
#
# $lastDetail carries the newest diagnosis out of the loop so the failure message
# can print it. Seeded 'no response' because the first iteration can throw before
# assigning anything, and a failure that says 'no response' is honest while an
# empty string reads like a bug in this script.
#
# $announcedWait makes the "waiting to compile" line print ONCE rather than every
# two seconds. A progress message repeated 45 times is noise that hides the real
# output above it.
$healthDeadline = (Get-Date).AddSeconds(90)
$health = $null
$lastDetail = 'no response'
$announcedWait = $false
while ($true) {
  try {
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:3000/AI/health' -TimeoutSec 15
    # TRUST THE SERVER'S OWN VERDICT (fixed 2026-09-25).
    #
    # This used to read `$health.mode -eq 'live-development' -and $health.upstream.ok`,
    # and BOTH halves were wrong.
    #
    #   `mode` is a hardcoded string literal in health_payload() -- it can never
    #   hold any other value, so testing it was a tautology wearing the shape of a
    #   check. It is also WRONG in -Built mode, where the upstream is a static
    #   production serve and the gateway still says "live-development", because the
    #   gateway is never told which mode the site is in.
    #
    #   `upstream.ok` is ONE of the THREE conditions the server combines into
    #   `ok`: upstream_ok AND registries.ok AND NOT last_render_error. So READY
    #   could be announced with broken registries or a live render error, and the
    #   comment above claiming this "refuses to announce READY for a genuinely
    #   unhealthy stack" was not true of the code beneath it.
    #
    # health_payload() already computes the answer. Read it; do not recompute a
    # weaker version of it.
    if ($health.ok) { break }
    $lastDetail = ('ok={0} upstream.ok={1} registries.ok={2} last_render_error={3} upstream.error={4}' -f `
      $health.ok, $health.upstream.ok, $health.registries.ok, $health.last_render_error, $health.upstream.error)
  } catch {
    # THE SERVER'S OWN DIAGNOSIS SURVIVES HERE OR IT IS LOST. Invoke-RestMethod
    # THROWS on 503, and health_payload() puts the three failing conditions in the
    # RESPONSE BODY of that 503. The old catch printed only
    # "Response status code does not indicate success" and discarded the answer
    # the server had already worked out. In PowerShell 7 the body survives on
    # $_.ErrorDetails.Message; $_.Exception.Message is the fallback for a real
    # transport failure, where there is no body because there was no response.
    $body = $_.ErrorDetails.Message
    $lastDetail = if ($body) { $body } else { $_.Exception.Message }
    # Cleared so a stale payload from an earlier iteration cannot be mistaken for
    # this one's answer by the posture check after the loop.
    $health = $null
  }
  # Deadline checked AFTER the attempt, so a stack that becomes healthy on the
  # very last try is still accepted. Checking first would discard a good answer.
  if ((Get-Date) -gt $healthDeadline) {
    Write-Error ("gateway readiness validation failed after 90s. Last health response:`n{0}" -f $lastDetail)
    exit 5
  }
  if (-not $announcedWait) {
    Write-Host '  waiting for the upstream site to compile its first request ...'
    $announcedWait = $true
  }
  # 2 seconds: fast enough that a ready stack is announced promptly, slow enough
  # that a compiling upstream is not hammered with 45 HEADs it has to queue.
  Start-Sleep -Seconds 2
}

# NOT retried: a write-posture mismatch is a real disagreement about what was
# asked for, not a cold start, and waiting cannot change it.
# THE ONE CONDITION THAT IS NOT RETRIED, and the comment above says why: a write
# posture mismatch is a disagreement about what was ASKED FOR, not a race, so
# waiting cannot change it. It means the flag and the running server disagree
# about whether Execute is live, and that is exactly the thing never to guess at.
#
# [bool] on both sides on purpose: JSON `false` arrives as $false but a missing
# field arrives as $null, and $null -ne $false in PowerShell. Without the casts an
# older gateway that omits the field would fail the comparison and be reported as
# a posture mismatch when it is really a version mismatch.
if ([bool]$health.execute_enabled -ne [bool]$EnableWrite) {
  $postureMsg = 'gateway write posture does not match the requested startup mode (execute_enabled={0}, -EnableWrite={1})'
  Write-Error ($postureMsg -f $health.execute_enabled, [bool]$EnableWrite)
  exit 5
}

# ===========================================================================
# STEP 4 -- READY, and it is a CLAIM this script has earned by measurement
# ===========================================================================
#
# Nothing above prints this word on a bound port alone. Reaching here means: both
# ports were free and then both came up, the gateway answered /AI/health with
# ok=true (upstream reachable AND registries loaded AND no live render error), and
# its write posture matched what was asked for on the command line. Four ways out
# before this point, each with its own exit code, so a failure names its stage.
Write-Host ''
Write-Host 'READY:'
# The SCRIPT knows which mode the site is in; the gateway does not and reports a
# constant. Print it here so the one line a reader trusts is the one that is true.
Write-Host ('  Site mode: {0}' -f $(if ($Built) { 'BUILT (static serve of out/, production-like)' } else { 'next dev (live source, HMR)' }))
Write-Host '  AI views:  http://localhost:3000/AI/'
Write-Host '  Console:   http://localhost:3000/AI/console'
Write-Host ('  Writes:    {0}' -f $(if ($EnableWrite) { 'ENABLED (explicit)' } else { 'disabled; previews only' }))
# SEARCH IS THE ONE CAPABILITY THAT DEPENDS ON THE MODE, so it is reported from
# $Built rather than probed. Pagefind writes its index during `npm run build`; in
# dev mode there is no index, so /search returns a page that loads cleanly and
# finds nothing. Reporting it as available would be the same class of lie as the
# hydration defect above: a surface that responds without working.
if ($Built) {
  Write-Host '  Search:    http://localhost:3000/search   (built mode -- index present)'
} else {
  Write-Host '  Search:    inert under `next dev` -- relaunch with -Built to test /search'
}
Write-Host ''
# The 8770 escape hatch: the maintenance console WITHOUT the gateway or the
# website, for when only the DBF tools are wanted. This script does not start it
# and does not require its port free -- see the preflight note above. Quoted here
# because this is a message for a human to copy, not a command this script runs,
# so the cmd /k quoting rule above does not apply.
Write-Host ('(Standalone console with writes, no gateway:  "{0}" tools\dbf\maint_server.py  -> http://127.0.0.1:8770/ )' -f $py)
# Opens /AI/ rather than /AI/console: the views are the read-only landing and the
# console is one click away. Last statement in the file, so nothing after this can
# fail and leave a browser open on a stack that was about to be reported broken.
Start-Process 'http://localhost:3000/AI/'
