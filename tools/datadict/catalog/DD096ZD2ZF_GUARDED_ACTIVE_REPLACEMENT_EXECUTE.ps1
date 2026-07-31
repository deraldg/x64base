# DD096Z-D2ZF guarded active Data Dictionary replacement execution
param(
  [switch]$ExecuteActiveReplacement
)
$ErrorActionPreference = "Stop"
$CandidateDbf = 'D:\code\ccode\docs\datadict\candidates\DD096ZB-backup-and-inactive-candidate-staging-v0\dbf'
$CandidateIndexes = 'D:\code\ccode\docs\datadict\candidates\DD096ZB-backup-and-inactive-candidate-staging-v0\indexes'
$CandidateLmdb = 'D:\code\ccode\docs\datadict\candidates\DD096ZB-backup-and-inactive-candidate-staging-v0\lmdb'
$ActiveDbf = 'D:\code\ccode\dottalkpp\data\datadict'
$ActiveIndexes = 'D:\code\ccode\dottalkpp\data\indexes\datadict'
$ActiveLmdb = 'D:\code\ccode\dottalkpp\data\lmdb\datadict'
$BackupRoot = 'D:\code\ccode\docs\datadict\backups\DD096ZD2ZF-active-datadict-backup-20260529_115426'
$ReportRoot = 'D:\code\ccode\docs\datadict\reports\DD096ZD2ZF-guarded-active-replacement-execution-v0'

