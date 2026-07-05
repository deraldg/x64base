param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

$target = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "run-wx.ps1"
& $target @AppArgs
exit $LASTEXITCODE
