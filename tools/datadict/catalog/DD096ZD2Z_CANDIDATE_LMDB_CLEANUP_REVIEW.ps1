# DD096Z-D2Z candidate LMDB cleanup REVIEW script
# Preview only by default. Pass -ExecuteCandidateCleanup to delete candidate LMDB envdirs/backups.
param([switch]$ExecuteCandidateCleanup)
$CandidateRoot = "D:\code\ccode\docs\datadict\candidates\DD096ZB-backup-and-inactive-candidate-staging-v0"
$CandidateLmdb = "D:\code\ccode\docs\datadict\candidates\DD096ZB-backup-and-inactive-candidate-staging-v0\lmdb"
$ForbiddenActiveFragment = "dottalkpp\data\lmdb\datadict"
Write-Host "DD096Z-D2Z candidate LMDB cleanup"
Write-Host "Candidate root: $CandidateRoot"
Write-Host "Candidate LMDB: $CandidateLmdb"
Write-Host "ExecuteCandidateCleanup: $ExecuteCandidateCleanup"
if (-not (Test-Path $CandidateLmdb)) { throw "Candidate LMDB path does not exist: $CandidateLmdb" }
if ($CandidateLmdb.ToLowerInvariant().Contains($ForbiddenActiveFragment)) { throw "REFUSING active datadict LMDB path: $CandidateLmdb" }
if (-not $CandidateLmdb.ToLowerInvariant().Contains("docs\datadict\candidates")) { throw "REFUSING non-candidate LMDB path: $CandidateLmdb" }
$Targets = @()
$Targets += Get-ChildItem $CandidateLmdb -Force -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*.cdx.d" }
$BackupRoot = Join-Path $CandidateLmdb "backups"
if (Test-Path $BackupRoot) { $Targets += Get-ChildItem $BackupRoot -Force -Directory -ErrorAction SilentlyContinue }
Write-Host ""
Write-Host "Candidate-only cleanup targets:"
$Targets | ForEach-Object {
  $size = (Get-ChildItem $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
  [pscustomobject]@{ Name=$_.Name; LastWriteTime=$_.LastWriteTime; Bytes=[int64]$size; Path=$_.FullName }
} | Sort-Object Bytes -Descending | Format-Table Name,LastWriteTime,Bytes,Path -AutoSize
if (-not $ExecuteCandidateCleanup) {
  Write-Host ""
  Write-Host "Preview only. Rerun with -ExecuteCandidateCleanup to delete these candidate-only LMDB envdirs/backups."
  return
}
foreach ($Target in $Targets) {
  Write-Host "Removing candidate-only LMDB path: $($Target.FullName)"
  Remove-Item $Target.FullName -Recurse -Force
}
Write-Host "Cleanup complete. Re-run D2Y after confirming drive space."
Get-PSDrive -Name D | Format-Table Name,Used,Free,Provider,Root -AutoSize
