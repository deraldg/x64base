param(
    [string]$RepoRoot = "D:\code\ccode"
)

$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $PSScriptRoot "export_message_catalog_phase6.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3.12 $ScriptPath --repo-root $RepoRoot
    if ($LASTEXITCODE -eq 0) { exit 0 }
    if ($LASTEXITCODE -ne 9009) { exit $LASTEXITCODE }
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    python $ScriptPath --repo-root $RepoRoot
    exit $LASTEXITCODE
}

throw "Python was not found. Install Python 3.12 or make sure py/python is on PATH."
