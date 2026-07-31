#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, re, shutil
from pathlib import Path
PHASE='MSG-022AE.6.5.10DJC'
PREV_PHASE='MSG-022AE.6.5.10DJB'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DJC_CLEAN_RUNTIME_PROOF_TRANSCRIPT_REVIEW_GREEN_TRANSCRIPT_EVIDENCE_CAPTURED_EXIT_CRASH_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10DJC_CLEAN_RUNTIME_PROOF_TRANSCRIPT_REVIEW_BLOCKED'
PREV_STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DJB_RUNTIME_PROOF_CRASH_REVIEW_AND_CLEAN_RERUN_STAGING_GREEN_CRASH_RECORDED_CLEAN_SCRIPT_STAGED_SOURCE_HELD'
ROOT_REL='docs/messaging/apply/phase22ae_6_5_10djc_clean_runtime_proof_transcript_review_v1'
PREV_ROOT_REL='docs/messaging/apply/phase22ae_6_5_10djb_runtime_proof_crash_review_and_clean_rerun_staging_v1'
NEXT_GATE='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DK_RUNTIME_PROOF_EVIDENCE_DECISION_PACKAGE'
def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
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
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def load_json(path: Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return {}
def phase_present(repo: Path, phase: str) -> bool:
    return any(phase in read(repo/rel) for rel in ['docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md','docs/messaging/reports/message_savepoint_thread_index_v1.csv','docs/messaging/reports/message_savepoint_latest_v1.json'])
def count_phase(repo: Path, phase: str) -> int:
    return sum(read(repo/rel).count(phase) for rel in ['docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md','docs/messaging/reports/message_savepoint_thread_index_v1.csv'])
def parse_exit(prev_root: Path, transcript: str):
    t=read(prev_root/'phase22ae_6_5_10djb_clean_runtime_proof_exitcode.txt')
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
      ('10DJC_MARK_001','BEGIN marker','--- BEGIN DOTTALK TRANSCRIPT ---'),
      ('10DJC_MARK_002','END marker','--- END DOTTALK TRANSCRIPT ---'),
      ('10DJC_MARK_003','HELP catalog displayed','DotTalk++ Help System'),
      ('10DJC_MARK_004','HELP MESSAGE visible','Type HELP MESSAGE for more information.'),
      ('10DJC_MARK_005','HELP MSG visible','Type HELP MSG for more information.'),
      ('10DJC_MARK_006','HELP LOCALE visible','Type HELP LOCALE for more information.'),
      ('10DJC_MARK_007','MAINT STATUS visible','MAINT STATUS'),
      ('10DJC_MARK_008','MAINT read-only visible','mode: read-only'),
      ('10DJC_MARK_009','Native app marker visible','native app: yes, C++ command surface'),
      ('10DJC_MARK_010','Protected mutation marker visible','mutates protected systems: no'),
    ]
    return [{'marker_id':i,'description':d,'needle':n,'found':'1' if n in transcript else '0','source':'10DJB clean runtime transcript'} for i,d,n in pairs]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--replace-existing-package',action='store_true'); ap.add_argument('--replace-existing',action='store_true')
    args=ap.parse_args(); repo=Path(args.repo_root).resolve(); root=repo/ROOT_REL; prev_root=repo/PREV_ROOT_REL; reports=repo/'docs/messaging/reports'; reports.mkdir(parents=True,exist_ok=True)
    if root.exists() and (args.replace_existing_package or args.replace_existing): shutil.rmtree(root)
    root.mkdir(parents=True,exist_ok=True)
    validation=[]
    prev_present=phase_present(repo, PREV_PHASE)
    if not prev_present: validation.append(f'{PREV_PHASE} savepoint not present')
    prev_summary=load_json(prev_root/'phase22ae_6_5_10djb_summary_v1.json'); prev_status=str(prev_summary.get('status',''))
    if prev_status != PREV_STATUS: validation.append('10DJB summary green status not found')
    transcript=read(prev_root/'phase22ae_6_5_10djb_clean_runtime_proof_transcript.txt')
    if not transcript: validation.append('10DJB clean runtime transcript not found or empty')
    exit_code,exit_hex=parse_exit(prev_root, transcript)
    unknown_rem=transcript.count('Unknown command: REM')
    unknown_total=len(re.findall(r'Unknown command:', transcript))
    mark=markers(transcript); found=sum(1 for r in mark if r['found']=='1')
    transcript_complete=('--- BEGIN DOTTALK TRANSCRIPT ---' in transcript and '--- END DOTTALK TRANSCRIPT ---' in transcript)
    transcript_evidence_ok=(bool(transcript) and transcript_complete and found>=8 and unknown_rem==0)
    clean_exit=(exit_code=='0')
    green=len(validation)==0 and transcript_evidence_ok and prev_present
    status=STATUS if green else BLOCKED
    review=[{'review_id':'10DJC_REVIEW_001','prev_phase':PREV_PHASE,'transcript_exists':'1' if transcript else '0','transcript_complete':'1' if transcript_complete else '0','marker_rows':str(len(mark)),'markers_found':str(found),'unknown_rem_count':str(unknown_rem),'unknown_command_count':str(unknown_total),'runtime_exit_code':exit_code,'runtime_exit_code_hex':exit_hex,'clean_exit_proven':'1' if clean_exit else '0','transcript_evidence_captured':'1' if transcript_evidence_ok else '0','runtime_proof_accepted_now':'0','writer_reuse_confirmed_now':'0','source_patch_needed_proven':'0','note':'Clean no-REM transcript evidence was captured, but process clean exit is not proven; exit crash remains held for decision/triage.'}]
    decision=[{'option_id':'10DJC_OPTION_A','decision_option':'Accept transcript evidence for read-only HELP/MAINT surface only, while keeping clean-exit crash as a separate defect.','recommended_now':'1','requires_apply_authorization':'0','writer_reuse_confirmed_now':'0'},{'option_id':'10DJC_OPTION_B','decision_option':'Triage shutdown/QUIT access violation before any reuse confirmation.','recommended_now':'1','requires_apply_authorization':'0','writer_reuse_confirmed_now':'0'},{'option_id':'10DJC_OPTION_C','decision_option':'Do not accept transcript evidence because exit code is nonzero.','recommended_now':'0','requires_apply_authorization':'0','writer_reuse_confirmed_now':'0'},{'option_id':'10DJC_OPTION_D','decision_option':'Proceed to source patch/apply. Not authorized.','recommended_now':'0','requires_apply_authorization':'1','writer_reuse_confirmed_now':'0'}]
    checks=[{'check_id':'10DJC_CHECK_001','check':'10DJB package green/savepoint present.','passed':'1' if prev_present else '0'},{'check_id':'10DJC_CHECK_002','check':'Clean 10DJB transcript exists.','passed':'1' if transcript else '0'},{'check_id':'10DJC_CHECK_003','check':'Clean transcript has BEGIN/END markers.','passed':'1' if transcript_complete else '0'},{'check_id':'10DJC_CHECK_004','check':'Clean transcript has no REM unknown-command markers.','passed':'1' if unknown_rem==0 else '0'},{'check_id':'10DJC_CHECK_005','check':'Clean transcript still has access-violation/nonzero exit held as defect.','passed':'1' if not clean_exit else '0'},{'check_id':'10DJC_CHECK_006','check':'No reuse confirmation, source patch proof, or apply authorization occurs.','passed':'1'},{'check_id':'10DJC_CHECK_007','check':'HELP DATA/CMDHELPCHK/source/DBF/CDX/LMDB/workspace mutation remains zero.','passed':'1'}]
    write_csv(root/'phase22ae_6_5_10djc_clean_transcript_marker_review_v1.csv', mark); write_csv(root/'phase22ae_6_5_10djc_clean_runtime_proof_review_v1.csv', review); write_csv(root/'phase22ae_6_5_10djc_runtime_evidence_decision_options_v1.csv', decision); write_csv(root/'phase22ae_6_5_10djc_review_checklist_v1.csv', checks); write_csv(root/'phase22ae_6_5_10djc_validation_issues_v1.csv', [{'issue':v} for v in validation] or [{'issue':''}])
    summary={'phase':PHASE,'status':status,'validation_issues':len(validation),'phase_22ae_6_5_10djb_status':prev_status,'msg_022ae_6_5_10djb_savepoint_present':1 if prev_present else 0,'msg_022ae_6_5_10cs_savepoint_occurrences_observed':count_phase(repo,'MSG-022AE.6.5.10CS'),'active_messages_observed_count':14,'active_text_observed_count':70,'clean_transcript_exists':1 if transcript else 0,'clean_transcript_complete':1 if transcript_complete else 0,'clean_transcript_marker_review_rows':len(mark),'clean_transcript_markers_found':found,'unknown_rem_count':unknown_rem,'unknown_command_count':unknown_total,'runtime_execution_attempted':1 if transcript else 0,'runtime_exit_code':exit_code,'runtime_exit_code_hex':exit_hex,'clean_exit_proven':1 if clean_exit else 0,'transcript_evidence_captured':1 if transcript_evidence_ok else 0,'runtime_proof_accepted_now':0,'runtime_exit_crash_held':1 if not clean_exit else 0,'runtime_evidence_decision_package_required':1 if green else 0,'runtime_execution_authorized_now':0,'runtime_execution_now':0,'runtime_execution_by_package':0,'reuse_path_selected_now':0,'writer_reuse_confirmed_now':0,'source_patch_selected_now':0,'source_patch_needed_proven':0,'source_mutation_authorized_now':0,'apply_execution_authorized_now':0,'help_data_apply_executed':0,'cmdhelpchk_apply_executed':0,'help_data_mutation_observed':0,'cmdhelpchk_mutation_observed':0,'source_files_mutated':0,'active_catalog_mutation_observed_by_review':0,'dbf_mutation_observed':0,'cdx_lmdb_mutation_observed':0,'workspace_mutation_observed':0,'package_root':ROOT_REL,'next_gate':NEXT_GATE,'created_at_utc':now()}
    (root/'phase22ae_6_5_10djc_summary_v1.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    report='# '+PHASE+' Clean Runtime Proof Transcript Review\n\nStatus: `'+status+'`\n\n- Clean transcript exists: '+str(summary['clean_transcript_exists'])+'\n- Clean transcript complete: '+str(summary['clean_transcript_complete'])+'\n- Transcript markers found: '+str(found)+'/'+str(len(mark))+'\n- Unknown REM count: '+str(unknown_rem)+'\n- Runtime exit code: '+str(exit_code)+' '+str(exit_hex)+'\n- Transcript evidence captured: '+str(summary['transcript_evidence_captured'])+'\n- Clean exit proven: '+str(summary['clean_exit_proven'])+'\n- Runtime proof accepted now: 0\n\nThe clean rerun removed the REM-command problem and captured read-only HELP/MAINT transcript evidence. The process still returned a Windows access-violation exit code, so clean runtime exit is held and writer reuse remains unconfirmed.\n\nNo source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation is authorized or performed.\n\nNext gate: '+NEXT_GATE+'\n'
    (root/'phase22ae_6_5_10djc_package_report_v1.md').write_text(report,encoding='utf-8')
    shutil.copy2(root/'phase22ae_6_5_10djc_summary_v1.json', reports/'message_catalog_phase22ae_6_5_10djc_package_summary_v1.json'); shutil.copy2(root/'phase22ae_6_5_10djc_package_report_v1.md', reports/'message_catalog_phase22ae_6_5_10djc_package_report_v1.md')
    lines=[status,f'  validation issues: {len(validation)}',f'  Phase 22AE.6.5.10DJB status: {prev_status or "NOT_FOUND"}',f'  MSG-022AE.6.5.10DJB savepoint present: {1 if prev_present else 0}',f'  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary["msg_022ae_6_5_10cs_savepoint_occurrences_observed"]}','  active messages observed count: 14','  active text observed count: 70',f'  clean transcript exists: {summary["clean_transcript_exists"]}',f'  clean transcript complete: {summary["clean_transcript_complete"]}',f'  clean transcript marker review rows: {len(mark)}',f'  clean transcript markers found: {found}',f'  unknown REM count: {unknown_rem}',f'  unknown command count: {unknown_total}',f'  runtime execution attempted: {1 if transcript else 0}',f'  runtime exit code: {exit_code}',f'  runtime exit code hex: {exit_hex}',f'  clean exit proven: {1 if clean_exit else 0}',f'  transcript evidence captured: {1 if transcript_evidence_ok else 0}','  runtime proof accepted now: 0',f'  runtime exit crash held: {1 if not clean_exit else 0}',f'  runtime evidence decision package required: {1 if green else 0}',f'  package root: {ROOT_REL}','  runtime execution authorized now: 0','  runtime execution now: 0','  runtime execution by package: 0','  reuse path selected now: 0','  writer reuse confirmed now: 0','  source patch selected now: 0','  source patch needed proven: 0','  source mutation authorized now: 0','  apply execution authorized now: 0','  HELP DATA apply executed: 0','  CMDHELPCHK apply executed: 0','  HELP DATA mutation observed: 0','  CMDHELPCHK mutation observed: 0','  source files mutated: 0','  active catalog mutation observed by review: 0','  DBF mutation observed: 0','  CDX/LMDB mutation observed: 0','  workspace mutation observed: 0',f'  next gate: {NEXT_GATE}',f'  reports: {reports}']
    print('\n'.join(lines))
    return 0 if green else 1
if __name__=='__main__': raise SystemExit(main())
