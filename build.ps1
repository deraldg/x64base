Param(
  [ValidateSet('Debug','Release')][string]$Config = 'Release',
  [switch]$UseNinja,
  [string]$BuildDir = '',
  [string]$VcpkgRoot = $env:VCPKG_ROOT,
  [string]$VcpkgTriplet = 'x64-windows',
  [string]$PythonExe = '',
  [switch]$NoIndex,
  [switch]$NoTV,
  [switch]$WithGui,
  [switch]$WithWx,
  [switch]$WithPyDotTalk
)

$ErrorActionPreference = 'Stop'
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

$Toolchain = $null
if (-not [string]::IsNullOrWhiteSpace($VcpkgRoot)) {
  $candidate = Join-Path $VcpkgRoot 'scripts\buildsystems\vcpkg.cmake'
  if (Test-Path $candidate) {
    $Toolchain = $candidate
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
} else {
  Write-Warning "vcpkg toolchain not found. Set VCPKG_ROOT or pass -VcpkgRoot."
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
  '-D', ('DOTTALK_WITH_GUI=' + ($(if ($WithGui) { 'ON' } else { 'OFF' }))),
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

if ($WithGui -or $WithWx) {
  $Targets += 'dottalk_gui_core'
  if ($Testing) {
    $Targets += 'dottalk_gui_core_async_smoke'
    # Guarded on the same switches as gui/core in src/tests/CMakeLists.txt
    # -- this one LINKS the library, so it does not exist without it.
    $Targets += 'dottalkpp_gui_match_count_test'
    $Targets += 'dottalkpp_gui_area_membership_test'
  }
}
if ($WithWx) { $Targets += 'dottalk_wb' }

# NOT GUI-CONDITIONAL: src/tests targets link nothing and exist purely under
# BUILD_TESTING.
#
# GAP, NAMED RATHER THAN PAPERED OVER: this script still does not build the
# OTHER src/tests targets. On 2026-08-23 `ctest` reported 17/17 green while
# this script had built at most four targets -- the other thirteen binaries
# were left over from an earlier full build. That is the SAME stale-artifact
# shape this script was fixed for, one directory across, and it is a
# pre-existing gap this lane did not create. Enumerating thirteen targets by
# hand is how a build script grows a list nobody maintains, and ALL_BUILD is
# wrong because it would build dottalk_wb_next, which is deliberately excluded.
# Recorded for a decision rather than guessed at.
if ($Testing) { $Targets += 'dottalkpp_relation_merge_test' }
if ($Testing) { $Targets += 'dottalkpp_area_alloc_test' }

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
