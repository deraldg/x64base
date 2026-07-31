# start-localhost.ps1 — launch the x64base.com dev site on http://localhost:3000
# Lives in D:\code\ccode for convenience; the site itself is D:\dev\x64base-site.
# Usage:  right-click > Run with PowerShell,  or from D:\code\ccode:  .\start-localhost.ps1
$ErrorActionPreference = "Stop"

$site = "D:\dev\x64base-site"
$url  = "http://localhost:3000"

if (-not (Test-Path $site)) { throw "Site folder not found: $site" }
Set-Location $site
Write-Host "x64base.com — local dev server" -ForegroundColor Cyan
Write-Host "  folder: $site"
Write-Host "  url:    $url"
Write-Host ""

# First run (or after a clean): install dependencies.
if (-not (Test-Path (Join-Path $site "node_modules"))) {
    Write-Host "node_modules not found — installing dependencies (one time)..." -ForegroundColor Yellow
    npm install
}

# Open the browser a few seconds after the server starts compiling.
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:3000"
} | Out-Null

Write-Host "Starting Next.js dev server (Ctrl+C to stop)..." -ForegroundColor Green
npm run dev
