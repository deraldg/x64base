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
    Write-Warning "CMakeCache points to WSL paths but you're in Windows PowerShell. Cleaning build/…"
    Remove-Item -Recurse -Force $BuildDir
  }
  elseif (-not $cwdIsWin -and $hasWinPath) {
    Write-Warning "CMakeCache points to Windows paths but you're in WSL. Cleaning build/…"
    Remove-Item -Recurse -Force $BuildDir
  }
  elseif ($cacheGenerator -and $cacheGenerator -ne $RequestedGenerator) {
    Write-Warning "CMakeCache generator '$cacheGenerator' does not match requested generator '$RequestedGenerator'. Cleaning build/…"
    Remove-Item -Recurse -Force $BuildDir
  }
  elseif ($cachedPyDotTalk -and $cachedPyDotTalk -ne $RequestedPyDotTalk) {
    Write-Warning "CMakeCache BUILD_PYDOTTALK='$cachedPyDotTalk' does not match requested BUILD_PYDOTTALK='$RequestedPyDotTalk'. Cleaning build/…"
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
Write-Host ">>> Building target dottalkpp..."
if ($UseNinja) {
  if ($WithPyDotTalk) {
    cmake --build $BuildDir --target dottalkpp pydottalk
  } else {
    cmake --build $BuildDir --target dottalkpp
  }
} else {
  if ($WithPyDotTalk) {
    cmake --build $BuildDir --config $Config --target dottalkpp pydottalk
  } else {
    cmake --build $BuildDir --config $Config --target dottalkpp
  }
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
