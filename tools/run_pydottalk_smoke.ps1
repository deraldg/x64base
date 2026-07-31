# tools/run_pydottalk_smoke.ps1
param(
  [Parameter(Mandatory = $false)]
  [string]$RepoRoot = (Get-Location).Path,

  [Parameter(Mandatory = $false)]
  [string]$BuildDir = "build",

  [Parameter(Mandatory = $false)]
  [ValidateSet("Debug", "Release", "RelWithDebInfo", "MinSizeRel")]
  [string]$Config = "Release",

  [Parameter(Mandatory = $false)]
  [string]$PythonExe = "",

  [Parameter(Mandatory = $false)]
  [string]$SmokeScript = "bindings\pydottalk_smoke.py",

  [Parameter(Mandatory = $false)]
  [string]$ModuleName = "pydottalk",

  [switch]$VerbosePaths
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$msg) { Write-Host $msg }
function Write-Warn([string]$msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Err([string]$msg)  { Write-Host $msg -ForegroundColor Red }

function Resolve-FullPath([string]$root, [string]$rel) {
  $p = Join-Path $root $rel
  return (Resolve-Path -LiteralPath $p -ErrorAction Stop).Path
}

function Find-Pyd([string]$root, [string]$buildRel, [string]$cfg, [string]$module) {
  $buildAbs = Join-Path $root $buildRel
  if (!(Test-Path $buildAbs)) { return $null }

  $pattern = "$module*.pyd"
  $candidates = Get-ChildItem -LiteralPath $buildAbs -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue |
    Where-Object {
      $_.FullName -notmatch '\\CMakeFiles\\' -and
      $_.FullName -notmatch '\\vcpkg_installed\\'
    }

  if (-not $candidates) { return $null }

  # Prefer ones under \Release\ (or chosen config), then shortest path.
  $preferred = $candidates |
    Sort-Object `
      @{ Expression = { if ($_.FullName -match "\\$cfg\\") { 0 } else { 1 } } }, `
      @{ Expression = { $_.FullName.Length } }

  return $preferred[0].FullName
}

function Prepend-EnvPath([string]$var, [string[]]$entries) {
  $cur = [Environment]::GetEnvironmentVariable($var, "Process")
  $curList = @()
  if ($cur) { $curList = $cur -split ';' | Where-Object { $_ -ne "" } }

  $newList = New-Object System.Collections.Generic.List[string]
  foreach ($e in $entries) {
    if ($e -and (Test-Path $e)) { $newList.Add((Resolve-Path $e).Path) }
  }

  foreach ($e in $curList) { $newList.Add($e) }

  # de-dupe preserving order
  $seen = @{}
  $dedup = @()
  foreach ($e in $newList) {
    $k = $e.ToLowerInvariant()
    if (-not $seen.ContainsKey($k)) {
      $seen[$k] = $true
      $dedup += $e
    }
  }

  [Environment]::SetEnvironmentVariable($var, ($dedup -join ';'), "Process")
}

function Get-Python([string]$py) {
  if ($py -and (Test-Path $py)) { return (Resolve-Path $py).Path }

  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Path }

  $cmd3 = Get-Command python3 -ErrorAction SilentlyContinue
  if ($cmd3) { return $cmd3.Path }

  return $null
}

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$py = Get-Python $PythonExe
if (-not $py) {
  Write-Err "Python not found. Pass -PythonExe <path-to-python.exe>."
  exit 2
}

$smokeAbs = Join-Path $RepoRoot $SmokeScript
if (!(Test-Path $smokeAbs)) {
  Write-Err "Smoke script not found: $smokeAbs"
  exit 2
}

$pyd = Find-Pyd $RepoRoot $BuildDir $Config $ModuleName
if (-not $pyd) {
  Write-Err "No '$ModuleName*.pyd' found under '$RepoRoot\$BuildDir'."
  Write-Info "Try building it:"
  Write-Info "  cmake --build $BuildDir --config $Config --target $ModuleName"
  exit 3
}

$pydDir = Split-Path -Parent $pyd

# Heuristic DLL paths for Windows
$vcpkgBin = Join-Path $RepoRoot "$BuildDir\vcpkg_installed\x64-windows\bin"
$vcpkgDbg = Join-Path $RepoRoot "$BuildDir\vcpkg_installed\x64-windows\debug\bin"

$binCfg1 = Join-Path $RepoRoot "$BuildDir\bin\$Config"
$binCfg2 = Join-Path $RepoRoot "$BuildDir\$Config"
$binCfg3 = $pydDir

Prepend-EnvPath "PYTHONPATH" @($pydDir)
Prepend-EnvPath "PATH" @($binCfg1, $binCfg2, $binCfg3, $vcpkgBin, $vcpkgDbg)

Write-Info "PY:  $py"
Write-Info "PYD: $pyd"
Write-Info "PYTHONPATH (prepended): $pydDir"

if ($VerbosePaths) {
  Write-Info ""
  Write-Info "PATH:"
  ($env:PATH -split ';') | Select-Object -First 25 | ForEach-Object { Write-Info "  $_" }
  Write-Info ""
  Write-Info "PYTHONPATH:"
  ($env:PYTHONPATH -split ';') | ForEach-Object { Write-Info "  $_" }
}

# Prove import resolves to the compiled extension.
$probe = @"
import importlib, sys
m = importlib.import_module("$ModuleName")
print("file   :", getattr(m, "__file__", None))
print("version:", getattr(m, "__version__", None))
print("has_xbase:", hasattr(m, "xbase"))
"@

Write-Info ""
Write-Info "=== Import probe ==="
& $py -c $probe
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Info ""
Write-Info "=== Running smoke: $smokeAbs ==="
& $py $smokeAbs
exit $LASTEXITCODE