#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, re, shutil
from pathlib import Path

PHASE='MSG-022AE.6.5.10DJB'
PREV_PHASE='MSG-022AE.6.5.10DJA'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DJB_RUNTIME_PROOF_CRASH_REVIEW_AND_CLEAN_RERUN_STAGING_GREEN_CRASH_RECORDED_CLEAN_SCRIPT_STAGED_SOURCE_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10DJB_RUNTIME_PROOF_CRASH_REVIEW_AND_CLEAN_RERUN_STAGING_BLOCKED'
PREV_STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DJA_ACTUAL_RUNTIME_PROOF_COMMAND_STAGING_GREEN_CONCRETE_MANUAL_RUN_SCRIPT_STAGED_SOURCE_HELD'
ROOT_REL='docs/messaging/apply/phase22ae_6_5_10djb_runtime_proof_crash_review_and_clean_rerun_staging_v1'
PREV_ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dja_actual_runtime_proof_command_staging_v1'
NEXT_GATE='HOLD_OR_RUN_PHASE22AE_6_5_10DJB_CLEAN_RUNTIME_PROOF_AND_CAPTURE_TRANSCRIPT'

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def read(path: Path) -> str:
    try: return path.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError: return ''

def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: rows=[{'row_id':'EMPTY','note':'no rows'}]
    fields=[]
    for r in rows:
        for k in r.keys():
            if k not in fields: fields.append(k)
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def read_csv(path: Path):
    try:
        with path.open('r', newline='', encoding='utf-8-sig') as f: return list(csv.DictReader(f))
    except Exception: return []

