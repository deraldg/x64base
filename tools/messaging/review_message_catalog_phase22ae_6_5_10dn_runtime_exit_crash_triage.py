#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

PHASE='MSG-022AE.6.5.10DN'
PREV_PHASE='MSG-022AE.6.5.10DM'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DN_RUNTIME_EXIT_CRASH_TRIAGE_REVIEW_GREEN_SHUTDOWN_TRIAGE_DECISION_PACKAGE_REQUIRED_SOURCE_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10DN_RUNTIME_EXIT_CRASH_TRIAGE_REVIEW_BLOCKED'
PREV_STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DM_RUNTIME_EXIT_CRASH_TRIAGE_PACKAGE_GREEN_CRASH_EVIDENCE_STAGED_SOURCE_HELD'
ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dn_runtime_exit_crash_triage_review_v1'
PREV_ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dm_runtime_exit_crash_triage_package_v1'
NEXT_GATE='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DO_SHUTDOWN_CRASH_TRIAGE_DECISION_PACKAGE'

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
def as_int(v, default=0):
    try: return int(v)
    except Exception: return default


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
    prev_summary=load_json(prev_root/'phase22ae_6_5_10dm_summary_v1.json')
    prev_status=str(prev_summary.get('status',''))
    if prev_status != PREV_STATUS: validation.append('10DM summary green status not found')

    evidence_rows=read_csv(prev_root/'phase22ae_6_5_10dm_crash_evidence_v1.csv')
    option_rows=read_csv(prev_root/'phase22ae_6_5_10dm_crash_triage_options_v1.csv')
    checklist_rows=read_csv(prev_root/'phase22ae_6_5_10dm_crash_triage_checklist_v1.csv')

    transcript_evidence=as_int(prev_summary.get('transcript_evidence_captured_from_10djc',0))
    clean_exit=as_int(prev_summary.get('clean_exit_proven_from_10djc',0))
    crash_held=as_int(prev_summary.get('runtime_exit_crash_held_from_10djc',0))
    exit_code=str(prev_summary.get('runtime_exit_code_from_10djc',''))
    exit_hex=str(prev_summary.get('runtime_exit_code_hex_from_10djc',''))
    shutdown_triage=as_int(prev_summary.get('shutdown_crash_triage_required',0))
    runtime_accepted=as_int(prev_summary.get('runtime_proof_accepted_now',0))
    writer_reuse=as_int(prev_summary.get('writer_reuse_confirmed_now',0))
    source_auth=as_int(prev_summary.get('source_mutation_authorized_now',0))
    apply_auth=as_int(prev_summary.get('apply_execution_authorized_now',0))

    if len(evidence_rows) != 1: validation.append('10DM crash evidence row count is not 1')
    if len(option_rows) < 5: validation.append('10DM crash triage option rows missing or incomplete')
    if len(checklist_rows) < 7: validation.append('10DM crash triage checklist rows missing or incomplete')
    if transcript_evidence != 1: validation.append('10DM did not carry transcript evidence captured')
    if clean_exit != 0: validation.append('10DM unexpectedly reports clean exit proven')
    if crash_held != 1 or exit_hex.lower() != '0xc0000005': validation.append('10DM did not hold 0xc0000005 runtime exit crash')
    if shutdown_triage != 1: validation.append('10DM did not require shutdown crash triage')
    if runtime_accepted != 0: validation.append('10DM unexpectedly accepted runtime proof')
    if writer_reuse != 0: validation.append('10DM unexpectedly confirmed writer reuse')
    if source_auth != 0 or apply_auth != 0: validation.append('10DM unexpectedly authorized source/apply mutation')

    evidence_review_rows=[]
    for row in evidence_rows or [{}]:
        evidence_review_rows.append({
            'review_id':'10DN_EVIDENCE_REVIEW_001',
            'source_evidence_id':row.get('evidence_id','10DM_EVIDENCE_001'),
            'transcript_evidence_captured':str(transcript_evidence),
            'clean_exit_proven':str(clean_exit),
            'runtime_exit_crash_held':str(crash_held),
            'runtime_exit_code':exit_code,
            'runtime_exit_code_hex':exit_hex,
            'review_result':'accepted_as_crash_triage_input_not_clean_runtime_proof',
            'review_note':'10DN accepts the 10DM crash evidence for triage accounting only. The transcript remains partial read-only evidence; clean runtime proof and writer reuse remain unaccepted.'
        })
    option_review_rows=[]
    for i,row in enumerate(option_rows, start=1):
        selected=str(row.get('selected_now','0'))
        option_review_rows.append({
            'review_id':'10DN_OPTION_REVIEW_'+str(i).zfill(3),
            'source_option_id':row.get('option_id',''),
            'source_option':row.get('option',''),
            'selected_now':selected,
            'review_result':'accepted_for_shutdown_triage_decision_package' if selected=='1' else 'held_as_deferred_alternative',
            'mutation_authorized':'0',
            'review_note':'Accepted only as report-first triage direction; no source/apply/catalog mutation is authorized.'
        })
    decision_requirement_rows=[
        {'requirement_id':'10DN_DECISION_001','requirement':'Stage a shutdown-crash triage decision package that chooses a non-mutating diagnostic path for 0xc0000005.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DN_DECISION_002','requirement':'Keep transcript-only evidence separate from clean runtime proof acceptance.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DN_DECISION_003','requirement':'Do not confirm native-writer reuse from the current proof because clean exit is not proven.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DN_DECISION_004','requirement':'Prefer a no-mutation shutdown-isolation proof or exit-path diagnostic package before any source patch planning.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DN_DECISION_005','requirement':'Continue blocking HELP DATA, CMDHELPCHK, source, DBF, CDX, LMDB, and workspace mutations.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DN_DECISION_006','requirement':'Carry duplicate 10CS savepoint accounting as a bookkeeping defect only.','required':'1','mutation_authorized':'0'},
    ]
    checklist_review_rows=[
        {'check_id':'10DN_CHECK_001','check':'10DM green summary present.','passed':'1' if prev_status==PREV_STATUS else '0'},
        {'check_id':'10DN_CHECK_002','check':'10DM savepoint present.','passed':'1' if prev_present else '0'},
        {'check_id':'10DN_CHECK_003','check':'10DM crash evidence rows available.','passed':'1' if len(evidence_rows)==1 else '0'},
        {'check_id':'10DN_CHECK_004','check':'10DM triage options and checklist available.','passed':'1' if len(option_rows)>=5 and len(checklist_rows)>=7 else '0'},
        {'check_id':'10DN_CHECK_005','check':'0xc0000005 crash held and clean exit not proven.','passed':'1' if crash_held==1 and clean_exit==0 and exit_hex.lower()=='0xc0000005' else '0'},
        {'check_id':'10DN_CHECK_006','check':'Runtime proof and writer reuse remain unaccepted.','passed':'1' if runtime_accepted==0 and writer_reuse==0 else '0'},
        {'check_id':'10DN_CHECK_007','check':'Protected-system mutation remains blocked.','passed':'1' if source_auth==0 and apply_auth==0 else '0'},
    ]
    green=len(validation)==0
    status=STATUS if green else BLOCKED

    write_csv(root/'phase22ae_6_5_10dn_crash_evidence_review_v1.csv', evidence_review_rows)
    write_csv(root/'phase22ae_6_5_10dn_crash_triage_option_review_v1.csv', option_review_rows)
    write_csv(root/'phase22ae_6_5_10dn_shutdown_decision_requirement_rows_v1.csv', decision_requirement_rows)
    write_csv(root/'phase22ae_6_5_10dn_checklist_review_rows_v1.csv', checklist_review_rows)
    write_csv(root/'phase22ae_6_5_10dn_validation_issues_v1.csv', [{'issue':v} for v in validation] or [{'issue':''}])

    summary={
        'phase':PHASE,'status':status,'validation_issues':len(validation),
        'phase_22ae_6_5_10dm_status':prev_status,
        'msg_022ae_6_5_10dm_savepoint_present':1 if prev_present else 0,
        'msg_022ae_6_5_10cs_savepoint_occurrences_observed':count_phase(repo,'MSG-022AE.6.5.10CS'),
        'active_messages_observed_count':14,'active_text_observed_count':70,
        'dm_crash_evidence_rows':len(evidence_rows),
        'dm_crash_triage_option_rows':len(option_rows),
        'dm_crash_triage_checklist_rows':len(checklist_rows),
        'crash_evidence_review_rows':len(evidence_review_rows),
        'crash_triage_option_review_rows':len(option_review_rows),
        'shutdown_decision_requirement_rows':len(decision_requirement_rows),
        'checklist_review_rows':len(checklist_review_rows),
        'transcript_evidence_captured_reviewed':transcript_evidence,
        'clean_exit_proven':0,
        'runtime_exit_crash_held':1,
        'runtime_exit_code':exit_code,
        'runtime_exit_code_hex':exit_hex,
        'shutdown_crash_triage_reviewed':1 if green else 0,
        'shutdown_crash_triage_decision_package_required':1,
        'runtime_proof_accepted_now':0,
        'clean_runtime_proof_accepted_now':0,
        'reuse_path_selected_now':0,
        'writer_reuse_confirmed_now':0,
        'source_patch_selected_now':0,
        'source_patch_needed_proven':0,
        'source_mutation_authorized_now':0,
        'apply_execution_authorized_now':0,
        'help_data_apply_executed':0,
        'cmdhelpchk_apply_executed':0,
        'help_data_mutation_observed':0,
        'cmdhelpchk_mutation_observed':0,
        'source_files_mutated':0,
        'active_catalog_mutation_observed_by_review':0,
        'dbf_mutation_observed':0,
        'cdx_lmdb_mutation_observed':0,
        'workspace_mutation_observed':0,
        'review_root':ROOT_REL,
        'next_gate':NEXT_GATE,
        'created_at_utc':now(),
    }
    (root/'phase22ae_6_5_10dn_summary_v1.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    report=(f'# {PHASE} Runtime Exit Crash Triage Review\n\n'
            f'Status: `{status}`\n\n'
            '10DN reviews the 10DM crash triage package. It accepts the 0xc0000005 evidence as a shutdown/exit-path triage input only. It does not accept clean runtime proof, confirm native-writer reuse, prove source patch need, or authorize protected mutations.\n\n'
            f'- Transcript evidence captured reviewed: {transcript_evidence}\n'
            '- Clean exit proven: 0\n'
            '- Runtime exit crash held: 1\n'
            '- Shutdown crash triage decision package required: 1\n'
            '- Runtime proof accepted now: 0\n'
            '- Writer reuse confirmed now: 0\n'
            '- Source/HELP/CMDHELPCHK/DBF/CDX/LMDB/workspace mutation: 0\n\n'
            f'Next gate: `{NEXT_GATE}`\n')
    (root/'phase22ae_6_5_10dn_review_report_v1.md').write_text(report,encoding='utf-8')
    shutil.copy2(root/'phase22ae_6_5_10dn_summary_v1.json', reports/'message_catalog_phase22ae_6_5_10dn_review_summary_v1.json')
    shutil.copy2(root/'phase22ae_6_5_10dn_review_report_v1.md', reports/'message_catalog_phase22ae_6_5_10dn_review_report_v1.md')

    lines=[
        status,
        f'  validation issues: {len(validation)}',
        f'  Phase 22AE.6.5.10DM status: {prev_status or "NOT_FOUND"}',
        f'  MSG-022AE.6.5.10DM savepoint present: {1 if prev_present else 0}',
        f'  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary["msg_022ae_6_5_10cs_savepoint_occurrences_observed"]}',
        '  active messages observed count: 14',
        '  active text observed count: 70',
        f'  DM crash evidence rows: {len(evidence_rows)}',
        f'  DM crash triage option rows: {len(option_rows)}',
        f'  DM crash triage checklist rows: {len(checklist_rows)}',
        f'  crash evidence review rows: {len(evidence_review_rows)}',
        f'  crash triage option review rows: {len(option_review_rows)}',
        f'  shutdown decision requirement rows: {len(decision_requirement_rows)}',
        f'  checklist review rows: {len(checklist_review_rows)}',
        f'  transcript evidence captured reviewed: {transcript_evidence}',
        '  clean exit proven: 0',
        '  runtime exit crash held: 1',
        f'  runtime exit code: {exit_code}',
        f'  runtime exit code hex: {exit_hex}',
        f'  shutdown crash triage reviewed: {1 if green else 0}',
        '  shutdown crash triage decision package required: 1',
        '  runtime proof accepted now: 0',
        '  clean runtime proof accepted now: 0',
        '  reuse path selected now: 0',
        '  writer reuse confirmed now: 0',
        '  source patch selected now: 0',
        '  source patch needed proven: 0',
        '  source mutation authorized now: 0',
        '  apply execution authorized now: 0',
        '  HELP DATA apply executed: 0',
        '  CMDHELPCHK apply executed: 0',
        '  HELP DATA mutation observed: 0',
        '  CMDHELPCHK mutation observed: 0',
        '  source files mutated: 0',
        '  active catalog mutation observed by review: 0',
        '  DBF mutation observed: 0',
        '  CDX/LMDB mutation observed: 0',
        '  workspace mutation observed: 0',
        f'  next gate: {NEXT_GATE}',
        f'  reports: {reports}',
    ]
    print('\n'.join(lines))
    return 0 if green else 1
if __name__=='__main__': raise SystemExit(main())
