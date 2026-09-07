# tools/staging/pk_durability_child.ps1
#
# AIF-156 -- the two-run durability measurement, launched FROM INSIDE a running
# dottalkpp via the `!` command so REGRESSION PKDURABLE can reach it.
#
# WHY THIS EXISTS BESIDE pk_durability_two_run.ps1, WHICH DOES THE SAME THING.
# That driver goes through datarun.ps1, which calls Update-DotTalkRuntimeExe --
# it may COPY the runtime executable, and the parent process holding this
# script open IS that executable. Copying over a running binary fails on
# Windows. This launcher therefore invokes build\src\Release\dottalkpp.exe
# DIRECTLY, sets no environment, and copies nothing.
#
# It also does NOT grade. Grading happens in the regression validator, which
# reads the .alt captures off disk -- `!` runs std::system(), so a child's
# stdout never passes through the C++ stream the routed capture swaps, and a
# transcript-reading validator would see none of it.

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$exe  = Join-Path $repo "build\src\Release\dottalkpp.exe"
$data = Join-Path $repo "dottalkpp\data"

if (-not (Test-Path -LiteralPath $exe)) {
    Write-Host "PKDURABLE-CHILD: runtime not found at $exe"
    exit 2
}

$run1 = Join-Path $data "scripts\pk_durable_write.dts"
$run2 = Join-Path $data "scripts\pk_durable_read.dts"
$alt1 = Join-Path $data "tmp\pkdur_run1.alt"
$alt2 = Join-Path $data "tmp\pkdur_run2.alt"

foreach ($p in @($run1, $run2)) {
    if (-not (Test-Path -LiteralPath $p)) {
        Write-Host "PKDURABLE-CHILD: missing script $p"
        exit 2
    }
}

# A stale capture would be graded as this run's evidence. The validator cannot
# tell an old file from a new one, so the deletion has to happen here.
foreach ($p in @($alt1, $alt2)) {
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
}

Push-Location $data
try {
    Write-Host "PKDURABLE-CHILD: run 1 of 2 -- declare and write"
    & $exe --script $run1 | Out-Null

    Write-Host "PKDURABLE-CHILD: run 2 of 2 -- reopen WITHOUT redeclaring"
    & $exe --script $run2 | Out-Null
}
finally {
    Pop-Location
}

Write-Host "PKDURABLE-CHILD: both runs complete; captures are on disk for the validator"
exit 0
