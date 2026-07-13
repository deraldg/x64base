param(
    [ValidateSet('Debug','Release')]
    [string]$Config = 'Release',

    [string]$PythonExe = ''
)

$ErrorActionPreference = "Stop"

$BindingsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $BindingsDir
$BuildScript = Join-Path $RepoRoot "build.ps1"

if (-not $PythonExe) {
    $pythonCandidates = @(
        (Join-Path $RepoRoot "build-labtalk\vcpkg_installed\x64-windows\tools\python3\python.exe"),
        (Join-Path $RepoRoot "build\vcpkg_installed\x64-windows\tools\python3\python.exe"),
        $env:PYDOTTALK_PYTHON,
        $env:PY12,
        (Join-Path $RepoRoot "pycrud\.venv\Scripts\python.exe"),
        (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    if ($pythonCandidates.Count -gt 0) {
        $PythonExe = $pythonCandidates[0]
    }
}

if (-not $PythonExe) {
    throw "No Python executable resolved for pydottalk. Set PYDOTTALK_PYTHON, PY12, or pass -PythonExe."
}

Write-Host "BindingsDir: $BindingsDir"
Write-Host "RepoRoot   : $RepoRoot"
Write-Host "PythonExe  : $PythonExe"

& $BuildScript -Config $Config -WithPyDotTalk -BuildDir (Join-Path $RepoRoot "build-labtalk") -PythonExe $PythonExe
exit $LASTEXITCODE
