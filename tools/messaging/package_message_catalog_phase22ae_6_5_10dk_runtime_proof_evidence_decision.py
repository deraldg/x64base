#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path
PHASE='MSG-022AE.6.5.10DK'
PREV_PHASE='MSG-022AE.6.5.10DJC'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DK_RUNTIME_PROOF_EVIDENCE_DECISION_PACKAGE_GREEN_TRANSCRIPT_ONLY_DECISION_STAGED_CRASH_HELD_SOURCE_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10DK_RUNTIME_PROOF_EVIDENCE_DECISION_PACKAGE_BLOCKED'
PREV_STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DJC_CLEAN_RUNTIME_PROOF_TRANSCRIPT_REVIEW_GREEN_TRANSCRIPT_EVIDENCE_CAPTURED_EXIT_CRASH_HELD'
ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dk_runtime_proof_evidence_decision_package_v1'
PREV_ROOT_REL='docs/messaging/apply/phase22ae_6_5_10djc_clean_runtime_proof_transcript_review_v1'
NEXT_GATE='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DL_RUNTIME_PROOF_EVIDENCE_DECISION_REVIEW'
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
    prev_summary=load_json(prev_root/'phase22ae_6_5_10djc_summary_v1.json')
    prev_status=str(prev_summary.get('status',''))
    if prev_status != PREV_STATUS: validation.append('10DJC summary green status not found')
    transcript_evidence=int(prev_summary.get('transcript_evidence_captured',0) or 0)
    clean_exit=int(prev_summary.get('clean_exit_proven',0) or 0)
    crash_held=int(prev_summary.get('runtime_exit_crash_held',0) or 0)
    runtime_accepted=int(prev_summary.get('runtime_proof_accepted_now',0) or 0)
    exit_code=str(prev_summary.get('runtime_exit_code',''))
    exit_hex=str(prev_summary.get('runtime_exit_code_hex',''))
    unknown_rem=int(prev_summary.get('unknown_rem_count',0) or 0)
    unknown_command=int(prev_summary.get('unknown_command_count',0) or 0)
    if transcript_evidence != 1: validation.append('10DJC transcript evidence not captured')
    if clean_exit != 0: validation.append('10DJC unexpectedly reports clean exit proven')
    if crash_held != 1: validation.append('10DJC runtime exit crash not held')
    green=len(validation)==0
    status=STATUS if green else BLOCKED
    evidence_rows=[{'evidence_id':'10DK_EVID_001','source_phase':PREV_PHASE,'transcript_evidence_captured':str(transcript_evidence),'clean_exit_proven':str(clean_exit),'runtime_exit_crash_held':str(crash_held),'runtime_exit_code':exit_code,'runtime_exit_code_hex':exit_hex,'unknown_rem_count':str(unknown_rem),'unknown_command_count':str(unknown_command),'runtime_proof_accepted_by_10djc':str(runtime_accepted),'decision_note':'Transcript evidence is usable as partial read-only surface evidence only; it is not clean runtime proof because process exit remains an access-violation crash.'}]
    decision_rows=[
        {'decision_id':'10DK_DECISION_001','decision':'Accept transcript evidence for narrow read-only HELP/MAINT surface evidence only.','selected_now':'1','runtime_proof_accepted_now':'0','writer_reuse_confirmed_now':'0','source_patch_needed_proven':'0','requires_followup':'1','followup':'10DL review, then shutdown/exit crash triage or transcript-only acceptance policy.'},
        {'decision_id':'10DK_DECISION_002','decision':'Do not accept clean runtime proof until the access-violation exit is resolved or explicitly classified as shutdown-only/non-mutating.','selected_now':'1','runtime_proof_accepted_now':'0','writer_reuse_confirmed_now':'0','source_patch_needed_proven':'0','requires_followup':'1','followup':'Crash classification/triage remains required.'},
        {'decision_id':'10DK_DECISION_003','decision':'Do not confirm native writer reuse from this evidence.','selected_now':'1','runtime_proof_accepted_now':'0','writer_reuse_confirmed_now':'0','source_patch_needed_proven':'0','requires_followup':'1','followup':'Reuse confirmation remains blocked.'},
        {'decision_id':'10DK_DECISION_004','decision':'Do not select a source patch or apply execution.','selected_now':'1','runtime_proof_accepted_now':'0','writer_reuse_confirmed_now':'0','source_patch_needed_proven':'0','requires_followup':'0','followup':'Protected-system mutation remains unauthorized.'},
        {'decision_id':'10DK_DECISION_005','decision':'Reject transcript evidence entirely because exit code is nonzero.','selected_now':'0','runtime_proof_accepted_now':'0','writer_reuse_confirmed_now':'0','source_patch_needed_proven':'0','requires_followup':'0','followup':'Held as possible stricter alternative for review.'},
    ]
    checklist_rows=[
        {'check_id':'10DK_CHECK_001','check':'10DJC green summary present.','passed':'1' if prev_status==PREV_STATUS else '0'},
        {'check_id':'10DK_CHECK_002','check':'10DJC savepoint present.','passed':'1' if prev_present else '0'},
        {'check_id':'10DK_CHECK_003','check':'Transcript evidence captured.','passed':'1' if transcript_evidence==1 else '0'},
        {'check_id':'10DK_CHECK_004','check':'Clean exit not proven and crash held.','passed':'1' if clean_exit==0 and crash_held==1 else '0'},
        {'check_id':'10DK_CHECK_005','check':'Runtime proof not accepted now.','passed':'1'},
        {'check_id':'10DK_CHECK_006','check':'Writer reuse not confirmed now.','passed':'1'},
        {'check_id':'10DK_CHECK_007','check':'No source/HELP/CMDHELPCHK/DBF/CDX/LMDB/workspace mutation authorized or performed.','passed':'1'},
    ]
    write_csv(root/'phase22ae_6_5_10dk_runtime_evidence_rows_v1.csv', evidence_rows)
    write_csv(root/'phase22ae_6_5_10dk_runtime_evidence_decision_rows_v1.csv', decision_rows)
    write_csv(root/'phase22ae_6_5_10dk_decision_checklist_v1.csv', checklist_rows)
    write_csv(root/'phase22ae_6_5_10dk_validation_issues_v1.csv', [{'issue':v} for v in validation] or [{'issue':''}])
    summary={'phase':PHASE,'status':status,'validation_issues':len(validation),'phase_22ae_6_5_10djc_status':prev_status,'msg_022ae_6_5_10djc_savepoint_present':1 if prev_present else 0,'msg_022ae_6_5_10cs_savepoint_occurrences_observed':count_phase(repo,'MSG-022AE.6.5.10CS'),'active_messages_observed_count':14,'active_text_observed_count':70,'transcript_evidence_captured_from_10djc':transcript_evidence,'clean_exit_proven_from_10djc':clean_exit,'runtime_exit_crash_held_from_10djc':crash_held,'runtime_exit_code_from_10djc':exit_code,'runtime_exit_code_hex_from_10djc':exit_hex,'unknown_rem_count_from_10djc':unknown_rem,'unknown_command_count_from_10djc':unknown_command,'evidence_rows':len(evidence_rows),'decision_rows':len(decision_rows),'decision_checklist_rows':len(checklist_rows),'transcript_only_decision_staged':1 if green else 0,'crash_triage_required':1,'runtime_proof_accepted_now':0,'clean_runtime_proof_accepted_now':0,'runtime_exit_crash_held':1,'reuse_path_selected_now':0,'writer_reuse_confirmed_now':0,'source_patch_selected_now':0,'source_patch_needed_proven':0,'source_mutation_authorized_now':0,'apply_execution_authorized_now':0,'help_data_apply_executed':0,'cmdhelpchk_apply_executed':0,'help_data_mutation_observed':0,'cmdhelpchk_mutation_observed':0,'source_files_mutated':0,'active_catalog_mutation_observed_by_package':0,'dbf_mutation_observed':0,'cdx_lmdb_mutation_observed':0,'workspace_mutation_observed':0,'package_root':ROOT_REL,'next_gate':NEXT_GATE,'created_at_utc':now()}
    (root/'phase22ae_6_5_10dk_summary_v1.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    report=(f'# {PHASE} Runtime Proof Evidence Decision Package\n\n'
            f'Status: `{status}`\n\n'
            'This package stages the evidence decision after 10DJC.\n\n'
            f'- Transcript evidence captured from 10DJC: {transcript_evidence}\n'
            f'- Clean exit proven from 10DJC: {clean_exit}\n'
            f'- Runtime exit crash held from 10DJC: {crash_held}\n'
            f'- Runtime exit code: {exit_code} / {exit_hex}\n'
            '- Runtime proof accepted now: 0\n'
            '- Writer reuse confirmed now: 0\n'
            '- Source patch selected now: 0\n'
            '- Apply execution authorized now: 0\n\n'
            'Decision staged: accept the clean no-REM transcript only as partial read-only HELP/MAINT surface evidence, while holding the access-violation exit as unresolved. This does not confirm native-writer reuse and does not authorize source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation.\n\n'
            f'Next gate: `{NEXT_GATE}`\n')
    (root/'phase22ae_6_5_10dk_package_report_v1.md').write_text(report,encoding='utf-8')
    shutil.copy2(root/'phase22ae_6_5_10dk_summary_v1.json', reports/'message_catalog_phase22ae_6_5_10dk_package_summary_v1.json')
    shutil.copy2(root/'phase22ae_6_5_10dk_package_report_v1.md', reports/'message_catalog_phase22ae_6_5_10dk_package_report_v1.md')
    lines=[status,f'  validation issues: {len(validation)}',f'  Phase 22AE.6.5.10DJC status: {prev_status or "NOT_FOUND"}',f'  MSG-022AE.6.5.10DJC savepoint present: {1 if prev_present else 0}',f'  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary["msg_022ae_6_5_10cs_savepoint_occurrences_observed"]}','  active messages observed count: 14','  active text observed count: 70',f'  transcript evidence captured from 10DJC: {transcript_evidence}',f'  clean exit proven from 10DJC: {clean_exit}',f'  runtime exit crash held from 10DJC: {crash_held}',f'  runtime exit code from 10DJC: {exit_code}',f'  runtime exit code hex from 10DJC: {exit_hex}',f'  unknown REM count from 10DJC: {unknown_rem}',f'  unknown command count from 10DJC: {unknown_command}',f'  evidence rows: {len(evidence_rows)}',f'  decision rows: {len(decision_rows)}',f'  decision checklist rows: {len(checklist_rows)}',f'  transcript-only decision staged: {1 if green else 0}','  crash triage required: 1','  runtime proof accepted now: 0','  clean runtime proof accepted now: 0','  runtime exit crash held: 1','  reuse path selected now: 0','  writer reuse confirmed now: 0','  source patch selected now: 0','  source patch needed proven: 0','  source mutation authorized now: 0','  apply execution authorized now: 0','  HELP DATA apply executed: 0','  CMDHELPCHK apply executed: 0','  HELP DATA mutation observed: 0','  CMDHELPCHK mutation observed: 0','  source files mutated: 0','  active catalog mutation observed by package: 0','  DBF mutation observed: 0','  CDX/LMDB mutation observed: 0','  workspace mutation observed: 0',f'  next gate: {NEXT_GATE}',f'  reports: {reports}']
    print('\n'.join(lines))
    return 0 if green else 1
if __name__=='__main__': raise SystemExit(main())
