# build_help.ps1 -- configure, build EVERY target, then validate HELP against the registry.
#
# WHAT LINE 3 USED TO BE, and why it is gone. It read
#
#     .\build\Release\helpdata_bridge_smoke.exe
#
# and `helpdata_bridge_smoke` EXISTS NOWHERE IN THIS TREE -- not as a CMake
# target, not as a source file, not as a binary in any of the eleven build
# roots. Measured 2026-09-15. The script therefore configured, built, and then
# failed its only verification step, and had done so since at least 2026-05-06.
# It went unnoticed because the two lines above it succeed loudly: a wall of
# green MSBuild output ending in one red line reads as noise.
#
# This is the shape AIF-078 D10 already recorded in the sibling script:
# "a flag whose success looks identical whether the thing built or not -- the
# AIF-118 shape, in the build script." That note says build.ps1 is NOT fixed
# because a root script needs separate authorization. This one is fixed here
# because its last line could never have worked, which is not a judgement call.
#
# WHAT REPLACES IT. CMDHELPCHK is the HELP validator that actually exists and is
# registered: it checks the HELP catalogs against the command registry and is
# report-only. For a script named build_help that is the verification the dead
# line was reaching for.
#
# NOTE, because it is not obvious and it is the reason to keep this script:
# `cmake --build build` with no --target builds EVERYTHING. build.ps1 hardcodes
# `--target dottalkpp` plus its test list, so metacollect, the cost probes and
# memo_zoo are built HERE and not there. If a target is missing after build.ps1,
# this is the script that produces it.
#
# ONE COMMAND PER INVOCATION, never a -CommandLines array: --script is stdin
# redirection (main.cpp:195-213), so a nested std::cin read eats the following
# line and only the first command runs. That cost a cycle on 2026-08-12 and
# again on 2026-08-24.

cmake -S . -B build -G "Visual Studio 17 2022" -A x64
if ($LASTEXITCODE -ne 0) { throw "build_help: cmake configure failed ($LASTEXITCODE)" }

cmake --build build --config Release
if ($LASTEXITCODE -ne 0) {
    # NOT a throw. A locked output file -- dottalk_bbsd.exe while the daemon is
    # running is the common one -- fails one target and leaves the rest built.
    # Refusing to validate because of it would hide a good HELP build.
    Write-Warning "build_help: at least one target failed to build (exit $LASTEXITCODE)."
    Write-Warning "  A LNK1104 'cannot open file' usually means the binary is RUNNING. Stop it and re-run."
    Write-Warning "  Continuing to the HELP validation, which reads the store and the registry."
}

$exe = Join-Path $PSScriptRoot "build\src\Release\dottalkpp.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "build_help: $exe was not produced. Nothing to validate against."
}
Write-Host "build_help: validating HELP against the command registry (CMDHELPCHK)."
& (Join-Path $PSScriptRoot "datarun.ps1") -CommandLines "cmdhelpchk"
