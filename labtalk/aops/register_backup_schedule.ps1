<#
.SYNOPSIS
  Register or replace a Windows Task Scheduler job for recurring backups.

.EXAMPLES
  .\register_backup_schedule.ps1
  .\register_backup_schedule.ps1 -Frequency Daily -Time 19:00
  .\register_backup_schedule.ps1 -Frequency Weekly -DaysOfWeek Sunday -Time 19:00 -BackupKind Both
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet("Daily", "Weekly")]
    [string]$Frequency = "Weekly",

    [ValidateSet("Essential", "Source", "Both")]
    [string]$BackupKind = "Essential",

    [string]$Time = "19:00",

    [ValidateSet("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")]
    [string[]]$DaysOfWeek = @("Sunday"),

    [string]$TaskName = "DotTalkpp Essential Backup",

    [string]$Description = "Recurring DotTalk++ / x64base curated backup to OneDrive.",

    [switch]$NoZip,
    [switch]$NoDev
)

$ErrorActionPreference = "Stop"

$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $toolsDir "run_scheduled_backup.ps1"
if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "Missing runner script: $runner"
}

$at = [datetime]::ParseExact($Time, "HH:mm", [Globalization.CultureInfo]::InvariantCulture)

$runnerArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", ('"{0}"' -f $runner),
    "-BackupKind", $BackupKind
)
if ($NoZip) { $runnerArgs += "-NoZip" }
if ($NoDev) { $runnerArgs += "-NoDev" }

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument ($runnerArgs -join " ")

if ($Frequency -eq "Daily") {
    $trigger = New-ScheduledTaskTrigger -Daily -At $at
} else {
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DaysOfWeek -At $at
}

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    if ($PSCmdlet.ShouldProcess($TaskName, "Replace scheduled backup task")) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
}

if ($PSCmdlet.ShouldProcess($TaskName, "Register scheduled backup task")) {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description $Description | Out-Null
}

Write-Host "Backup schedule registered"
Write-Host "  TaskName   : $TaskName"
Write-Host "  Frequency  : $Frequency"
if ($Frequency -eq "Weekly") {
    Write-Host "  Days       : $($DaysOfWeek -join ', ')"
}
Write-Host "  Time       : $Time"
Write-Host "  BackupKind : $BackupKind"
Write-Host "  Runner     : $runner"
