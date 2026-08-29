param(
    [switch]$NoApi,
    [switch]$Setup,
    [int]$Port = 8000,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PycrudRoot = Join-Path $RepoRoot "pycrud"
$ApiRoot = Join-Path $PycrudRoot "pydottalk_api"
$GuiPython = Join-Path $PycrudRoot ".venv\Scripts\python.exe"
$ApiPython = Join-Path $ApiRoot ".venv\Scripts\python.exe"

if ($Setup) {
    & (Join-Path $PycrudRoot "setup.ps1")
    & (Join-Path $ApiRoot "setup.ps1")
}

if (-not (Test-Path $GuiPython)) {
    Write-Host "pycrud GUI venv missing; running setup..."
    & (Join-Path $PycrudRoot "setup.ps1")
}

if (-not $NoApi) {
    if (-not (Test-Path $ApiPython)) {
        Write-Host "pydottalk_api venv missing; running setup..."
        & (Join-Path $ApiRoot "setup.ps1")
    }

    $apiUrl = "http://127.0.0.1:$Port"
    $env:DOT_TALK_URL = $apiUrl
    $env:PYCRUD_API_URL = $apiUrl

    try {
        Invoke-RestMethod -Uri "$apiUrl/status" -TimeoutSec 2 | Out-Null
        Write-Host "pydottalk_api already running at $apiUrl"
    } catch {
        Write-Host "Starting pydottalk_api at $apiUrl"
        Start-Process -FilePath $ApiPython `
            -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port") `
            -WorkingDirectory $ApiRoot `
            -WindowStyle Hidden | Out-Null
        Start-Sleep -Seconds 2
    }
}

Set-Location $PycrudRoot
& $GuiPython ".\main.py" @AppArgs
