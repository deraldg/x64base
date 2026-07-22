param(
    [string[]]$CommandLines,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "launch-common.ps1")

Invoke-DotTalkCliRuntime -EntryScriptPath $MyInvocation.MyCommand.Path -CommandLines $CommandLines -AppArgs $AppArgs
