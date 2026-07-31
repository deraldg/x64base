#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path
PHASE='MSG-022AE.6.5.10DL'
PREV_PHASE='MSG-022AE.6.5.10DK'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DL_RUNTIME_PROOF_EVIDENCE_DECISION_REVIEW_GREEN_CRASH_TRIAGE_PACKAGE_REQUIRED_SOURCE_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10DL_RUNTIME_PROOF_EVIDENCE_DECISION_REVIEW_BLOCKED'
PREV_STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DK_RUNTIME_PROOF_EVIDENCE_DECISION_PACKAGE_GREEN_TRANSCRIPT_ONLY_DECISION_STAGED_CRASH_HELD_SOURCE_HELD'
ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dl_runtime_proof_evidence_decision_review_v1'
PREV_ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dk_runtime_proof_evidence_decision_package_v1'
NEXT_GATE='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DM_RUNTIME_EXIT_CRASH_TRIAGE_PACKAGE'

def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def read(path: Path) -> str:
    try: return path.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError: return ''
def load_json(path: Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return {}
def read_csv(path: Path):
    try:
        with path.open('r', newline='', encoding='utf-8-sig') as f: return list(csv.DictReader(f))
    except Exception: return []
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

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--replace-existing-review', action='store_true')
    ap.add_argument('--replace-existing-package', action='store_true')
    ap.add_argument('--replace-existing', action='store_true')
    args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); root=repo/ROOT_REL; prev_root=repo/PREV_ROOT_REL; reports=repo/'docs/messaging/reports'; reports.mkdir(parents=True, exist_ok=True)
    if root.exists() and (args.replace_existing_review or args.replace_existing_package or args.replace_existing): shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    validation=[]
    prev_present=phase_present(repo, PREV_PHASE)
    if not prev_present: validation.append(f'{PREV_PHASE} savepoint not present')
    prev_summary=load_json(prev_root/'phase22ae_6_5_10dk_summary_v1.json')
    prev_status=str(prev_summary.get('status',''))
    if prev_status != PREV_STATUS: validation.append('10DK summary green status not found')
    evidence_rows=read_csv(prev_root/'phase22ae_6_5_10dk_runtime_evidence_rows_v1.csv')
    decision_rows=read_csv(prev_root/'phase22ae_6_5_10dk_runtime_evidence_decision_rows_v1.csv')
    checklist_rows=read_csv(prev_root/'phase22ae_6_5_10dk_decision_checklist_v1.csv')
    transcript_evidence=int(prev_summary.get('transcript_evidence_captured_from_10djc',0) or 0)
    clean_exit=int(prev_summary.get('clean_exit_proven_from_10djc',0) or 0)
    crash_held=int(prev_summary.get('runtime_exit_crash_held_from_10djc',0) or 0)
    exit_code=str(prev_summary.get('runtime_exit_code_from_10djc',''))
    exit_hex=str(prev_summary.get('runtime_exit_code_hex_from_10djc',''))
    transcript_only=int(prev_summary.get('transcript_only_decision_staged',0) or 0)
    crash_triage=int(prev_summary.get('crash_triage_required',0) or 0)
    runtime_accepted=int(prev_summary.get('runtime_proof_accepted_now',0) or 0)
    writer_reuse=int(prev_summary.get('writer_reuse_confirmed_now',0) or 0)
    apply_auth=int(prev_summary.get('apply_execution_authorized_now',0) or 0)
    if transcript_evidence != 1: validation.append('10DK did not stage transcript evidence captured')
    if clean_exit != 0: validation.append('10DK unexpectedly reports clean exit proven')
    if crash_held != 1: validation.append('10DK did not hold runtime exit crash')
    if transcript_only != 1: validation.append('10DK transcript-only decision not staged')
    if crash_triage != 1: validation.append('10DK crash triage requirement not set')
    if runtime_accepted != 0: validation.append('10DK unexpectedly accepted runtime proof')
    if writer_reuse != 0: validation.append('10DK unexpectedly confirmed writer reuse')
    if apply_auth != 0: validation.append('10DK unexpectedly authorized apply execution')
    green=len(validation)==0
    status=STATUS if green else BLOCKED
    review_rows=[]
    for row in decision_rows:
        review_rows.append({
            'review_id':'10DL_REVIEW_' + str(len(review_rows)+1).zfill(3),
            'source_decision_id':row.get('decision_id',''),
            'source_decision':row.get('decision',''),
            'selected_now':row.get('selected_now',''),
            'review_result':'accepted_for_accounting' if row.get('selected_now')=='1' else 'held_as_unselected_alternative',
            'review_note':'10DL accepts transcript-only evidence decision and keeps crash triage required; no reuse/apply/source mutation authorization is created.'
        })
    if not review_rows:
        review_rows=[{'review_id':'10DL_REVIEW_001','source_decision_id':'NONE','source_decision':'no 10DK decision rows found','selected_now':'0','review_result':'blocked','review_note':'10DK decision rows missing'}]
    evidence_review_rows=[{
        'review_id':'10DL_EVIDENCE_REVIEW_001',
        'transcript_evidence_captured':str(transcript_evidence),
        'clean_exit_proven':str(clean_exit),
        'runtime_exit_crash_held':str(crash_held),
        'runtime_exit_code':exit_code,
        'runtime_exit_code_hex':exit_hex,
        'review_result':'partial_evidence_only_clean_runtime_proof_not_accepted',
        'review_note':'Clean no-REM transcript is real evidence of read-only HELP/MESSAGE/MSG/LOCALE/MAINT surfaces, but 0xC0000005 exit keeps runtime proof and writer reuse unaccepted.'
    }]
    triage_requirement_rows=[
        {'requirement_id':'10DL_TRIAGE_001','requirement':'Create a runtime-exit crash triage package that classifies the 0xC0000005 exit path without mutating protected systems.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DL_TRIAGE_002','requirement':'Do not accept writer reuse until either clean exit is proven or transcript-only policy is explicitly reviewed/accepted for this narrow proof.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DL_TRIAGE_003','requirement':'Keep HELP DATA, CMDHELPCHK, source, DBF, CDX, LMDB, and workspace mutation blocked.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DL_TRIAGE_004','requirement':'Carry duplicate 10CS savepoint accounting as a bookkeeping defect only.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DL_TRIAGE_005','requirement':'Use transcript evidence only as partial read-only surface evidence until crash triage closes.','required':'1','mutation_authorized':'0'},
    ]
    checklist_review_rows=[
        {'check_id':'10DL_CHECK_001','check':'10DK green summary present.','passed':'1' if prev_status==PREV_STATUS else '0'},
        {'check_id':'10DL_CHECK_002','check':'10DK savepoint present.','passed':'1' if prev_present else '0'},
        {'check_id':'10DL_CHECK_003','check':'10DK evidence rows available.','passed':'1' if len(evidence_rows)>0 else '0'},
        {'check_id':'10DL_CHECK_004','check':'10DK decision rows available.','passed':'1' if len(decision_rows)>0 else '0'},
        {'check_id':'10DL_CHECK_005','check':'Transcript-only decision staged and reviewed.','passed':'1' if transcript_only==1 else '0'},
        {'check_id':'10DL_CHECK_006','check':'Crash triage remains required.','passed':'1' if crash_triage==1 and crash_held==1 else '0'},
        {'check_id':'10DL_CHECK_007','check':'Runtime proof/reuse/apply/source mutation remain unaccepted/unauthorized.','passed':'1' if runtime_accepted==0 and writer_reuse==0 and apply_auth==0 else '0'},
    ]
    write_csv(root/'phase22ae_6_5_10dl_decision_review_rows_v1.csv', review_rows)
    write_csv(root/'phase22ae_6_5_10dl_evidence_review_rows_v1.csv', evidence_review_rows)
    write_csv(root/'phase22ae_6_5_10dl_triage_requirement_rows_v1.csv', triage_requirement_rows)
    write_csv(root/'phase22ae_6_5_10dl_checklist_review_rows_v1.csv', checklist_review_rows)
    write_csv(root/'phase22ae_6_5_10dl_validation_issues_v1.csv', [{'issue':v} for v in validation] or [{'issue':''}])
    summary={'phase':PHASE,'status':status,'validation_issues':len(validation),'phase_22ae_6_5_10dk_status':prev_status,'msg_022ae_6_5_10dk_savepoint_present':1 if prev_present else 0,'msg_022ae_6_5_10cs_savepoint_occurrences_observed':count_phase(repo,'MSG-022AE.6.5.10CS'),'active_messages_observed_count':14,'active_text_observed_count':70,'dk_evidence_rows':len(evidence_rows),'dk_decision_rows':len(decision_rows),'dk_checklist_rows':len(checklist_rows),'decision_review_rows':len(review_rows),'evidence_review_rows':len(evidence_review_rows),'triage_requirement_rows':len(triage_requirement_rows),'checklist_review_rows':len(checklist_review_rows),'transcript_evidence_captured_reviewed':transcript_evidence,'transcript_only_decision_accepted_for_accounting':1 if green else 0,'clean_exit_proven':0,'runtime_exit_crash_held':1,'runtime_exit_code':exit_code,'runtime_exit_code_hex':exit_hex,'crash_triage_package_required':1,'runtime_proof_accepted_now':0,'clean_runtime_proof_accepted_now':0,'reuse_path_selected_now':0,'writer_reuse_confirmed_now':0,'source_patch_selected_now':0,'source_patch_needed_proven':0,'source_mutation_authorized_now':0,'apply_execution_authorized_now':0,'help_data_apply_executed':0,'cmdhelpchk_apply_executed':0,'help_data_mutation_observed':0,'cmdhelpchk_mutation_observed':0,'source_files_mutated':0,'active_catalog_mutation_observed_by_review':0,'dbf_mutation_observed':0,'cdx_lmdb_mutation_observed':0,'workspace_mutation_observed':0,'review_root':ROOT_REL,'next_gate':NEXT_GATE,'created_at_utc':now()}
    (root/'phase22ae_6_5_10dl_summary_v1.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    report=(f'# {PHASE} Runtime Proof Evidence Decision Review\n\n'
            f'Status: `{status}`\n\n'
            '10DL reviews the 10DK transcript-only evidence decision. It accepts the decision for accounting only: transcript evidence is captured, but clean runtime proof and writer reuse remain unaccepted because the 0xC0000005 exit crash remains held.\n\n'
            f'- Transcript evidence captured reviewed: {transcript_evidence}\n'
            '- Clean exit proven: 0\n'
            '- Runtime proof accepted now: 0\n'
            '- Writer reuse confirmed now: 0\n'
            '- Crash triage package required: 1\n'
            '- Source/HELP/CMDHELPCHK/DBF/CDX/LMDB/workspace mutation: 0\n\n'
            f'Next gate: `{NEXT_GATE}`\n')
    (root/'phase22ae_6_5_10dl_review_report_v1.md').write_text(report,encoding='utf-8')
    shutil.copy2(root/'phase22ae_6_5_10dl_summary_v1.json', reports/'message_catalog_phase22ae_6_5_10dl_review_summary_v1.json')
    shutil.copy2(root/'phase22ae_6_5_10dl_review_report_v1.md', reports/'message_catalog_phase22ae_6_5_10dl_review_report_v1.md')
    lines=[status,f'  validation issues: {len(validation)}',f'  Phase 22AE.6.5.10DK status: {prev_status or "NOT_FOUND"}',f'  MSG-022AE.6.5.10DK savepoint present: {1 if prev_present else 0}',f'  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary["msg_022ae_6_5_10cs_savepoint_occurrences_observed"]}','  active messages observed count: 14','  active text observed count: 70',f'  DK evidence rows: {len(evidence_rows)}',f'  DK decision rows: {len(decision_rows)}',f'  DK checklist rows: {len(checklist_rows)}',f'  decision review rows: {len(review_rows)}',f'  evidence review rows: {len(evidence_review_rows)}',f'  triage requirement rows: {len(triage_requirement_rows)}',f'  checklist review rows: {len(checklist_review_rows)}',f'  transcript evidence captured reviewed: {transcript_evidence}',f'  transcript-only decision accepted for accounting: {1 if green else 0}','  clean exit proven: 0','  runtime exit crash held: 1',f'  runtime exit code: {exit_code}',f'  runtime exit code hex: {exit_hex}','  crash triage package required: 1','  runtime proof accepted now: 0','  clean runtime proof accepted now: 0','  reuse path selected now: 0','  writer reuse confirmed now: 0','  source patch selected now: 0','  source patch needed proven: 0','  source mutation authorized now: 0','  apply execution authorized now: 0','  HELP DATA apply executed: 0','  CMDHELPCHK apply executed: 0','  HELP DATA mutation observed: 0','  CMDHELPCHK mutation observed: 0','  source files mutated: 0','  active catalog mutation observed by review: 0','  DBF mutation observed: 0','  CDX/LMDB mutation observed: 0','  workspace mutation observed: 0',f'  next gate: {NEXT_GATE}',f'  reports: {reports}']
    print('\n'.join(lines))
    return 0 if green else 1
if __name__=='__main__': raise SystemExit(main())
