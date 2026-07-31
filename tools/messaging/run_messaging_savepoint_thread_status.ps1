param(
  [Parameter(Mandatory=$true)][string]$RepoRoot
)

$reports = Join-Path $RepoRoot "docs\messaging\reports"
$journal = Join-Path $RepoRoot "docs\messaging\MESSAGING_SAVEPOINT_JOURNAL.md"
$index = Join-Path $reports "message_savepoint_thread_index_v1.csv"
$latest = Join-Path $reports "message_savepoint_latest_v1.json"

Write-Host "MESSAGING SAVEPOINT THREAD STATUS"
Write-Host "  journal exists:" (Test-Path $journal)
Write-Host "  index exists:  " (Test-Path $index)
Write-Host "  latest exists: " (Test-Path $latest)

if (Test-Path $index) {
  Import-Csv $index | Select-Object -Last 5 | Format-Table -AutoSize
}
if (Test-Path $latest) {
  Get-Content $latest
}
