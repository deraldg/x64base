param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($AppArgs -and $AppArgs.Count -gt 0) {
    & (Join-Path $scriptDir "datarun.ps1") -CommandLines @("DOTSCRIPT arctictalk") @AppArgs
} else {
    & (Join-Path $scriptDir "datarun.ps1") -CommandLines @("DOTSCRIPT arctictalk")
}
exit $LASTEXITCODE
