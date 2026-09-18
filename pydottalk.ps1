param(
    [string]$PythonExe = '',
    [string]$ModuleDir = ''
)

$ErrorActionPreference = "Stop"

# Both parameters used to DEFAULT to absolute paths inside build-labtalk: a
# tree reclaimed 2026-09-17 whose tools\ directory had never held a python.exe
# in the first place (measured 2026-08-17). Neither default has resolved for
# some time, and each one threw at its own Test-Path rather than looking
# anywhere else. One shared resolver now.
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $repoRoot "launch-common.ps1")

$PythonExe = Resolve-DotTalkPython -RepoRoot $repoRoot -PythonExe $PythonExe -Label "pydottalk"
$ModuleDir = Resolve-DotTalkPyModuleDir -RepoRoot $repoRoot -ModuleDir $ModuleDir

if (-not $ModuleDir) {
    throw "pydottalk module directory not found under $repoRoot. Build it first: .\build_pydottalk.ps1"
}
if (-not (Test-Path -LiteralPath $ModuleDir)) {
    throw "pydottalk module directory not found: $ModuleDir"
}

$env:PYDOTTALK_BIN = $ModuleDir
if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
    $env:PYTHONPATH = $ModuleDir
} else {
    $env:PYTHONPATH = "$ModuleDir;$env:PYTHONPATH"
}

& $PythonExe -c "import sys; print(sys.version); print(sys.executable)"
& $PythonExe -c "import pydottalk; print('LOADED:', pydottalk.__file__); print([n for n in dir(pydottalk) if not n.startswith('_')])"
