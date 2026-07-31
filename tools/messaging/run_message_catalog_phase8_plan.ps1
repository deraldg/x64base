param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "RepoRoot not found: $RepoRoot"
}

$script = Join-Path $RepoRoot "tools\messaging\plan_message_catalog_phase8_dbf_schema_staging.py"
if (-not (Test-Path -LiteralPath $script)) {
    throw "Phase 8 planner not found: $script"
}

if ($PythonExe -and (Test-Path -LiteralPath $PythonExe)) {
    & $PythonExe $script --repo-root $RepoRoot
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    & $python.Source $script --repo-root $RepoRoot
    exit $LASTEXITCODE
}

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & $py.Source -3.12 $script --repo-root $RepoRoot
    exit $LASTEXITCODE
}

throw "No suitable Python runtime found. Re-run with -PythonExe `$py12 or a full python.exe path."
