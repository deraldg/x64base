param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$preview = Join-Path $scriptDir "tools\gui_preview\dottalk_gui_preview.py"

if (-not (Test-Path -LiteralPath $preview)) {
    throw "Tk preview launcher not found: $preview"
}

Push-Location $scriptDir
try {
    & $python $preview @AppArgs
    $global:LASTEXITCODE = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $LASTEXITCODE
