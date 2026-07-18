#requires -Version 5.1
<#
  Pinocchio orchestrator -- generate (optional) -> build -> measure.

  Runs entirely in the Pinocchio lane (dbf/indexes/lmdb/tmp under .../pinocchio).
  Never touches the MCC sample foundation. Stages the freshly built exe via
  datarun.ps1, then DOTSCRIPT TRACEs the build and measure scripts, teeing
  transcripts to data/tmp/pinocchio/*.log.

  A zero exit code is NOT proof -- read the transcripts and confirm counts,
  the canary (50000000 Taylor Quinn), and per-command elapsed (SET TIMER ON).

  Usage:
    .\run_pinocchio.ps1                     # build + measure (data must exist)
    .\run_pinocchio.ps1 -Generate           # generate 1M first, then build+measure
    .\run_pinocchio.ps1 -Generate -Students 100000
#>
param(
  [string] $Root,
  [switch] $Generate,
  [switch] $Reset,
  [int]    $Students = 1000000,
  [string] $MachineType
)

if (-not $Root) {
  $Root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
}
$dataRoot = Join-Path $Root 'dottalkpp\data'

# lane dirs (derived, disposable)
foreach ($d in 'tmp\pinocchio','dbf\pinocchio','indexes\pinocchio','lmdb\pinocchio') {
  New-Item -ItemType Directory -Path (Join-Path $dataRoot $d) -Force | Out-Null
}

# Capture hardware as a first-class benchmark variable. A caller-supplied
# -MachineType is the stable lab label; CIM details remain supporting facts.
$machineProfile = [ordered]@{
  schema             = 'dottalk.pinocchio.machine_profile.v1'
  captured_at_utc    = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  capture_method     = 'environment_fallback'
  machine_type       = if ($MachineType) { $MachineType } else { $env:COMPUTERNAME }
  manufacturer       = ''
  model              = ''
  cpu                = $env:PROCESSOR_IDENTIFIER
  logical_processors = [int]$env:NUMBER_OF_PROCESSORS
  memory_gib         = $null
  os                 = [System.Environment]::OSVersion.VersionString
  os_version         = [System.Environment]::OSVersion.Version.ToString()
  historical_run_binding = 'CURRENT_RUN_ONLY'
}
try {
  $computer = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop
  $processor = Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -First 1
  $operatingSystem = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
  $machineProfile.capture_method = if ($MachineType) { 'machine_type_override_plus_windows_cim' } else { 'windows_cim' }
  $machineProfile.manufacturer = $computer.Manufacturer
  $machineProfile.model = $computer.Model
  if (-not $MachineType) {
    $machineProfile.machine_type = ("{0} {1}" -f $computer.Manufacturer, $computer.Model).Trim()
  }
  $machineProfile.cpu = $processor.Name
  $machineProfile.logical_processors = [int]$processor.NumberOfLogicalProcessors
  $machineProfile.memory_gib = [math]::Round($computer.TotalPhysicalMemory / 1GB, 1)
  $machineProfile.os = $operatingSystem.Caption
  $machineProfile.os_version = $operatingSystem.Version
} catch {
  $machineProfile.capture_warning = $_.Exception.Message
}
$machineProfilePath = Join-Path $dataRoot 'tmp\pinocchio\machine_profile.json'
$machineProfile | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $machineProfilePath -Encoding UTF8
Write-Host ("[machine] type={0} profile={1}" -f $machineProfile.machine_type, $machineProfilePath)

# -Reset clears the BUILT artifacts (tables, indexes, lmdb) so CDX CREATE /
# ADDTAG / BUILDLMDB build fresh over the imported rows. The generated CSVs
# under tmp are kept, so this does not force a regenerate.
if ($Reset) {
  Write-Host "[reset] clearing built pinocchio tables + indexes + lmdb (CSVs kept)..."
  foreach ($d in 'dbf\pinocchio','indexes\pinocchio','lmdb\pinocchio') {
    Get-ChildItem -Path (Join-Path $dataRoot $d) -Force -ErrorAction SilentlyContinue |
      Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  }
}

$studentsCsv = Join-Path $dataRoot 'tmp\pinocchio\students.csv'
if ($Generate -or -not (Test-Path -LiteralPath $studentsCsv)) {
  Write-Host "[1/3] Generating data ($Students students)..."
  & (Join-Path $PSScriptRoot 'gen_pinocchio_data.ps1') -Root $Root -Students $Students
} else {
  Write-Host "[1/3] Reusing existing data at tmp\pinocchio (pass -Generate to rebuild it)."
}

$stages = @(
  'DOTSCRIPT TRACE scripts\pinocchio\pinocchio_build.dts   OUT tmp\pinocchio\build.log',
  'DOTSCRIPT TRACE scripts\pinocchio\pinocchio_measure.dts OUT tmp\pinocchio\measure.log',
  'QUIT'
)

Write-Host "[2/3] Building x64 tables + CDX + LMDB (this is the timed build)..."
Write-Host "[3/3] Running the measure battery..."
& (Join-Path $Root 'datarun.ps1') -CommandLines $stages

Write-Host ""
Write-Host "Pinocchio run complete. Transcripts (READ THESE -- exit code is not proof):"
Write-Host "  data\tmp\pinocchio\build.log     (AUTODBF / CDX / BUILDLMDB + build timings)"
Write-Host "  data\tmp\pinocchio\measure.log   (query battery + per-command elapsed)"
Write-Host "  data\tmp\pinocchio\machine_profile.json (machine type, CPU, memory, OS)"
Write-Host ""
Write-Host "Confirm: STUDENTS COUNT == $Students; record 1 by SID = 50000000 Taylor Quinn;"
Write-Host "SHOW COLUMNS types sane; every BUILDLMDB OK; SMARTLIST in tag order."
