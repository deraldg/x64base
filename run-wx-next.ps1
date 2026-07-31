param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "launch-common.ps1")

Invoke-DotTalkWxRuntime `
    -EntryScriptPath $MyInvocation.MyCommand.Path `
    -WxRelativeExeCandidates @(
        "build\src\gui\wx\Release\dottalk_wx_next.exe",
        "build\src\gui\wx\Debug\dottalk_wx_next.exe",
        "build-wx-fixed-local\src\gui\wx\Release\dottalk_wx_next.exe"
    ) `
    -AppArgs $AppArgs
