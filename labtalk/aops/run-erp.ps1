param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "launch-common.ps1")

$layout = Get-DotTalkLayout -EntryScriptPath $MyInvocation.MyCommand.Path
$erpDb = "cascade_precision_erp\cascade_precision_mfg_erp.sqlite"
$erpPath = Join-Path $layout.RuntimeData $erpDb

Write-Host "DotTalk++ launch directory:"
Write-Host "  $($layout.RuntimeData)"
Write-Host ""

if (Test-Path -LiteralPath $erpPath) {
    $info = Get-Item -LiteralPath $erpPath
    Write-Host "Cascade Precision ERP SQLite seed found:"
    Write-Host "  $erpDb"
    Write-Host "  $($info.Length) bytes"
} else {
    Write-Warning "Cascade Precision ERP SQLite seed NOT found at: $erpPath"
}

Write-Host ""
Write-Host "Recommended DotTalk++ ERP smoke commands:"
Write-Host "  erp cwd"
Write-Host "  erp check"
Write-Host "  erp modules"
Write-Host "  erp tables"
Write-Host "  erp views"
Write-Host "  erp columns Items"
Write-Host "  erp list Items 10"
Write-Host "  erp select select count(*) as user_tables from sqlite_schema where type='table' and name not like 'sqlite_%'"
Write-Host "  erp select select count(*) as analytical_views from sqlite_schema where type='view'"
Write-Host ""

Invoke-DotTalkCliRuntime -EntryScriptPath $MyInvocation.MyCommand.Path -AppArgs $AppArgs
