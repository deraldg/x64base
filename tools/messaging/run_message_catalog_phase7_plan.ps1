param(
    [Parameter(Mandatory=$true)]
    [string]$RepoRoot,

    [Parameter(Mandatory=$false)]
    [string]$PythonExe
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    if ($env:PYTHON312) {
        $PythonExe = $env:PYTHON312
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 --version *> $null
        if ($LASTEXITCODE -eq 0) {
            $PythonExe = "py"
            $script:UsePyLauncher = $true
        }
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonExe = "python"
    } else {
        throw "No Python runtime found. Pass -PythonExe `$py12 or set PYTHON312."
    }
}

$ScriptPath = Join-Path $RepoRoot "tools\messaging\plan_message_catalog_phase7_promotion.py"

if (-not (Test-Path $ScriptPath)) {
    throw "Missing Phase 7 script: $ScriptPath"
}

if ($script:UsePyLauncher) {
    & py -3.12 $ScriptPath --repo-root $RepoRoot
} else {
    & $PythonExe $ScriptPath --repo-root $RepoRoot
}

if ($LASTEXITCODE -ne 0) {
    throw "Phase 7 promotion-readiness plan failed with exit code $LASTEXITCODE"
}