function Assert-Contains($PathValue, $Needle, $Label) {
  if (-not $PathValue.ToLowerInvariant().Contains($Needle.ToLowerInvariant())) {
    throw "$Label failed safety check: $PathValue"
  }
}
function Get-Status($PathValue) {
  if (-not (Test-Path $PathValue)) { return 'MISSING' }
  try { return [string]((Get-Content $PathValue -Raw | ConvertFrom-Json).status) } catch { return 'UNREADABLE' }
}
function Get-Bytes($PathValue) {
  if (-not (Test-Path $PathValue)) { return 0 }
  $item = Get-Item $PathValue -Force
  if (-not $item.PSIsContainer) { return [int64]$item.Length }
  return [int64]((Get-ChildItem $PathValue -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum)
}
function Get-HashOrBlank($PathValue) {
  if (Test-Path $PathValue -PathType Leaf) { return (Get-FileHash -Algorithm SHA256 $PathValue).Hash }
  return ''
}

Assert-Contains $CandidateDbf 'docs\datadict\candidates' 'candidate dbf'
Assert-Contains $CandidateIndexes 'docs\datadict\candidates' 'candidate indexes'
Assert-Contains $CandidateLmdb 'docs\datadict\candidates' 'candidate lmdb'
Assert-Contains $ActiveDbf 'dottalkpp\data\datadict' 'active dbf'
Assert-Contains $ActiveIndexes 'dottalkpp\data\indexes\datadict' 'active indexes'
Assert-Contains $ActiveLmdb 'dottalkpp\data\lmdb\datadict' 'active lmdb'
New-Item -ItemType Directory -Force -Path $ReportRoot | Out-Null

$Preconditions = @(
  [pscustomobject]@{ Lane='DD096ZD2ZC'; Path='docs\datadict\reports\DD096ZD2ZC-current-session-select-clean-tiny-rebuild-v0\dd096zd2zc_current_session_select_clean_tiny_rebuild_manifest.json'; Expected='DD096ZD2ZC_CURRENT_SESSION_SELECT_CLEAN_TINY_REBUILD_GREEN' },
  [pscustomobject]@{ Lane='DD096ZD2ZD'; Path='docs\datadict\reports\DD096ZD2ZD-candidate-promotion-readiness-gate-v0\dd096zd2zd_candidate_promotion_readiness_gate_manifest.json'; Expected='DD096ZD2ZD_CANDIDATE_PROMOTION_READINESS_READY' },
  [pscustomobject]@{ Lane='DD096ZD2ZE'; Path='docs\datadict\reports\DD096ZD2ZE-guarded-active-replacement-apply-plan-v0\dd096zd2ze_guarded_active_replacement_apply_plan_manifest.json'; Expected='DD096ZD2ZE_GUARDED_ACTIVE_REPLACEMENT_APPLY_PLAN_READY' }
)
$PreRows = @()
foreach ($p in $Preconditions) {
  $observed = Get-Status $p.Path
  $PreRows += [pscustomobject]@{ Lane=$p.Lane; Path=$p.Path; Expected=$p.Expected; Observed=$observed; Pass=[int]($observed -eq $p.Expected) }
}
$PreRows | Export-Csv (Join-Path $ReportRoot 'dd096zd2zf_precondition_ledger.csv') -NoTypeInformation
if (($PreRows | Where-Object { $_.Pass -ne 1 }).Count -gt 0) { throw 'Precondition failure. Refusing active replacement.' }

$CopyPlan = @(
  [pscustomobject]@{ Table='DATA_DICTIONARY_OBJECTS'; Kind='file'; Source=(Join-Path $CandidateDbf 'DATA_DICTIONARY_OBJECTS.dbf'); Target=(Join-Path $ActiveDbf 'DATA_DICTIONARY_OBJECTS.dbf'); Backup=(Join-Path $BackupRoot 'dbf\DATA_DICTIONARY_OBJECTS.dbf') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_OBJECTS'; Kind='file'; Source=(Join-Path $CandidateIndexes 'DATA_DICTIONARY_OBJECTS.cdx'); Target=(Join-Path $ActiveIndexes 'DATA_DICTIONARY_OBJECTS.cdx'); Backup=(Join-Path $BackupRoot 'indexes\DATA_DICTIONARY_OBJECTS.cdx') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_OBJECTS'; Kind='directory'; Source=(Join-Path $CandidateLmdb 'DATA_DICTIONARY_OBJECTS.cdx.d'); Target=(Join-Path $ActiveLmdb 'DATA_DICTIONARY_OBJECTS.cdx.d'); Backup=(Join-Path $BackupRoot 'lmdb\DATA_DICTIONARY_OBJECTS.cdx.d') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_OBJECT_ATTRIBUTES'; Kind='file'; Source=(Join-Path $CandidateDbf 'DATA_DICTIONARY_OBJECT_ATTRIBUTES.dbf'); Target=(Join-Path $ActiveDbf 'DATA_DICTIONARY_OBJECT_ATTRIBUTES.dbf'); Backup=(Join-Path $BackupRoot 'dbf\DATA_DICTIONARY_OBJECT_ATTRIBUTES.dbf') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_OBJECT_ATTRIBUTES'; Kind='file'; Source=(Join-Path $CandidateIndexes 'DATA_DICTIONARY_OBJECT_ATTRIBUTES.cdx'); Target=(Join-Path $ActiveIndexes 'DATA_DICTIONARY_OBJECT_ATTRIBUTES.cdx'); Backup=(Join-Path $BackupRoot 'indexes\DATA_DICTIONARY_OBJECT_ATTRIBUTES.cdx') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_OBJECT_ATTRIBUTES'; Kind='directory'; Source=(Join-Path $CandidateLmdb 'DATA_DICTIONARY_OBJECT_ATTRIBUTES.cdx.d'); Target=(Join-Path $ActiveLmdb 'DATA_DICTIONARY_OBJECT_ATTRIBUTES.cdx.d'); Backup=(Join-Path $BackupRoot 'lmdb\DATA_DICTIONARY_OBJECT_ATTRIBUTES.cdx.d') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_RELATION_EDGES'; Kind='file'; Source=(Join-Path $CandidateDbf 'DATA_DICTIONARY_RELATION_EDGES.dbf'); Target=(Join-Path $ActiveDbf 'DATA_DICTIONARY_RELATION_EDGES.dbf'); Backup=(Join-Path $BackupRoot 'dbf\DATA_DICTIONARY_RELATION_EDGES.dbf') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_RELATION_EDGES'; Kind='file'; Source=(Join-Path $CandidateIndexes 'DATA_DICTIONARY_RELATION_EDGES.cdx'); Target=(Join-Path $ActiveIndexes 'DATA_DICTIONARY_RELATION_EDGES.cdx'); Backup=(Join-Path $BackupRoot 'indexes\DATA_DICTIONARY_RELATION_EDGES.cdx') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_RELATION_EDGES'; Kind='directory'; Source=(Join-Path $CandidateLmdb 'DATA_DICTIONARY_RELATION_EDGES.cdx.d'); Target=(Join-Path $ActiveLmdb 'DATA_DICTIONARY_RELATION_EDGES.cdx.d'); Backup=(Join-Path $BackupRoot 'lmdb\DATA_DICTIONARY_RELATION_EDGES.cdx.d') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_EVIDENCE_RECORDS'; Kind='file'; Source=(Join-Path $CandidateDbf 'DATA_DICTIONARY_EVIDENCE_RECORDS.dbf'); Target=(Join-Path $ActiveDbf 'DATA_DICTIONARY_EVIDENCE_RECORDS.dbf'); Backup=(Join-Path $BackupRoot 'dbf\DATA_DICTIONARY_EVIDENCE_RECORDS.dbf') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_EVIDENCE_RECORDS'; Kind='file'; Source=(Join-Path $CandidateIndexes 'DATA_DICTIONARY_EVIDENCE_RECORDS.cdx'); Target=(Join-Path $ActiveIndexes 'DATA_DICTIONARY_EVIDENCE_RECORDS.cdx'); Backup=(Join-Path $BackupRoot 'indexes\DATA_DICTIONARY_EVIDENCE_RECORDS.cdx') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_EVIDENCE_RECORDS'; Kind='directory'; Source=(Join-Path $CandidateLmdb 'DATA_DICTIONARY_EVIDENCE_RECORDS.cdx.d'); Target=(Join-Path $ActiveLmdb 'DATA_DICTIONARY_EVIDENCE_RECORDS.cdx.d'); Backup=(Join-Path $BackupRoot 'lmdb\DATA_DICTIONARY_EVIDENCE_RECORDS.cdx.d') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_GATE_RECORDS'; Kind='file'; Source=(Join-Path $CandidateDbf 'DATA_DICTIONARY_GATE_RECORDS.dbf'); Target=(Join-Path $ActiveDbf 'DATA_DICTIONARY_GATE_RECORDS.dbf'); Backup=(Join-Path $BackupRoot 'dbf\DATA_DICTIONARY_GATE_RECORDS.dbf') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_GATE_RECORDS'; Kind='file'; Source=(Join-Path $CandidateIndexes 'DATA_DICTIONARY_GATE_RECORDS.cdx'); Target=(Join-Path $ActiveIndexes 'DATA_DICTIONARY_GATE_RECORDS.cdx'); Backup=(Join-Path $BackupRoot 'indexes\DATA_DICTIONARY_GATE_RECORDS.cdx') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_GATE_RECORDS'; Kind='directory'; Source=(Join-Path $CandidateLmdb 'DATA_DICTIONARY_GATE_RECORDS.cdx.d'); Target=(Join-Path $ActiveLmdb 'DATA_DICTIONARY_GATE_RECORDS.cdx.d'); Backup=(Join-Path $BackupRoot 'lmdb\DATA_DICTIONARY_GATE_RECORDS.cdx.d') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_RUNS'; Kind='file'; Source=(Join-Path $CandidateDbf 'DATA_DICTIONARY_RUNS.dbf'); Target=(Join-Path $ActiveDbf 'DATA_DICTIONARY_RUNS.dbf'); Backup=(Join-Path $BackupRoot 'dbf\DATA_DICTIONARY_RUNS.dbf') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_RUNS'; Kind='file'; Source=(Join-Path $CandidateIndexes 'DATA_DICTIONARY_RUNS.cdx'); Target=(Join-Path $ActiveIndexes 'DATA_DICTIONARY_RUNS.cdx'); Backup=(Join-Path $BackupRoot 'indexes\DATA_DICTIONARY_RUNS.cdx') },
  [pscustomobject]@{ Table='DATA_DICTIONARY_RUNS'; Kind='directory'; Source=(Join-Path $CandidateLmdb 'DATA_DICTIONARY_RUNS.cdx.d'); Target=(Join-Path $ActiveLmdb 'DATA_DICTIONARY_RUNS.cdx.d'); Backup=(Join-Path $BackupRoot 'lmdb\DATA_DICTIONARY_RUNS.cdx.d') }
)
$PlanRows = @()
foreach ($e in $CopyPlan) {
  $PlanRows += [pscustomobject]@{ Table=$e.Table; Kind=$e.Kind; Source=$e.Source; SourceExists=[int](Test-Path $e.Source); SourceBytes=Get-Bytes $e.Source; SourceSha256=Get-HashOrBlank $e.Source; Target=$e.Target; TargetExistsBefore=[int](Test-Path $e.Target); TargetBytesBefore=Get-Bytes $e.Target; TargetSha256Before=Get-HashOrBlank $e.Target; Backup=$e.Backup }
}
$PlanRows | Export-Csv (Join-Path $ReportRoot 'dd096zd2zf_execution_copy_plan.csv') -NoTypeInformation
if (($PlanRows | Where-Object { $_.SourceExists -ne 1 }).Count -gt 0) { throw 'Candidate source artifacts missing. Refusing active replacement.' }
if (-not $ExecuteActiveReplacement) {
  $manifest = [ordered]@{ contract='dd096zd2zf_guarded_active_replacement_execution_v0'; status='DD096ZD2ZF_ACTIVE_REPLACEMENT_PREVIEW_READY'; active_replacement_executed=0; backup_root=$BackupRoot; report_root=$ReportRoot; created_utc=(Get-Date).ToUniversalTime().ToString('s') + 'Z' }
  $manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $ReportRoot 'dd096zd2zf_active_replacement_execution_manifest.json')
  Write-Host 'Preview only. Rerun with -ExecuteActiveReplacement to perform backup and copy.'
  return
}

