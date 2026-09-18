param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Both paths handed to the runner used to be hardcoded into build-labtalk, a
# tree reclaimed 2026-09-17 whose tools\ directory had never held a python.exe
# (measured 2026-08-17). The runner has its own fallback list, so this script
# was overriding a list that could still have answered with two paths that
# could not. One shared resolver now.
. (Join-Path $repoRoot "launch-common.ps1")

$runner = Join-Path $repoRoot "bindings\run_pydottalk_smokes.ps1"
$pythonExe = Resolve-DotTalkPython -RepoRoot $repoRoot -Label "pydottalk smokes"
$buildPython = Resolve-DotTalkPyModuleDir -RepoRoot $repoRoot

if (-not (Test-Path -LiteralPath $runner)) {
    throw "pydottalk smoke runner not found: $runner"
}

$argList = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $runner,
    '-PythonExe', $pythonExe
)

# Nothing built yet is not an error here -- say so and let the runner report
# the miss in its own words, rather than passing a directory name that is not
# there and calling it a configuration.
if ($buildPython) {
    $argList += @('-BuildPython', $buildPython)
} else {
    Write-Warning "No built pydottalk module found under $repoRoot. Build it first: .\build_pydottalk.ps1"
}

if ($AppArgs) {
    $argList += $AppArgs
}

& powershell @argList
exit $LASTEXITCODE
