Param(
  [ValidateSet('Debug','Release')][string]$Config = 'Release',
  [switch]$UseNinja,
  [string]$BuildDir = '',
  [string]$VcpkgRoot = $env:VCPKG_ROOT,
  [string]$VcpkgTriplet = 'x64-windows',
  [string]$PythonExe = '',
  [switch]$NoIndex,
  [switch]$NoTV,
  [switch]$NoGui,
  [switch]$WithGui,
  [switch]$WithWx,
  [switch]$WithPyDotTalk,
  [switch]$NoTests
)

$ErrorActionPreference = 'Stop'

# AIF-078, 2026-08-24 (steward: "-WithGui should be the default").
#
# The GUI used to be OFF unless asked for, and src/CMakeLists.txt:476 gates
# gui/core behind DOTTALK_WITH_GUI -- so a plain build did not COMPILE
# src/gui/core at all. Measured on 508325324: a build.ps1 run reported
# "Built OK" while session.obj was a full DAY older than dottalkpp.exe.
# Because the gate is at CONFIGURE time, even `cmake --build build` over the
# whole tree walked past it: 25 targets built, none of them the file that had
# just changed.
#
# The cost was not a slow build, it was SILENCE. ctest went 18 -> 20 the
# moment the GUI was switched on, and the two that appeared --
# dottalk_gui_core_async_smoke and dottalkpp_gui_match_count_test -- had not
# been failing. They had not been RUNNING, and nothing in a green summary
# said so. That is the same shape as REGRESSION ALL passing ten specs over a
# commit that rewrote the allocator without once exercising it.
#
# So the GUI now follows the house idiom for a feature that is ON: an opt-OUT
# switch, like -NoIndex and -NoTV. -WithGui is still ACCEPTED and still forces
# it on -- it is redundant now rather than wrong, and removing it would break
# every script and habit that spells it. -NoWx is NOT added: wxWidgets is a
# heavier dependency and DOTTALK_WITH_WX stays opt-in.
$GuiEnabled = (-not $NoGui) -or $WithGui
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if ([string]::IsNullOrWhiteSpace($BuildDir)) {
  if ($WithPyDotTalk) {
    $BuildDir = Join-Path $RepoRoot 'build-labtalk'
  } else {
    $BuildDir = Join-Path $RepoRoot 'build'
  }
}

