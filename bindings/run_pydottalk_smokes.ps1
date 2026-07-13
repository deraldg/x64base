# run_pydottalk_smokes.ps1
# Convenience runner for the pydottalk starter smokes.
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File .\bindings\run_pydottalk_smokes.ps1
#   .\bindings\run_pydottalk_smokes.ps1 -PythonExe .\pycrud\.venv\Scripts\python.exe

param(
    [string]$PythonExe = $env:PY12,
    [string]$BuildPython = $env:PYDOTTALK_BIN,
    [string]$SandboxDbfDir = $env:DOTTALK_DBF_DIR,
    [string]$X64Dbf = $env:DOTTALK_X64_DBF,
    [string]$X64DbfDir = $env:DOTTALK_X64_DBF_DIR
)

$ErrorActionPreference = "Stop"

$BindingsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $BindingsDir

if (-not $PythonExe) {
    $pythonCandidates = @(
        (Join-Path $RepoRoot "build-labtalk\vcpkg_installed\x64-windows\tools\python3\python.exe"),
        (Join-Path $RepoRoot "build\vcpkg_installed\x64-windows\tools\python3\python.exe"),
        $env:PYDOTTALK_PYTHON,
        $env:PY12,
        (Join-Path $RepoRoot "pycrud\.venv\Scripts\python.exe")
    ) | Where-Object { $_ -and (Test-Path $_) }

    if ($pythonCandidates.Count -gt 0) {
        $PythonExe = $pythonCandidates[0]
    } else {
        $PythonExe = "python"
    }
}

if (-not $BuildPython) {
    $buildPythonCandidates = @(
        (Join-Path $RepoRoot "build-labtalk\python"),
        (Join-Path $RepoRoot "build\python")
    ) | Where-Object { Test-Path -LiteralPath $_ }

    if ($buildPythonCandidates.Count -gt 0) {
        $BuildPython = $buildPythonCandidates[0]
    } else {
        $BuildPython = Join-Path $RepoRoot "build-labtalk\python"
    }
}

$env:PYDOTTALK_BIN = $BuildPython
$env:PYTHONPATH = $BuildPython

if ($SandboxDbfDir) { $env:DOTTALK_DBF_DIR = $SandboxDbfDir }
if ($X64Dbf) { $env:DOTTALK_X64_DBF = $X64Dbf }
if ($X64DbfDir) { $env:DOTTALK_X64_DBF_DIR = $X64DbfDir }

Write-Host "RepoRoot      : $RepoRoot"
Write-Host "PythonExe     : $PythonExe"
Write-Host "PYDOTTALK_BIN : $env:PYDOTTALK_BIN"
Write-Host ""

$pydCandidates = @(
    (Join-Path $env:PYDOTTALK_BIN "pydottalk.cp312-win_amd64.pyd"),
    (Join-Path $env:PYDOTTALK_BIN "pydottalk.cp311-win_amd64.pyd")
) | Where-Object { Test-Path -LiteralPath $_ }

if ($pydCandidates.Count -eq 0) {
    throw @"
pydottalk module not found under $($env:PYDOTTALK_BIN)
Build the LabTalk bindings lane first:
  .\build.ps1 -WithPyDotTalk
or:
  .\labtalk\aops\build-labtalk.ps1
"@
}

& $PythonExe (Join-Path $BindingsDir "pydottalk_probe_api.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
& $PythonExe (Join-Path $BindingsDir "pydottalk_smoke_readonly.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
& $PythonExe (Join-Path $BindingsDir "pydottalk_smoke_x64.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "OK: all pydottalk starter smokes completed."
