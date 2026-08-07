param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "launch-common.ps1")

Invoke-PydotTalkStarterSmokes -EntryScriptPath $MyInvocation.MyCommand.Path -AppArgs $AppArgs