if ($WithPyDotTalk -and [string]::IsNullOrWhiteSpace($PythonExe)) {
  $pythonCandidates = @(
    (Join-Path $RepoRoot 'build-labtalk\vcpkg_installed\x64-windows\tools\python3\python.exe'),
    (Join-Path $RepoRoot 'build\vcpkg_installed\x64-windows\tools\python3\python.exe'),
    $env:PYDOTTALK_PYTHON,
    $env:PY12,
    (Join-Path $RepoRoot 'pycrud\.venv\Scripts\python.exe')
  ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

  $PythonExe = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

# VCPKG RESOLUTION, IN ORDER, AND IT SAYS WHICH ONE WON.
#
# This used to read $env:VCPKG_ROOT and nothing else, which is how a build run
# from an SD card at H:\ccode silently linked against C:\Users\deral\vcpkg --
# correct on this machine, wrong on any other, and reported as a bare path with
# no hint of where it came from.
#
# TWO VARIABLES NAME THE SAME THING IN THIS REPO AND THAT IS THE REAL TRAP:
# build.ps1 read VCPKG_ROOT while every preset in CMakePresets.json reads
# $env{VCPKG_INSTALLATION_ROOT}. Setting one satisfied half the build system.
# Both are consulted here now.
#
# The last candidate is the useful one for a portable clone: a vcpkg sitting
# BESIDE the repo (<parent>\vcpkg). On a card laid out as X:\ccode + X:\vcpkg
# that resolves on any drive letter with no environment variable at all. On a
# normal checkout the sibling does not exist and this changes nothing.
$vcpkgCandidates = @(
  @{ src = '-VcpkgRoot / VCPKG_ROOT';     root = $VcpkgRoot },
  @{ src = 'VCPKG_INSTALLATION_ROOT';     root = $env:VCPKG_INSTALLATION_ROOT },
  @{ src = 'a vcpkg beside the repo';     root = (Join-Path (Split-Path -Parent $RepoRoot) 'vcpkg') }
)

$Toolchain = $null
$ToolchainSource = $null
foreach ($c in $vcpkgCandidates) {
  if ([string]::IsNullOrWhiteSpace($c.root)) { continue }
  $candidate = Join-Path $c.root 'scripts\buildsystems\vcpkg.cmake'
  if (Test-Path -LiteralPath $candidate) {
    $Toolchain = $candidate
    $ToolchainSource = $c.src
    break
  }
}

Write-Host "RepoRoot: $RepoRoot"
Write-Host "BuildDir: $BuildDir"
Write-Host "Config:   $Config"
Write-Host "Triplet:  $VcpkgTriplet"
if ($WithPyDotTalk) {
  if ($PythonExe) {
    Write-Host "Python:   $PythonExe"
  } else {
    Write-Warning "pydottalk build requested but no Python executable was resolved. CMake will try its default discovery."
  }
}
if ($Toolchain) {
  Write-Host "vcpkg:    $Toolchain"
  Write-Host "          (from $ToolchainSource)"
} else {
  Write-Warning "vcpkg toolchain not found. Set VCPKG_ROOT or VCPKG_INSTALLATION_ROOT, pass -VcpkgRoot, or put a vcpkg beside the repo."
}

$ManifestFeatures = @()
if (-not $NoIndex) { $ManifestFeatures += 'index' }
if (-not $NoTV) { $ManifestFeatures += 'tv' }
if ($WithWx) { $ManifestFeatures += 'wx' }
if ($WithPyDotTalk) { $ManifestFeatures += 'python' }
$ManifestFeatureValue = $ManifestFeatures -join ';'
if ($ManifestFeatureValue) {
  Write-Host "Features:  $ManifestFeatureValue"
}

# --- 1) Detect mixed-environment CMake cache and clean ---
$Cache = Join-Path $BuildDir 'CMakeCache.txt'
if ($UseNinja) {
  $RequestedGenerator = 'Ninja'
} else {
  $RequestedGenerator = 'Visual Studio 17 2022'
}
$RequestedPyDotTalk = if ($WithPyDotTalk) { 'ON' } else { 'OFF' }

if (Test-Path $Cache) {
  $cacheText = Get-Content $Cache -Raw
  $hasWSLPath = $cacheText -match '/mnt/' -or $cacheText -match '/home/'
  $hasWinPath = $cacheText -match '^[A-Z]:\\'
  $cwdIsWin   = $PWD.Path -match '^[A-Z]:\\'
  $generatorLine = ($cacheText -split "`r?`n" | Where-Object { $_ -like 'CMAKE_GENERATOR:*' } | Select-Object -First 1)
  $cacheGenerator = $null
  $cachedPyDotTalkLine = ($cacheText -split "`r?`n" | Where-Object { $_ -like 'BUILD_PYDOTTALK:*' } | Select-Object -First 1)
  $cachedPyDotTalk = $null
  if ($generatorLine) {
    $cacheGenerator = ($generatorLine -split '=', 2)[1]
  }
  if ($cachedPyDotTalkLine) {
    $cachedPyDotTalk = ($cachedPyDotTalkLine -split '=', 2)[1]
  }

  if ($cwdIsWin -and $hasWSLPath) {
    Write-Warning "CMakeCache points to WSL paths but you're in Windows PowerShell. Cleaning build/..."
    Remove-Item -Recurse -Force $BuildDir
  }
  elseif (-not $cwdIsWin -and $hasWinPath) {
    Write-Warning "CMakeCache points to Windows paths but you're in WSL. Cleaning build/..."
    Remove-Item -Recurse -Force $BuildDir
  }
  elseif ($cacheGenerator -and $cacheGenerator -ne $RequestedGenerator) {
    Write-Warning "CMakeCache generator '$cacheGenerator' does not match requested generator '$RequestedGenerator'. Cleaning build/..."
    Remove-Item -Recurse -Force $BuildDir
  }
  elseif ($cachedPyDotTalk -and $cachedPyDotTalk -ne $RequestedPyDotTalk) {
    Write-Warning "CMakeCache BUILD_PYDOTTALK='$cachedPyDotTalk' does not match requested BUILD_PYDOTTALK='$RequestedPyDotTalk'. Cleaning build/..."
    Remove-Item -Recurse -Force $BuildDir
  }
}

# Ensure build dir exists
if (!(Test-Path $BuildDir)) { New-Item -ItemType Directory -Path $BuildDir | Out-Null }

# --- 2) Configure ---
$generator = $RequestedGenerator

$configureArgs = @(
  '-S', $RepoRoot,
  '-B', $BuildDir,
  '-G', $generator,
  '-D', "CMAKE_BUILD_TYPE=$Config",
  '-D', ('DOTTALK_WITH_INDEX=' + ($(if ($NoIndex) { 'OFF' } else { 'ON' }))),
  '-D', ('DOTTALK_WITH_TV=' + ($(if ($NoTV) { 'OFF' } else { 'ON' }))),
  '-D', ('DOTTALK_WITH_GUI=' + ($(if ($GuiEnabled) { 'ON' } else { 'OFF' }))),
  '-D', ('DOTTALK_WITH_WX=' + ($(if ($WithWx) { 'ON' } else { 'OFF' }))),
  '-D', ('BUILD_PYDOTTALK=' + ($(if ($WithPyDotTalk) { 'ON' } else { 'OFF' }))),
  '-D', "DOTTALK_PROFILE=DEV"
)
if (-not $UseNinja) { $configureArgs += @('-A','x64') }
if ($Toolchain) {
  $configureArgs += @(
    '-D', "CMAKE_TOOLCHAIN_FILE=$Toolchain",
    '-D', "VCPKG_TARGET_TRIPLET=$VcpkgTriplet",
    '-D', "VCPKG_MANIFEST_FEATURES=$ManifestFeatureValue"
  )
}
if ($WithPyDotTalk -and $PythonExe) {
  $pythonRoot = Split-Path -Parent $PythonExe
  $configureArgs += @(
    '-D', "Python3_EXECUTABLE=$PythonExe",
    '-D', "Python3_ROOT_DIR=$pythonRoot",
    '-D', "Python_ROOT_DIR=$pythonRoot",
    '-D', 'Python3_FIND_REGISTRY=NEVER',
    '-D', 'Python3_FIND_VIRTUALENV=STANDARD'
  )
}

Write-Host ">>> Running CMake configure..."
cmake @configureArgs
if ($LASTEXITCODE -ne 0) {
  throw "CMake configure failed with exit code $LASTEXITCODE"
}

# --- 3) Build ---
#
# AIF-078, 2026-08-23 (steward: "fix it"). This block was a HARDCODED
# `--target dottalkpp` regardless of the switches, so -WithGui and -WithWx
# reached only the CONFIGURE step: they made the GUI targets exist in the
# solution and then never built them, while the summary above printed
# "DOTTALK_WITH_GUI : ON" / "DOTTALK_WITH_WX : ON" either way. A switch whose
# success looks identical whether the thing built or not is the same shape this
# lane keeps removing from the source -- and it is how a STALE
# dottalk_gui_core_async_smoke.exe reported PASS against a fixture that did not
# exist yet, 25 minutes before it was written.
#
# The target list is now DERIVED from the switches and PRINTED, so what the flag
# did is visible in the transcript instead of assumed. Guards mirror the CMake
# ones exactly (src/CMakeLists.txt:476-482): gui/core is added under
# DOTTALK_WITH_GUI *or* DOTTALK_WITH_WX, gui/wx only under DOTTALK_WITH_WX, and
# the async smoke target exists only when BUILD_TESTING is on -- which is read
# back from the CACHE rather than guessed, because naming a target that was
# never generated fails the whole build.
$Targets = @('dottalkpp')
if ($WithPyDotTalk) { $Targets += 'pydottalk' }

# BUILD_TESTING is read ONCE, here, and from the cache rather than guessed.
# It was previously read inside the GUI block, which meant a test target that
# is not GUI-conditional could not be reached at all.
$Testing = $false
$CacheFile = Join-Path $BuildDir 'CMakeCache.txt'
if (Test-Path $CacheFile) {
  $Testing = Select-String -Path $CacheFile -Pattern '^BUILD_TESTING:BOOL=ON' -Quiet
}

if ($GuiEnabled -or $WithWx) {
  $Targets += 'dottalk_gui_core'
  if ($Testing -and -not $NoTests) {
    # dottalk_gui_core_async_smoke is declared by src/gui, not src/tests, so it
    # is NOT in the derived list below and is still named here.
    # dottalkpp_gui_match_count_test and dottalkpp_gui_area_membership_test used
    # to be named here too. They are gone on purpose: src/tests only CREATES
    # them when gui/core exists, so the derived list already carries exactly the
    # same guard without restating it.
    $Targets += 'dottalk_gui_core_async_smoke'
  }
}
if ($WithWx) { $Targets += 'dottalk_wb' }

# THE GAP ABOVE IS CLOSED, 2026-09-11 (steward: "i was using .build to build").
#
# What stood here was a two-line hand-maintained list and a comment saying a
# hand-maintained list was the wrong answer. It named
# dottalkpp_relation_merge_test and dottalkpp_area_alloc_test out of the
# twenty-nine targets src/tests declares. The other twenty-seven were whatever
# an earlier full build had left on disk -- and on 2026-09-11 ctest reported
# dottalkpp_group_log_test PASSED from a binary compiled before eleven of that
# test's markers were written. A green suite that has not run the test is worse
# than a red one.
#
# The list is now DERIVED. src/tests/CMakeLists.txt writes every EXECUTABLE it
# created to build/test_targets.txt at configure time -- conditions included,
# so a target skipped for a missing VFP fixture or a GUI that is off is simply
# absent rather than named and unbuildable. Adding a test to src/tests adds it
# to this build with no edit to this file. See the reasoning at the end of
# src/tests/CMakeLists.txt.
#
# A MISSING FILE IS A THROW, NOT A SKIP. If BUILD_TESTING is ON and configure
# did not write the file, the only thing this script could do quietly is build
# no tests and let ctest grade yesterday's binaries -- which is the exact
# failure being removed. Configure runs above, unconditionally, and throws on
# its own failure, so reaching this with no file means something structural
# changed and the build should stop and say so.
if ($Testing -and -not $NoTests) {
  $TestTargetFile = Join-Path $BuildDir 'test_targets.txt'
  if (-not (Test-Path $TestTargetFile)) {
    throw ("BUILD_TESTING is ON but '$TestTargetFile' was not written by " +
           "configure. src/tests/CMakeLists.txt writes it last; a missing file " +
           "means this run would build no test binaries and ctest would grade " +
           "whatever is already on disk.")
  }
  $DerivedTests = @(Get-Content -LiteralPath $TestTargetFile |
                    ForEach-Object { $_.Trim() } |
                    Where-Object { $_ -ne '' })
  if ($DerivedTests.Count -eq 0) {
    throw "'$TestTargetFile' is empty: configure created no test executables."
  }
  Write-Host (">>> Test targets derived from configure: " + $DerivedTests.Count)
  $Targets += $DerivedTests
}
if ($Testing -and $NoTests) {
  # Opt-OUT, in the house idiom of -NoIndex / -NoTV / -NoGui. It does NOT turn
  # BUILD_TESTING off: the tests still exist and ctest will still run them.
  # That is precisely why it warns -- this switch is how a stale binary gets
  # graded green, and using it should be a decision, not a default.
  Write-Warning ("-NoTests: test binaries will NOT be rebuilt. Any ctest run " +
                 "after this build grades binaries from an earlier one.")
}

# Named twice is built twice; the GUI block and the derived list can overlap,
# and a target may be handed to MSBuild only once.
$Targets = @($Targets | Select-Object -Unique)

# OI-022, owner ruling 2026-09-20: leave `dottalk_bbsd` OUT of the house build
# and SAY SO, so the omission reads as a choice rather than an oversight.
#
# `DOTTALK_BUILD_BBSD` defaults ON and the target configures on every run, but
# this script builds seven targets and that is not one of them, so A CHANGE
# THAT BREAKS IT PASSES THIS BUILD IN SILENCE. That is the mirror of the
# standing rule that a single-target build never proves the other six: a target
# outside the seven is never proven at all.
#
# It is out ON PURPOSE. You cannot relink a running executable, so a daemon in
# the default list fails the build for everyone who has it up -- LNK1104,
# cannot open OUTPUT, which reads nothing like the missing symbol people expect
# and cost an afternoon once already. That is a bad trade for the many to cover
# the few who are actually touching bbsd. The hypothesis was in OI-022 from
# 2026-08-30 and nothing in this file said it; now it does.
#
# DERIVED, NOT ASSERTED. It reads the cache and the live target list rather
# than stating a fact that can rot: put `dottalk_bbsd` in $Targets some day and
# this notice removes itself. A hardcoded sentence here would be the same shape
# AIF-078 took out of this very block -- a summary that printed the same thing
# whether or not it was true.
$BbsdConfigured = $false
if (Test-Path $CacheFile) {
  $BbsdConfigured = Select-String -Path $CacheFile -Pattern '^DOTTALK_BUILD_BBSD:BOOL=ON' -Quiet
}
if ($BbsdConfigured -and ($Targets -notcontains 'dottalk_bbsd')) {
  Write-Host ">>> NOT BUILT HERE: dottalk_bbsd -- configured ON, deliberately outside this build."
  Write-Host ">>>   A running daemon holds its own exe open, so building it here would fail"
  Write-Host ">>>   for anyone with it up. Prove it yourself when you touch it:"
  Write-Host (">>>   cmake --build " + $BuildDir + " --config " + $Config + " --target dottalk_bbsd")
}

Write-Host (">>> Building target(s): " + ($Targets -join ', '))
if ($UseNinja) {
  cmake --build $BuildDir --target $Targets
} else {
  cmake --build $BuildDir --config $Config --target $Targets
}
if ($LASTEXITCODE -ne 0) {
  throw "CMake build failed with exit code $LASTEXITCODE"
}

# --- 4) Locate executable ---
$CandidatePaths = @(
  (Join-Path $BuildDir "bin\$Config\dottalkpp.exe"),
  (Join-Path $BuildDir "$Config\dottalkpp.exe"),
  (Join-Path $BuildDir "dottalkpp.exe"),
  (Join-Path $BuildDir "Release\dottalkpp.exe"),
  (Join-Path $BuildDir "Debug\dottalkpp.exe"),
  (Join-Path $BuildDir "src\$Config\dottalkpp.exe")
)

$exe = $null
foreach ($p in $CandidatePaths) { if (Test-Path $p) { $exe = $p; break } }

if ($exe) {
  Write-Host "Built OK: $exe"
} else {
  Write-Warning "Built, but couldn't find dottalkpp.exe in expected locations."
  Write-Host "Checked:"
  $CandidatePaths | ForEach-Object { Write-Host "  $_" }
}

if ($WithPyDotTalk) {
  $pydCandidates = @(
    (Join-Path $BuildDir "python\pydottalk.cp312-win_amd64.pyd"),
    (Join-Path $BuildDir "python\pydottalk.cp313-win_amd64.pyd"),
    (Join-Path $BuildDir "python\pydottalk.cp311-win_amd64.pyd"),
    (Join-Path $BuildDir "$Config\pydottalk.cp313-win_amd64.pyd"),
    (Join-Path $BuildDir "$Config\pydottalk.cp312-win_amd64.pyd"),
    (Join-Path $BuildDir "$Config\pydottalk.cp311-win_amd64.pyd")
  )

  $pyd = $pydCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if ($pyd) {
    Write-Host "Built OK: $pyd"
  } else {
    Write-Warning "Built with BUILD_PYDOTTALK=ON, but couldn't find the built pydottalk module in expected locations."
    $pydCandidates | ForEach-Object { Write-Host "  $_" }
  }
}
