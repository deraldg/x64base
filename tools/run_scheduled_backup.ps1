<#
.SYNOPSIS
  Task Scheduler entrypoint for recurring DotTalk++ / x64base backups.

.DESCRIPTION
  Runs the curated backup scripts with logging. By default it runs the
  essential zipped backup to D:\backups.
#>

[CmdletBinding()]
param(
    [ValidateSet("Essential", "Source", "Both")]
    [string]$BackupKind = "Essential",
    [switch]$NoZip,

    # DEPRECATED, accepted and ignored. The backup scripts no longer reach into
    # D:\dev, so there is nothing to suppress. It stays declared because a
    # scheduled task registered before that change may still pass it, and an
    # unknown parameter would fail the task at run time rather than at edit time.
    [switch]$NoDev
)

$ErrorActionPreference = "Stop"

$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dropRoot = "D:\backups"
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

    # Not $args: that is an automatic variable, and assigning to it inside a
    # function shadows the caller's argument array.
    $scriptArgs = @("-DropRoot", $dropRoot)
    if (-not $NoZip) { $scriptArgs += "-Zip" }

    "Running: $ScriptPath $($scriptArgs -join ' ')" | Tee-Object -FilePath $logPath -Append
    & $ScriptPath @scriptArgs *>&1 | Tee-Object -FilePath $logPath -Append
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
