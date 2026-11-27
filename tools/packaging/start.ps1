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
#   .\start.ps1 -FirstRun           build the sample LMDB indexes once (MCC x64,
#                                   Cascade ERP), then start
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
        # LMDB environments are derived and never shipped; build each sample
        # system's once. Each build runs in its own process, so the session
        # that follows starts with no tables open.
        $builds = @(
            "scripts\mcc\mcc_build_x64_lmdb.dts",
            "systems\cascade_erp\scripts\cascade_erp_build_indexes.dts"
        )
        foreach ($rel in $builds) {
            $build = Join-Path $data $rel
            if (-not (Test-Path -LiteralPath $build)) { continue }
            Write-Host "start.ps1: building LMDB indexes: $rel (first run only)..."
            & $exe --script $build | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "start.ps1: index build $rel exited $LASTEXITCODE" }
        }
    }
    & $exe @DotTalkArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $code
