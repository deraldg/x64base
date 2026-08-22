param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "launch-common.ps1")

Invoke-DotTalkWbRuntime `
    -EntryScriptPath $MyInvocation.MyCommand.Path `
    -WbRelativeExeCandidates @(
        "build\src\gui\wx\Release\dottalk_wb_next.exe",
        "build\src\gui\wx\Debug\dottalk_wb_next.exe",
        "build-wx-fixed-local\src\gui\wx\Release\dottalk_wb_next.exe"
    ) `
    -AppArgs $AppArgs
