param(
  [string]$PythonExe = "",
  [string]$RepoRoot = "",
  [string]$PydottalkBin = "",
  [string]$SandboxDir = "",
  [string]$X64Dir = ""
)

$ErrorActionPreference = "Stop"
$BindingsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent $BindingsDir }
if (-not $PydottalkBin) { $PydottalkBin = Join-Path $RepoRoot "build-labtalk\python" }
if (-not $SandboxDir) { $SandboxDir = Join-Path $RepoRoot "dottalkpp\data\dbf\sandbox" }
if (-not $X64Dir) { $X64Dir = Join-Path $RepoRoot "dottalkpp\data\dbf\x64" }

if (-not $PythonExe) {
  $pythonCandidates = @(
    (Join-Path $RepoRoot "build-labtalk\vcpkg_installed\x64-windows\tools\python3\python.exe"),
    (Join-Path $RepoRoot "build\vcpkg_installed\x64-windows\tools\python3\python.exe"),
    $env:PYDOTTALK_PYTHON,
    $env:PY12,
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
  ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
  if ($pythonCandidates.Count -gt 0) { $PythonExe = $pythonCandidates[0] }
}
if (-not $PythonExe) { throw "No Python executable resolved. Pass -PythonExe or set PYDOTTALK_PYTHON." }

$env:PYDOTTALK_BIN = $PydottalkBin
$env:PYTHONPATH = "$PydottalkBin;$BindingsDir"
$env:DOTTALK_SANDBOX_DBF_DIR = $SandboxDir

Write-Host "PythonExe=$PythonExe"
Write-Host "PYDOTTALK_BIN=$env:PYDOTTALK_BIN"
Write-Host "PYTHONPATH=$env:PYTHONPATH"
Write-Host "DOTTALK_SANDBOX_DBF_DIR=$env:DOTTALK_SANDBOX_DBF_DIR"

$scripts = @(
  "pydottalk_cursor_matrix_sandbox.py",
  "pydottalk_fixed_field_type_matrix_sandbox.py",
  "pydottalk_append_update_delete_lifecycle_sandbox.py",
  "pydottalk_error_contract_sandbox.py"
)
foreach ($script in $scripts) {
  & $PythonExe (Join-Path $BindingsDir $script)
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
& $PythonExe (Join-Path $BindingsDir "pydottalk_x64_read_matrix.py") --x64-dir $X64Dir --limit 20
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "OK: pydottalk non-memo proof suite completed."