New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot 'dbf') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot 'indexes') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot 'lmdb') | Out-Null
$ActionRows = @()
foreach ($e in $CopyPlan) {
  New-Item -ItemType Directory -Force -Path (Split-Path $e.Backup -Parent) | Out-Null
  New-Item -ItemType Directory -Force -Path (Split-Path $e.Target -Parent) | Out-Null
  $backupPerformed = 0
  if (Test-Path $e.Target) { Copy-Item $e.Target $e.Backup -Recurse -Force; $backupPerformed = 1; Remove-Item $e.Target -Recurse -Force }
  Copy-Item $e.Source $e.Target -Recurse -Force
  $ActionRows += [pscustomobject]@{ Table=$e.Table; Kind=$e.Kind; Source=$e.Source; Target=$e.Target; Backup=$e.Backup; BackupPerformed=$backupPerformed; TargetExistsAfter=[int](Test-Path $e.Target); TargetBytesAfter=Get-Bytes $e.Target; TargetSha256After=Get-HashOrBlank $e.Target }
}
$ActionRows | Export-Csv (Join-Path $ReportRoot 'dd096zd2zf_execution_action_ledger.csv') -NoTypeInformation
$missingAfter = ($ActionRows | Where-Object { $_.TargetExistsAfter -ne 1 }).Count
$status = if ($missingAfter -eq 0) { 'DD096ZD2ZF_ACTIVE_REPLACEMENT_EXECUTED_PENDING_SMOKE' } else { 'DD096ZD2ZF_ACTIVE_REPLACEMENT_EXECUTION_REVIEW' }
$manifest = [ordered]@{ contract='dd096zd2zf_guarded_active_replacement_execution_v0'; status=$status; active_replacement_executed=1; missing_after_copy=$missingAfter; backup_root=$BackupRoot; report_root=$ReportRoot; created_utc=(Get-Date).ToUniversalTime().ToString('s') + 'Z' }
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $ReportRoot 'dd096zd2zf_active_replacement_execution_manifest.json')
Write-Host "DD096Z-D2ZF status: $status"
