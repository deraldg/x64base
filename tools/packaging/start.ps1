# start.ps1 -- launch DotTalk++ from an unzipped x64base release.
#
# Installed at the package root beside bin\ and data\ (CMakeLists.txt). The
# runtime treats its launch directory as the data root, so it must start from
# data\; this does that from wherever you run the script, and puts your shell
# back where it was afterwards. Owner's recipe, 2026-11-27:
#     cd data ; ..\bin\dottalkpp.exe ; cd ..
#
#   .\start.ps1                     interactive shell
#   .\start.ps1 --script my.dts     any dottalkpp arguments pass straight through
#   .\start.ps1 -FirstRun           build the x64 LMDB indexes once, then start
#
# The development tree uses datarun.ps1 instead; it also stages a fresh build.
[CmdletBinding()]
param(
    [switch] $FirstRun,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $DotTalkArgs
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$exe  = Join-Path $root "bin\dottalkpp.exe"
$data = Join-Path $root "data"
foreach ($p in $exe, $data) {
    if (-not (Test-Path -LiteralPath $p)) { throw "start.ps1: not found: $p (run it from the unzipped release folder)" }
}

Push-Location -LiteralPath $data
try {
    if ($FirstRun) {
        $build = Join-Path $data "scripts\mcc\mcc_build_x64_lmdb.dts"
        Write-Host "start.ps1: building the x64 LMDB indexes (first run only)..."
        & $exe --script $build
        if ($LASTEXITCODE -ne 0) { throw "start.ps1: index build exited $LASTEXITCODE" }
    }
    & $exe @DotTalkArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code
