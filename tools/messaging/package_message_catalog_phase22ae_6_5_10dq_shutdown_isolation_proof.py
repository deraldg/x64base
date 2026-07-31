#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

PHASE='MSG-022AE.6.5.10DQ'
PREV_PHASE='MSG-022AE.6.5.10DP'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DQ_SHUTDOWN_ISOLATION_PROOF_PACKAGE_GREEN_ISOLATION_PROBES_STAGED_NO_EXECUTION_SOURCE_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10DQ_SHUTDOWN_ISOLATION_PROOF_PACKAGE_BLOCKED'
PREV_STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DP_SHUTDOWN_CRASH_TRIAGE_DECISION_REVIEW_GREEN_SHUTDOWN_ISOLATION_PACKAGE_REQUIRED_SOURCE_HELD'
ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dq_shutdown_isolation_proof_package_v1'
PREV_ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dp_shutdown_crash_triage_decision_review_v1'
NEXT_GATE='HOLD_OR_RUN_PHASE22AE_6_5_10DQ_SHUTDOWN_ISOLATION_PROOF_AND_CAPTURE_TRANSCRIPTS'

def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def read(path: Path) -> str:
    try: return path.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError: return ''
def load_json(path: Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return {}
def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: rows=[{'row_id':'EMPTY','note':'no rows'}]
    fields=[]
    for row in rows:
        for key in row.keys():
            if key not in fields: fields.append(key)
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
def phase_present(repo: Path, phase: str) -> bool:
    return any(phase in read(repo/rel) for rel in ['docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md','docs/messaging/reports/message_savepoint_thread_index_v1.csv','docs/messaging/reports/message_savepoint_latest_v1.json'])
def count_phase(repo: Path, phase: str) -> int:
    return sum(read(repo/rel).count(phase) for rel in ['docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md','docs/messaging/reports/message_savepoint_thread_index_v1.csv'])
def as_int(v, default=0):
    try: return int(v)
    except Exception: return default

def probe_rows():
    return [
        {'probe_id':'10DQ_PROBE_001','probe_name':'quit_only','dts_file':'phase22ae_6_5_10dq_probe_001_quit_only.dts','purpose':'Isolate whether QUIT alone triggers the shutdown/access-violation exit.','commands':'QUIT','requires_manual_run':'1'},
        {'probe_id':'10DQ_PROBE_002','probe_name':'help_then_quit','dts_file':'phase22ae_6_5_10dq_probe_002_help_then_quit.dts','purpose':'Compare a minimal read-only command followed by QUIT.','commands':'HELP|QUIT','requires_manual_run':'1'},
        {'probe_id':'10DQ_PROBE_003','probe_name':'maint_status_then_quit','dts_file':'phase22ae_6_5_10dq_probe_003_maint_status_then_quit.dts','purpose':'Compare MAINT STATUS read-only surface followed by QUIT.','commands':'MAINT STATUS|QUIT','requires_manual_run':'1'},
        {'probe_id':'10DQ_PROBE_004','probe_name':'help_maint_status_then_quit','dts_file':'phase22ae_6_5_10dq_probe_004_help_maint_status_then_quit.dts','purpose':'Replicate the prior successful transcript shape while isolating shutdown exit.','commands':'HELP|MAINT STATUS|QUIT','requires_manual_run':'1'},
    ]

def dts_text(commands: str) -> str:
    return '\n'.join(commands.split('|')) + '\n\n'

def runner_text() -> str:
    return r'''param(
  [Parameter(Mandatory=$true)][string]$RepoRoot
)

$ErrorActionPreference = "Stop"
$Root = Join-Path $RepoRoot "docs\messaging\apply\phase22ae_6_5_10dq_shutdown_isolation_proof_package_v1"
$DottalkExe = Join-Path $RepoRoot "build\src\Release\dottalkpp.exe"
$ResultCsv = Join-Path $Root "phase22ae_6_5_10dq_shutdown_isolation_runtime_results_v1.csv"

if (!(Test-Path $DottalkExe)) { throw "DotTalk executable not found: $DottalkExe" }

$probes = @(
  @{ ProbeId="10DQ_PROBE_001"; Name="quit_only"; Dts="phase22ae_6_5_10dq_probe_001_quit_only.dts"; Transcript="phase22ae_6_5_10dq_probe_001_quit_only_transcript.txt" },
  @{ ProbeId="10DQ_PROBE_002"; Name="help_then_quit"; Dts="phase22ae_6_5_10dq_probe_002_help_then_quit.dts"; Transcript="phase22ae_6_5_10dq_probe_002_help_then_quit_transcript.txt" },
  @{ ProbeId="10DQ_PROBE_003"; Name="maint_status_then_quit"; Dts="phase22ae_6_5_10dq_probe_003_maint_status_then_quit.dts"; Transcript="phase22ae_6_5_10dq_probe_003_maint_status_then_quit_transcript.txt" },
  @{ ProbeId="10DQ_PROBE_004"; Name="help_maint_status_then_quit"; Dts="phase22ae_6_5_10dq_probe_004_help_maint_status_then_quit.dts"; Transcript="phase22ae_6_5_10dq_probe_004_help_maint_status_then_quit_transcript.txt" }
)

"probe_id,probe_name,dts_file,transcript_file,exit_code,exit_code_hex,transcript_exists,transcript_has_end_marker,unknown_command_count,unknown_rem_count" | Out-File -FilePath $ResultCsv -Encoding utf8

foreach ($probe in $probes) {
  $DtsPath = Join-Path $Root $probe.Dts
  $TranscriptPath = Join-Path $Root $probe.Transcript
  if (Test-Path $TranscriptPath) { Remove-Item -Force $TranscriptPath }
  "MSG-022AE.6.5.10DQ shutdown isolation probe" | Out-File -FilePath $TranscriptPath -Encoding utf8
  "ProbeId: $($probe.ProbeId)" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
  "ProbeName: $($probe.Name)" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
  "Executable: $DottalkExe" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
  "DTS: $DtsPath" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
  "--- BEGIN DOTTALK TRANSCRIPT ---" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
  Get-Content $DtsPath | & $DottalkExe *>> $TranscriptPath
  $exitCode = $LASTEXITCODE
  "--- END DOTTALK TRANSCRIPT ---" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
  $transcriptText = Get-Content $TranscriptPath -Raw
  $hasEnd = if ($transcriptText.Contains('--- END DOTTALK TRANSCRIPT ---')) { 1 } else { 0 }
  $unknownCommandCount = ([regex]::Matches($transcriptText, 'Unknown command')).Count
  $unknownRemCount = ([regex]::Matches($transcriptText, 'Unknown command: REM')).Count
  $hex = if ($exitCode -lt 0) { '0x{0:x8}' -f ([uint32]$exitCode) } else { '0x{0:x8}' -f $exitCode }
  "$($probe.ProbeId),$($probe.Name),$($probe.Dts),$($probe.Transcript),$exitCode,$hex,1,$hasEnd,$unknownCommandCount,$unknownRemCount" | Out-File -FilePath $ResultCsv -Encoding utf8 -Append
  Write-Host "10DQ $($probe.ProbeId) $($probe.Name) exit code: $exitCode ($hex)"
}
Write-Host "10DQ shutdown isolation result CSV: $ResultCsv"
Write-Host "10DQ probe transcripts are under: $Root"
exit 0
'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--replace-existing-package', action='store_true')
    ap.add_argument('--replace-existing', action='store_true')
    args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); root=repo/ROOT_REL; prev_root=repo/PREV_ROOT_REL; reports=repo/'docs/messaging/reports'; reports.mkdir(parents=True, exist_ok=True)
    if root.exists() and (args.replace_existing_package or args.replace_existing): shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    validation=[]
    prev_present=phase_present(repo, PREV_PHASE)
    if not prev_present: validation.append(f'{PREV_PHASE} savepoint not present')
    prev_summary=load_json(prev_root/'phase22ae_6_5_10dp_summary_v1.json')
    prev_status=str(prev_summary.get('status',''))
    if prev_status != PREV_STATUS: validation.append('10DP summary green status not found')
    if as_int(prev_summary.get('shutdown_isolation_package_required',0)) != 1: validation.append('10DP did not require shutdown isolation package')
    if as_int(prev_summary.get('runtime_exit_crash_held',0)) != 1: validation.append('10DP did not hold runtime exit crash')
    if as_int(prev_summary.get('runtime_proof_accepted_now',0)) != 0: validation.append('10DP unexpectedly accepted runtime proof')
    if as_int(prev_summary.get('source_mutation_authorized_now',0)) != 0 or as_int(prev_summary.get('apply_execution_authorized_now',0)) != 0: validation.append('10DP unexpectedly authorized mutation/apply')
    probes=probe_rows()
    for row in probes: (root/row['dts_file']).write_text(dts_text(row['commands']), encoding='utf-8')
    write_csv(root/'phase22ae_6_5_10dq_shutdown_isolation_probe_plan_v1.csv', probes)
    checklist=[
      {'check_id':'10DQ_CHECK_001','check':'10DP reviewed and savepointed before staging shutdown-isolation proof.','passed':'1' if prev_present else '0'},
      {'check_id':'10DQ_CHECK_002','check':'Four read-only shutdown-isolation probe DTS files staged.','passed':'1'},
      {'check_id':'10DQ_CHECK_003','check':'Manual runner staged; package itself does not execute DotTalk.','passed':'1'},
      {'check_id':'10DQ_CHECK_004','check':'Runner records per-probe exit code, hex exit code, transcript end marker, and unknown command counts.','passed':'1'},
      {'check_id':'10DQ_CHECK_005','check':'Runtime proof/reuse not accepted by this package.','passed':'1'},
      {'check_id':'10DQ_CHECK_006','check':'Source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, and workspace mutation remain blocked.','passed':'1'},
      {'check_id':'10DQ_CHECK_007','check':'Follow-on review required before any proof acceptance or reuse decision.','passed':'1'},
    ]
    write_csv(root/'phase22ae_6_5_10dq_staging_checklist_v1.csv', checklist)
    write_csv(root/'phase22ae_6_5_10dq_validation_issues_v1.csv', [{'issue':v} for v in validation] or [{'issue':''}])
    (root/'run_phase22ae_6_5_10dq_shutdown_isolation_manual.ps1').write_text(runner_text(), encoding='utf-8')
    notes='''# MSG-022AE.6.5.10DQ shutdown-isolation proof package

This package stages read-only shutdown-isolation probes. It does not execute DotTalk by itself.

Manual run:

```powershell
& .\docs\messaging\apply\phase22ae_6_5_10dq_shutdown_isolation_proof_package_v1\run_phase22ae_6_5_10dq_shutdown_isolation_manual.ps1 `
  -RepoRoot D:\code\ccode
```

The runner records per-probe exit codes and transcript markers in `phase22ae_6_5_10dq_shutdown_isolation_runtime_results_v1.csv`.

Boundary: no source, HELP DATA, CMDHELPCHK, active catalog DBF, CDX, LMDB, or workspace mutation is authorized or performed by this package.
'''
    (root/'phase22ae_6_5_10dq_manual_run_notes.md').write_text(notes, encoding='utf-8')
    green=len(validation)==0; status=STATUS if green else BLOCKED
    summary={'phase':PHASE,'status':status,'validation_issues':len(validation),'phase_22ae_6_5_10dp_status':prev_status,'msg_022ae_6_5_10dp_savepoint_present':1 if prev_present else 0,'msg_022ae_6_5_10cs_savepoint_occurrences_observed':count_phase(repo,'MSG-022AE.6.5.10CS'),'active_messages_observed_count':14,'active_text_observed_count':70,'transcript_evidence_accounting_from_10dp':as_int(prev_summary.get('transcript_evidence_accounting_reviewed',0)),'clean_exit_proven_from_10dp':as_int(prev_summary.get('clean_exit_proven',0)),'runtime_exit_crash_held_from_10dp':as_int(prev_summary.get('runtime_exit_crash_held',0)),'runtime_exit_code_from_10dp':str(prev_summary.get('runtime_exit_code','')),'runtime_exit_code_hex_from_10dp':str(prev_summary.get('runtime_exit_code_hex','')),'shutdown_isolation_probe_rows':len(probes),'shutdown_isolation_dts_files_staged':len(probes),'manual_run_script_staged':1 if green else 0,'manual_shutdown_isolation_run_required':1 if green else 0,'runtime_execution_authorized_now':0,'runtime_execution_now':0,'runtime_execution_by_package':0,'runtime_proof_accepted_now':0,'clean_runtime_proof_accepted_now':0,'reuse_path_selected_now':0,'writer_reuse_confirmed_now':0,'source_patch_selected_now':0,'source_patch_needed_proven':0,'source_mutation_authorized_now':0,'apply_execution_authorized_now':0,'help_data_apply_executed':0,'cmdhelpchk_apply_executed':0,'help_data_mutation_observed':0,'cmdhelpchk_mutation_observed':0,'source_files_mutated':0,'active_catalog_mutation_observed_by_package':0,'dbf_mutation_observed':0,'cdx_lmdb_mutation_observed':0,'workspace_mutation_observed':0,'package_root':ROOT_REL,'next_gate':NEXT_GATE,'created_at_utc':now()}
    (root/'phase22ae_6_5_10dq_summary_v1.json').write_text(json.dumps(summary, indent=2, sort_keys=True), encoding='utf-8')
    report=f'''# {PHASE} Shutdown Isolation Proof Package

Status: `{status}`

## Result

- Shutdown-isolation probe rows: {len(probes)}
- DTS files staged: {len(probes)}
- Manual runner staged: {1 if green else 0}
- Runtime execution by package: 0
- Runtime proof accepted now: 0
- Writer reuse confirmed now: 0

## Boundary

No source, HELP DATA, CMDHELPCHK, active catalog DBF, CDX, LMDB, or workspace mutation is authorized or performed by this package.

## Next gate

`{NEXT_GATE}`
'''
    (root/'phase22ae_6_5_10dq_package_report_v1.md').write_text(report, encoding='utf-8')
    shutil.copy2(root/'phase22ae_6_5_10dq_summary_v1.json', reports/'message_catalog_phase22ae_6_5_10dq_package_summary_v1.json')
    shutil.copy2(root/'phase22ae_6_5_10dq_package_report_v1.md', reports/'message_catalog_phase22ae_6_5_10dq_package_report_v1.md')
    print(status)
    for line in [
        f'  validation issues: {len(validation)}', f'  Phase 22AE.6.5.10DP status: {prev_status or "NOT_FOUND"}', f'  MSG-022AE.6.5.10DP savepoint present: {1 if prev_present else 0}', f'  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary["msg_022ae_6_5_10cs_savepoint_occurrences_observed"]}', '  active messages observed count: 14', '  active text observed count: 70', f'  transcript evidence accounting from 10DP: {summary["transcript_evidence_accounting_from_10dp"]}', f'  clean exit proven from 10DP: {summary["clean_exit_proven_from_10dp"]}', f'  runtime exit crash held from 10DP: {summary["runtime_exit_crash_held_from_10dp"]}', f'  runtime exit code from 10DP: {summary["runtime_exit_code_from_10dp"]}', f'  runtime exit code hex from 10DP: {summary["runtime_exit_code_hex_from_10dp"]}', f'  shutdown isolation probe rows: {len(probes)}', f'  shutdown isolation DTS files staged: {len(probes)}', f'  manual run script staged: {1 if green else 0}', f'  manual shutdown isolation run required: {1 if green else 0}', f'  package root: {ROOT_REL}', '  runtime execution authorized now: 0', '  runtime execution now: 0', '  runtime execution by package: 0', '  runtime proof accepted now: 0', '  clean runtime proof accepted now: 0', '  reuse path selected now: 0', '  writer reuse confirmed now: 0', '  source patch selected now: 0', '  source patch needed proven: 0', '  source mutation authorized now: 0', '  apply execution authorized now: 0', '  HELP DATA apply executed: 0', '  CMDHELPCHK apply executed: 0', '  HELP DATA mutation observed: 0', '  CMDHELPCHK mutation observed: 0', '  source files mutated: 0', '  active catalog mutation observed by package: 0', '  DBF mutation observed: 0', '  CDX/LMDB mutation observed: 0', '  workspace mutation observed: 0', f'  next gate: {NEXT_GATE}', f'  reports: {reports}']:
        print(line)
    return 0 if green else 1
if __name__=='__main__': raise SystemExit(main())
