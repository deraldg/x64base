param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $repoRoot "bindings\run_pydottalk_smokes.ps1"
$pythonExe = Join-Path $repoRoot "build-labtalk\vcpkg_installed\x64-windows\tools\python3\python.exe"
$buildPython = Join-Path $repoRoot "build-labtalk\python"

if (-not (Test-Path -LiteralPath $runner)) {
    throw "pydottalk smoke runner not found: $runner"
}

$argList = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $runner,
    '-PythonExe', $pythonExe,
    '-BuildPython', $buildPython
)

if ($AppArgs) {
    $argList += $AppArgs
}

& powershell @argList
exit $LASTEXITCODE
