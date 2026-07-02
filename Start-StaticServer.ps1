param(
    [int]$Port = 4173,
    [switch]$Build,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutDir = Join-Path $Root "out"

Set-Location -LiteralPath $Root

if ($Build -or -not (Test-Path (Join-Path $OutDir "index.html"))) {
    npm install
    npm run build
}

if (-not (Test-Path (Join-Path $OutDir "index.html"))) {
    throw "Static export was not found at $OutDir. Run with -Build or run npm run build first."
}

while (Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -InformationLevel Quiet) {
    $Port++
}

$Url = "http://127.0.0.1:$Port/"
Write-Host "Serving static export from $OutDir"
Write-Host "URL: $Url"

if (-not $NoBrowser) {
    Start-Process $Url
}

Set-Location -LiteralPath $OutDir
python -m http.server $Port --bind 127.0.0.1
