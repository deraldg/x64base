param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"

# THIS COPY WAS BROKEN TWICE OVER. It ran `Set-Location $PSScriptRoot` and then
# `python .\portal\labtalk_portal.py` -- but labtalk\aops\portal\ does not
# exist and never has; the portal lives at labtalk\portal\. So even an
# interpreter that could open the window had nothing to open. Measured
# 2026-09-18.
#
# It delegates to the repo-root launcher rather than repeating it, and it
# dot-sources the ROOT launch-common.ps1 by way of that launcher: the twin in
# this directory is a different, shorter file and does not carry the resolver.
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$entry = Join-Path $repoRoot "launch_portal.ps1"

if (-not (Test-Path -LiteralPath $entry)) {
    throw "LabTalk portal launcher not found: $entry"
}

if ($AppArgs) {
    & $entry @AppArgs
} else {
    & $entry
}
exit $LASTEXITCODE
