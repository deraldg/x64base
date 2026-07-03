<#
.SYNOPSIS
  Task Scheduler entrypoint for recurring DotTalk++ / x64base backups.

.DESCRIPTION
  Runs the curated backup scripts with logging. By default it runs the
  essential zipped backup to C:\Users\deral\OneDrive\ccode_drops.
#>

[CmdletBinding()]
param(
    [ValidateSet("Essential", "Source", "Both")]
    [string]$BackupKind = "Essential",
    [switch]$NoZip,
    [switch]$NoDev
)

$ErrorActionPreference = "Stop"

$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dropRoot = "C:\Users\deral\OneDrive\ccode_drops"
$logDir = Join-Path $dropRoot "logs"

if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = Join-Path $logDir ("scheduled_backup_{0}_{1}.log" -f $BackupKind.ToLowerInvariant(), $timestamp)

function Invoke-BackupScript {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptPath
    )

    $args = @("-DropRoot", $dropRoot)
    if (-not $NoZip) { $args += "-Zip" }
    if ($NoDev) { $args += "-NoDev" }

    "Running: $ScriptPath $($args -join ' ')" | Tee-Object -FilePath $logPath -Append
    & $ScriptPath @args *>&1 | Tee-Object -FilePath $logPath -Append
    if ($LASTEXITCODE -ne 0) {
        throw "Backup script failed with exit code $LASTEXITCODE: $ScriptPath"
    }
}

"Scheduled backup started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $logPath
"BackupKind: $BackupKind" | Tee-Object -FilePath $logPath -Append
"DropRoot: $dropRoot" | Tee-Object -FilePath $logPath -Append

switch ($BackupKind) {
    "Essential" {
        Invoke-BackupScript -ScriptPath (Join-Path $toolsDir "backup_essential_drop.ps1")
    }
    "Source" {
        Invoke-BackupScript -ScriptPath (Join-Path $toolsDir "backup_source_drop.ps1")
    }
    "Both" {
        Invoke-BackupScript -ScriptPath (Join-Path $toolsDir "backup_essential_drop.ps1")
        Invoke-BackupScript -ScriptPath (Join-Path $toolsDir "backup_source_drop.ps1")
    }
}

"Scheduled backup completed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $logPath -Append
"Log: $logPath" | Tee-Object -FilePath $logPath -Append