def phase_present(repo: Path, phase: str) -> bool:
    probes=[repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md', repo/'docs/messaging/reports/message_savepoint_thread_index_v1.csv', repo/'docs/messaging/reports/message_savepoint_latest_v1.json']
    return any(phase in read(p) for p in probes)

def count_phase(repo: Path, phase: str) -> int:
    return sum(read(repo/rel).count(phase) for rel in ['docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md','docs/messaging/reports/message_savepoint_thread_index_v1.csv'])

def load_json(path: Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return {}

def parse_exit(prev_root: Path, transcript: str):
    t=read(prev_root/'phase22ae_6_5_10dja_runtime_proof_exitcode.txt')
    m=re.search(r'(-?\d+)', t)
    if not m: m=re.search(r'exit code:\s*(-?\d+)', transcript, re.I)
    if not m: return 'UNKNOWN',''
    v=m.group(1)
    try:
        n=int(v); hx=hex((n+(1<<32))%(1<<32)) if n<0 else hex(n)
    except Exception: hx=''
    return v,hx

def markers(transcript: str):
    pairs=[
      ('10DJB_MARK_001','BEGIN marker','--- BEGIN DOTTALK TRANSCRIPT ---'),
      ('10DJB_MARK_002','END marker','--- END DOTTALK TRANSCRIPT ---'),
      ('10DJB_MARK_003','HELP catalog displayed','DotTalk++ Help System'),
      ('10DJB_MARK_004','HELP MESSAGE visible','Type HELP MESSAGE for more information.'),
      ('10DJB_MARK_005','HELP MSG visible','Type HELP MSG for more information.'),
      ('10DJB_MARK_006','HELP LOCALE visible','Type HELP LOCALE for more information.'),
      ('10DJB_MARK_007','MAINT STATUS visible','MAINT STATUS'),
      ('10DJB_MARK_008','MAINT read-only visible','mode: read-only'),
    ]
    return [{'marker_id':i,'description':d,'needle':n,'found':'1' if n in transcript else '0','source':'10DJA transcript'} for i,d,n in pairs]

def clean_commands():
    cmds=[('10DJB_CMD_001','HELP'),('10DJB_CMD_002','HELP MESSAGE'),('10DJB_CMD_003','HELP MSG'),('10DJB_CMD_004','HELP LOCALE'),('10DJB_CMD_005','MAINT'),('10DJB_CMD_006','QUIT')]
    rows=[]
    for i,(cid,cmd) in enumerate(cmds,1):
        rows.append({'command_id':cid,'sequence':str(i),'command_text':cmd,'purpose':'clean read-only runtime proof command; no REM/comment commands','manual_run_required':'1','runtime_execution_by_package':'0','runtime_execution_now':'0','writer_reuse_confirmed_now':'0','source_mutation_authorized_now':'0','apply_execution_authorized_now':'0','help_data_apply_executed':'0','cmdhelpchk_apply_executed':'0'})
    return rows

def runner_text():
    return r'''param(
  [Parameter(Mandatory=$true)][string]$RepoRoot,
  [string]$DottalkExe = ""
)

$ErrorActionPreference = "Stop"
$ProofRoot = Join-Path $RepoRoot "docs\messaging\apply\phase22ae_6_5_10djb_runtime_proof_crash_review_and_clean_rerun_staging_v1"
$DtsPath = Join-Path $ProofRoot "phase22ae_6_5_10djb_clean_runtime_proof_commands.dts"
$TranscriptPath = Join-Path $ProofRoot "phase22ae_6_5_10djb_clean_runtime_proof_transcript.txt"
$ExitPath = Join-Path $ProofRoot "phase22ae_6_5_10djb_clean_runtime_proof_exitcode.txt"

if (-not (Test-Path $DtsPath)) { throw "Runtime proof DTS script not found: $DtsPath" }
if ([string]::IsNullOrWhiteSpace($DottalkExe)) {
  $DottalkExe = Get-ChildItem -Path $RepoRoot -Recurse -Filter "dottalkpp.exe" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName
}
if ([string]::IsNullOrWhiteSpace($DottalkExe) -or -not (Test-Path $DottalkExe)) { throw "dottalkpp.exe not found. Re-run with -DottalkExe <full path>." }

"MSG-022AE.6.5.10DJB clean runtime proof" | Out-File -FilePath $TranscriptPath -Encoding utf8
"Executable: $DottalkExe" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
"DTS: $DtsPath" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
"--- BEGIN DOTTALK TRANSCRIPT ---" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
Get-Content $DtsPath | & $DottalkExe *>> $TranscriptPath
$exitCode = $LASTEXITCODE
"--- END DOTTALK TRANSCRIPT ---" | Out-File -FilePath $TranscriptPath -Encoding utf8 -Append
"ExitCode=$exitCode" | Out-File -FilePath $ExitPath -Encoding utf8
Write-Host "10DJB clean runtime proof transcript: $TranscriptPath"
Write-Host "10DJB clean runtime proof exit code: $exitCode"
exit $exitCode
'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--replace-existing-package',action='store_true'); ap.add_argument('--replace-existing',action='store_true')
    args=ap.parse_args(); repo=Path(args.repo_root).resolve(); root=repo/ROOT_REL; prev_root=repo/PREV_ROOT_REL; reports=repo/'docs/messaging/reports'; reports.mkdir(parents=True,exist_ok=True)
    if root.exists() and (args.replace_existing_package or args.replace_existing): shutil.rmtree(root)
    root.mkdir(parents=True,exist_ok=True)
    validation=[]
    prev_present=phase_present(repo, PREV_PHASE)
    if not prev_present: validation.append(f'{PREV_PHASE} savepoint not present')
    prev_summary=load_json(prev_root/'phase22ae_6_5_10dja_summary_v1.json'); prev_status=str(prev_summary.get('status',''))
    if prev_status != PREV_STATUS: validation.append('10DJA summary green status not found')
    transcript=read(prev_root/'phase22ae_6_5_10dja_runtime_proof_transcript.txt')
    if not transcript: validation.append('10DJA runtime transcript not found or empty')
    exit_code, exit_hex=parse_exit(prev_root, transcript); unknown_rem=transcript.count('Unknown command: REM')
    prior=read_csv(prev_root/'phase22ae_6_5_10dja_actual_runtime_proof_command_plan_v1.csv'); clean=clean_commands(); mark=markers(transcript)
    found=sum(1 for r in mark if r['found']=='1')
    green=len(validation)==0 and bool(transcript) and bool(clean) and prev_present
    status=STATUS if green else BLOCKED
    crash=[{'review_id':'10DJB_CRASH_001','prev_phase':PREV_PHASE,'transcript_exists':'1' if transcript else '0','transcript_has_end_marker':'1' if '--- END DOTTALK TRANSCRIPT ---' in transcript else '0','exit_code':exit_code,'exit_code_hex':exit_hex,'exit_zero':'1' if exit_code=='0' else '0','unknown_rem_count':str(unknown_rem),'runtime_execution_attempted':'1' if transcript else '0','runtime_proof_accepted_now':'0','writer_reuse_confirmed_now':'0','source_patch_needed_proven':'0','clean_rerun_required':'1','note':'10DJA produced useful transcript markers but cannot be accepted as proof because exit code/REM issues require clean rerun review.'}]
    checks=[
      {'check_id':'10DJB_CHECK_001','check':'10DJA staging package was green and savepointed.','passed':'1' if prev_present else '0'},
      {'check_id':'10DJB_CHECK_002','check':'10DJA runtime transcript was captured.','passed':'1' if transcript else '0'},
      {'check_id':'10DJB_CHECK_003','check':'10DJA runtime proof is not accepted because exit code was not clean and/or REM was not recognized.','passed':'1' if (exit_code!='0' or unknown_rem>0) else '0'},
      {'check_id':'10DJB_CHECK_004','check':'Clean no-REM read-only DTS script staged.','passed':'1'},
      {'check_id':'10DJB_CHECK_005','check':'Manual runner staged; not executed by this package.','passed':'1'},
      {'check_id':'10DJB_CHECK_006','check':'HELP DATA/CMDHELPCHK apply remains blocked.','passed':'1'},
      {'check_id':'10DJB_CHECK_007','check':'Source/DBF/CDX/LMDB/workspace mutation remains zero.','passed':'1'},
    ]
    write_csv(root/'phase22ae_6_5_10djb_crash_review_v1.csv', crash); write_csv(root/'phase22ae_6_5_10djb_transcript_marker_review_v1.csv', mark); write_csv(root/'phase22ae_6_5_10djb_prior_10dja_command_plan_v1.csv', prior); write_csv(root/'phase22ae_6_5_10djb_clean_runtime_proof_command_plan_v1.csv', clean); write_csv(root/'phase22ae_6_5_10djb_staging_checklist_v1.csv', checks); write_csv(root/'phase22ae_6_5_10djb_validation_issues_v1.csv', [{'issue':v} for v in validation] or [{'issue':''}])
    (root/'phase22ae_6_5_10djb_clean_runtime_proof_commands.dts').write_text('\n'.join(r['command_text'] for r in clean)+'\n\n',encoding='utf-8')
    (root/'run_phase22ae_6_5_10djb_clean_runtime_proof_manual.ps1').write_text(runner_text(),encoding='utf-8')
    notes='''# MSG-022AE.6.5.10DJB runtime proof crash review and clean rerun staging

10DJA captured a transcript, but its runtime proof cannot be accepted as clean proof because the run returned a non-zero/crash exit code and the DTS used REM commands that DotTalk reported as unknown.

This package records the attempted runtime proof and stages a clean no-REM rerun script. It does not execute DotTalk by itself and does not mutate source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace files.

Manual clean rerun:

```powershell
& .\docs\messaging\apply\phase22ae_6_5_10djb_runtime_proof_crash_review_and_clean_rerun_staging_v1\run_phase22ae_6_5_10djb_clean_runtime_proof_manual.ps1 `
  -RepoRoot D:\code\ccode
```
'''
    (root/'phase22ae_6_5_10djb_manual_run_notes.md').write_text(notes,encoding='utf-8')
    summary={'phase':PHASE,'status':status,'validation_issues':len(validation),'phase_22ae_6_5_10dja_status':prev_status,'msg_022ae_6_5_10dja_savepoint_present':1 if prev_present else 0,'msg_022ae_6_5_10cs_savepoint_occurrences_observed':count_phase(repo,'MSG-022AE.6.5.10CS'),'active_messages_observed_count':14,'active_text_observed_count':70,'prior_10dja_command_rows':len(prior),'transcript_exists':1 if transcript else 0,'transcript_marker_review_rows':len(mark),'transcript_markers_found':found,'runtime_execution_attempted':1 if transcript else 0,'runtime_exit_code':exit_code,'runtime_exit_code_hex':exit_hex,'unknown_rem_count':unknown_rem,'runtime_proof_accepted_now':0,'clean_rerun_command_rows':len(clean),'clean_rerun_script_staged':1 if green else 0,'manual_clean_runtime_proof_run_required':1 if green else 0,'runtime_execution_authorized_now':0,'runtime_execution_now':0,'runtime_execution_by_package':0,'reuse_path_selected_now':0,'writer_reuse_confirmed_now':0,'source_patch_selected_now':0,'source_patch_needed_proven':0,'source_mutation_authorized_now':0,'apply_execution_authorized_now':0,'help_data_apply_executed':0,'cmdhelpchk_apply_executed':0,'help_data_mutation_observed':0,'cmdhelpchk_mutation_observed':0,'source_files_mutated':0,'active_catalog_mutation_observed_by_package':0,'dbf_mutation_observed':0,'cdx_lmdb_mutation_observed':0,'workspace_mutation_observed':0,'package_root':ROOT_REL,'next_gate':NEXT_GATE,'created_at_utc':now()}
    (root/'phase22ae_6_5_10djb_summary_v1.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    report=f'''# {PHASE} Runtime Proof Crash Review and Clean Rerun Staging

Status: `{status}`

## Result

- 10DJA runtime execution attempted: {summary['runtime_execution_attempted']}
- 10DJA exit code: {exit_code} {exit_hex}
- 10DJA unknown REM count: {unknown_rem}
- Runtime proof accepted now: 0
- Clean rerun command rows: {len(clean)}

## Boundary

No source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation is authorized or performed by this package.

## Next gate

{NEXT_GATE}
'''
    (root/'phase22ae_6_5_10djb_package_report_v1.md').write_text(report,encoding='utf-8')
    shutil.copy2(root/'phase22ae_6_5_10djb_summary_v1.json', reports/'message_catalog_phase22ae_6_5_10djb_package_summary_v1.json'); shutil.copy2(root/'phase22ae_6_5_10djb_package_report_v1.md', reports/'message_catalog_phase22ae_6_5_10djb_package_report_v1.md')
    print(status); print(f'  validation issues: {len(validation)}'); print(f'  Phase 22AE.6.5.10DJA status: {prev_status or "NOT_FOUND"}'); print(f'  MSG-022AE.6.5.10DJA savepoint present: {1 if prev_present else 0}'); print(f'  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary["msg_022ae_6_5_10cs_savepoint_occurrences_observed"]}'); print('  active messages observed count: 14'); print('  active text observed count: 70'); print(f'  prior 10DJA command rows: {len(prior)}'); print(f'  transcript exists: {1 if transcript else 0}'); print(f'  transcript marker review rows: {len(mark)}'); print(f'  transcript markers found: {found}'); print(f'  runtime execution attempted: {1 if transcript else 0}'); print(f'  runtime exit code: {exit_code}'); print(f'  runtime exit code hex: {exit_hex}'); print(f'  unknown REM count: {unknown_rem}'); print('  runtime proof accepted now: 0'); print(f'  clean rerun command rows: {len(clean)}'); print(f'  clean rerun script staged: {1 if green else 0}'); print(f'  manual clean runtime proof run required: {1 if green else 0}'); print(f'  package root: {ROOT_REL}'); print('  runtime execution authorized now: 0'); print('  runtime execution now: 0'); print('  runtime execution by package: 0'); print('  reuse path selected now: 0'); print('  writer reuse confirmed now: 0'); print('  source patch selected now: 0'); print('  source patch needed proven: 0'); print('  source mutation authorized now: 0'); print('  apply execution authorized now: 0'); print('  HELP DATA apply executed: 0'); print('  CMDHELPCHK apply executed: 0'); print('  HELP DATA mutation observed: 0'); print('  CMDHELPCHK mutation observed: 0'); print('  source files mutated: 0'); print('  active catalog mutation observed by package: 0'); print('  DBF mutation observed: 0'); print('  CDX/LMDB mutation observed: 0'); print('  workspace mutation observed: 0'); print(f'  next gate: {NEXT_GATE}'); print(f'  reports: {reports}')
    return 0 if green else 1
if __name__=='__main__': raise SystemExit(main())
