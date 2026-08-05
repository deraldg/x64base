# start-ai.ps1 -- bring up the local AI views + maintenance console on :3000.
#
# Companion to tools/reports/run_reports.py. The difference that matters:
# run_reports REUSES whatever already listens on :3000 / :3002, so a stale
# `next dev` on :3000 gets adopted AS the gateway and /AI/ + /AI/console 404.
# This script FREES those ports first, so the gateway always really starts.
#
# What it does, in order:
#   1. free ports 3000 / 3002 / 8770 (stop any stale listener)
#   2. start the Next.js website on :3002              (its own window)
#   3. start the reports gateway on :3000              (its own window, writes ON)
#         -> /AI/         live reports, rebuilt per request
#         -> /AI/console  maintenance UI (--enable-write allows Execute)
#   4. open http://localhost:3000/AI/console
#
# Stop everything by closing the two spawned windows (or Ctrl+C in each).
#
# Run:
#   powershell -ExecutionPolicy Bypass -File <repo>\start-ai.ps1
#
# Overridable (defaults match run_reports.py):
#   $env:X64BASE_SITE    website source dir   [default: D:/dev/x64base-site]
#   $env:X64BASE_PYTHON  python launcher      [default: python]

$ErrorActionPreference = 'Continue'

# Repo root = the directory this script lives in (no hard-coded path).
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$site = if ($env:X64BASE_SITE)   { $env:X64BASE_SITE }   else { 'D:/dev/x64base-site' }
$py   = if ($env:X64BASE_PYTHON) { $env:X64BASE_PYTHON } else { 'python' }

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

Write-Host ("starting website (Next.js) on :3002 in {0} ..." -f $site)
Start-Process -FilePath 'cmd.exe' `
  -ArgumentList '/k', 'npx next dev -p 3002' `
  -WorkingDirectory $site
Wait-Port 3002 'website'

Write-Host 'starting reports gateway on :3000 (console Execute enabled) ...'
$gwArgs = ('/k {0} "{1}\tools\reports\serve_dynamic_reports.py" --bind 127.0.0.1 --port 3000 --upstream http://127.0.0.1:3002 --enable-write' -f $py, $repo)
Start-Process -FilePath 'cmd.exe' -ArgumentList $gwArgs -WorkingDirectory $repo
Wait-Port 3000 'gateway'

Write-Host ''
Write-Host 'READY:'
Write-Host '  AI views:  http://localhost:3000/AI/'
Write-Host '  Console:   http://localhost:3000/AI/console'
Write-Host ''
Write-Host ('(Standalone console with writes, no gateway:  {0} tools\dbf\maint_server.py  -> http://127.0.0.1:8770/ )' -f $py)
Start-Process 'http://localhost:3000/AI/console'
