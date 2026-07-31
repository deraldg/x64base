param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowActiveMessagingCatalogPromotion,

    [string]$ActiveDbfDir = "",
    [string]$ActiveIndexesDir = "",
    [string]$ActiveLmdbDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowActiveMessagingCatalogPromotion) {
    throw "Refusing Phase 18.2 active promotion without -AllowActiveMessagingCatalogPromotion"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\messaging\promote_message_catalog_phase18_1_active.py"
$argsList = @($script, "--repo-root", $RepoRoot, "--allow-active-messaging-catalog-promotion")

if ($ActiveDbfDir) { $argsList += @("--active-dbf-dir", $ActiveDbfDir) }
if ($ActiveIndexesDir) { $argsList += @("--active-indexes-dir", $ActiveIndexesDir) }
if ($ActiveLmdbDir) { $argsList += @("--active-lmdb-dir", $ActiveLmdbDir) }

if ($PythonExe -eq "py") {
    & py -3.12 @argsList
} else {
    & $PythonExe @argsList
}
exit $LASTEXITCODE
