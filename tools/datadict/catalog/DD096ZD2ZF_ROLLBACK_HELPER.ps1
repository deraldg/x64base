# DD096Z-D2ZF rollback helper
param(
  [Parameter(Mandatory=$true)][string]$BackupRoot,
  [switch]$ExecuteRollback
)
$ActiveDbf = 'D:\code\ccode\dottalkpp\data\datadict'
$ActiveIndexes = 'D:\code\ccode\dottalkpp\data\indexes\datadict'
$ActiveLmdb = 'D:\code\ccode\dottalkpp\data\lmdb\datadict'
if (-not $ExecuteRollback) {
  Write-Host 'Preview only. Rerun with -ExecuteRollback to restore backup artifacts.'
  return
}
if (-not (Test-Path $BackupRoot)) { throw "BackupRoot not found: $BackupRoot" }
Copy-Item (Join-Path $BackupRoot 'dbf\*') $ActiveDbf -Recurse -Force
Copy-Item (Join-Path $BackupRoot 'indexes\*') $ActiveIndexes -Recurse -Force
Copy-Item (Join-Path $BackupRoot 'lmdb\*') $ActiveLmdb -Recurse -Force
Write-Host 'Rollback copy complete. Run DDICT/workspace smoke.'
