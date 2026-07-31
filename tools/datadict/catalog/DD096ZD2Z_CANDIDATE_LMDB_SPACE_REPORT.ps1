# DD096Z-D2Z candidate LMDB space report
# Read-only. No deletion.
$CandidateRoot = "D:\code\ccode\docs\datadict\candidates\DD096ZB-backup-and-inactive-candidate-staging-v0"
$CandidateLmdb = "D:\code\ccode\docs\datadict\candidates\DD096ZB-backup-and-inactive-candidate-staging-v0\lmdb"
Write-Host "DD096Z-D2Z candidate LMDB space report"
Write-Host "Candidate root: $CandidateRoot"
Write-Host "Candidate LMDB: $CandidateLmdb"
Write-Host ""
Write-Host "Drive space:"
Get-PSDrive -Name D | Format-Table Name,Used,Free,Provider,Root -AutoSize
Write-Host ""
Write-Host "Candidate LMDB top-level items:"
if (Test-Path $CandidateLmdb) {
  Get-ChildItem $CandidateLmdb -Force | ForEach-Object {
    $size = if ($_.PSIsContainer) { (Get-ChildItem $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum } else { $_.Length }
    [pscustomobject]@{ Name=$_.Name; Mode=$_.Mode; LastWriteTime=$_.LastWriteTime; Bytes=[int64]$size; Path=$_.FullName }
  } | Sort-Object Bytes -Descending | Format-Table Name,Mode,LastWriteTime,Bytes,Path -AutoSize
} else {
  Write-Host "Candidate LMDB path does not exist."
}
Write-Host ""
Write-Host "Candidate LMDB backups:"
$BackupRoot = Join-Path $CandidateLmdb "backups"
if (Test-Path $BackupRoot) {
  Get-ChildItem $BackupRoot -Force | ForEach-Object {
    $size = if ($_.PSIsContainer) { (Get-ChildItem $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum } else { $_.Length }
    [pscustomobject]@{ Name=$_.Name; Mode=$_.Mode; LastWriteTime=$_.LastWriteTime; Bytes=[int64]$size; Path=$_.FullName }
  } | Sort-Object Bytes -Descending | Format-Table Name,Mode,LastWriteTime,Bytes,Path -AutoSize
} else {
  Write-Host "No backups directory found."
}
