param(
    [int]$Port = 3000,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

if (-not (Test-Path (Join-Path $Root "node_modules"))) {
    npm install
}

while (Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -InformationLevel Quiet) {
    $Port++
}

$Url = "http://127.0.0.1:$Port/"
Write-Host "Starting Next development server"
Write-Host "URL: $Url"

if (-not $NoBrowser) {
    Start-Process $Url
}

npm run dev -- --hostname 127.0.0.1 --port $Port
