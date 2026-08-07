param(
    [ValidateSet('Debug','Release')]
    [string]$Config = 'Release',

    [string]$PythonExe = $env:PYDOTTALK_PYTHON
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$buildScript = Join-Path $repoRoot "build.ps1"

if (-not $PythonExe) {
    $pythonCandidates = @(
        $env:PY12,
        (Join-Path $repoRoot "pycrud\.venv\Scripts\python.exe"),
        (Join-Path $repoRoot "build-labtalk\vcpkg_installed\x64-windows\tools\python3\python.exe"),
        (Join-Path $repoRoot "build\vcpkg_installed\x64-windows\tools\python3\python.exe")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    if ($pythonCandidates.Count -gt 0) {
        $PythonExe = $pythonCandidates[0]
    }
}

if ($PythonExe) {
    Write-Host "LabTalk Python: $PythonExe"
} else {
    Write-Warning "No explicit Python executable resolved for pydottalk. CMake will fall back to default Python discovery."
}

& $buildScript -Config $Config -WithPyDotTalk -BuildDir (Join-Path $repoRoot "build-labtalk") -PythonExe $PythonExe
exit $LASTEXITCODE
