param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe = "",

    [switch]$AllowActiveLocalePromotion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowActiveLocalePromotion) {
    throw "Refusing Phase 23G active locale promotion without -AllowActiveLocalePromotion"
}

if (-not $PythonExe) {
    if ($env:PYTHON_EXE) { $PythonExe = $env:PYTHON_EXE }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    else { throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON_EXE." }
}

$script = Join-Path $RepoRoot "tools\locale\promote_locale_phase23g_active_locale_spine.py"

if ($PythonExe -eq "py") {
    & py -3.12 $script --repo-root $RepoRoot --allow-active-locale-promotion
} else {
    & $PythonExe $script --repo-root $RepoRoot --allow-active-locale-promotion
}
exit $LASTEXITCODE
