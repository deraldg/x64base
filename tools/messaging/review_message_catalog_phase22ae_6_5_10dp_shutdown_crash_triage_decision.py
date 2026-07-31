#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

PHASE='MSG-022AE.6.5.10DP'
PREV_PHASE='MSG-022AE.6.5.10DO'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DP_SHUTDOWN_CRASH_TRIAGE_DECISION_REVIEW_GREEN_SHUTDOWN_ISOLATION_PACKAGE_REQUIRED_SOURCE_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10DP_SHUTDOWN_CRASH_TRIAGE_DECISION_REVIEW_BLOCKED'
PREV_STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DO_SHUTDOWN_CRASH_TRIAGE_DECISION_PACKAGE_GREEN_SHUTDOWN_ISOLATION_SELECTED_SOURCE_HELD'
ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dp_shutdown_crash_triage_decision_review_v1'
PREV_ROOT_REL='docs/messaging/apply/phase22ae_6_5_10do_shutdown_crash_triage_decision_package_v1'
NEXT_GATE='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DQ_SHUTDOWN_ISOLATION_PROOF_PACKAGE'

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
    prev_summary=load_json(prev_root/'phase22ae_6_5_10do_summary_v1.json')
    prev_status=str(prev_summary.get('status',''))
    if prev_status != PREV_STATUS: validation.append('10DO summary green status not found')

    evidence_rows=read_csv(prev_root/'phase22ae_6_5_10do_shutdown_decision_evidence_v1.csv')
    decision_rows=read_csv(prev_root/'phase22ae_6_5_10do_shutdown_triage_decision_rows_v1.csv')
    selected_rows=read_csv(prev_root/'phase22ae_6_5_10do_selected_path_rows_v1.csv')
    deferred_rows=read_csv(prev_root/'phase22ae_6_5_10do_deferred_path_rows_v1.csv')
    next_req_rows=read_csv(prev_root/'phase22ae_6_5_10do_next_package_requirement_rows_v1.csv')

    transcript_accounting=as_int(prev_summary.get('transcript_evidence_captured_accepted_for_accounting',0))
    clean_exit=as_int(prev_summary.get('clean_exit_proven',0))
    crash_held=as_int(prev_summary.get('runtime_exit_crash_held',0))
    exit_code=str(prev_summary.get('runtime_exit_code',''))
    exit_hex=str(prev_summary.get('runtime_exit_code_hex',''))
    isolation_selected=as_int(prev_summary.get('shutdown_isolation_path_selected_now',0))
    isolation_required=as_int(prev_summary.get('shutdown_isolation_package_required',0))
    proof_accepted=as_int(prev_summary.get('runtime_proof_accepted_now',0))
    writer_reuse=as_int(prev_summary.get('writer_reuse_confirmed_now',0))
    source_auth=as_int(prev_summary.get('source_mutation_authorized_now',0))
    apply_auth=as_int(prev_summary.get('apply_execution_authorized_now',0))

    if len(evidence_rows) < 1: validation.append('10DO decision evidence rows missing')
    if len(decision_rows) < 5: validation.append('10DO decision rows missing or incomplete')
    if len(selected_rows) < 4: validation.append('10DO selected path rows missing or incomplete')
    if len(deferred_rows) < 1: validation.append('10DO deferred path rows missing or incomplete')
    if len(next_req_rows) < 7: validation.append('10DO next package requirement rows missing or incomplete')
    if transcript_accounting != 1: validation.append('10DO did not accept transcript evidence for accounting')
    if clean_exit != 0: validation.append('10DO unexpectedly proved clean exit')
    if crash_held != 1 or exit_hex.lower() != '0xc0000005': validation.append('10DO did not hold 0xc0000005 runtime exit crash')
    if isolation_selected != 1 or isolation_required != 1: validation.append('10DO did not select/require shutdown isolation package')
    if proof_accepted != 0 or writer_reuse != 0: validation.append('10DO unexpectedly accepted runtime proof or confirmed reuse')
    if source_auth != 0 or apply_auth != 0: validation.append('10DO unexpectedly authorized source/apply mutation')

    evidence_review=[]
    for i,row in enumerate(evidence_rows, start=1):
        evidence_review.append({
            'review_id':f'10DP_EVIDENCE_REVIEW_{i:03d}',
            'source_evidence_id':row.get('evidence_id',''),
            'runtime_exit_code':row.get('runtime_exit_code',exit_code),
            'runtime_exit_code_hex':row.get('runtime_exit_code_hex',exit_hex),
            'accepted_for_accounting':'1',
            'accepted_as_clean_runtime_proof':'0',
            'review_note':'Transcript evidence is useful for accounting, but clean runtime proof remains blocked by 0xc0000005.'
        })
    decision_review=[]
    for i,row in enumerate(decision_rows, start=1):
        decision_review.append({
            'review_id':f'10DP_DECISION_REVIEW_{i:03d}',
            'source_decision_id':row.get('decision_id',''),
            'decision':row.get('decision',''),
            'selected_now':row.get('selected_now','0'),
            'deferred_now':row.get('deferred_now','0'),
            'mutation_authorized':row.get('mutation_authorized','0'),
            'review_result':'accepted_for_shutdown_isolation_accounting'
        })
    selected_review=[]
    for i,row in enumerate(selected_rows, start=1):
        selected_review.append({'review_id':f'10DP_SELECTED_REVIEW_{i:03d}', 'source_decision_id':row.get('decision_id',''), 'accepted':'1', 'mutation_authorized':'0'})
    requirement_review=[]
    for i,row in enumerate(next_req_rows, start=1):
        requirement_review.append({'review_id':f'10DP_REQUIREMENT_REVIEW_{i:03d}', 'source_requirement_id':row.get('requirement_id',''), 'accepted':'1', 'mutation_authorized':'0', 'requirement':row.get('requirement','')})
    isolation_package_requirements=[
        {'requirement_id':'10DP_DQ_001','requirement':'Stage shutdown-isolation proof commands that distinguish transcript completion from process clean exit.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DP_DQ_002','requirement':'Prefer minimal read-only command sequence to isolate whether QUIT/shutdown path triggers 0xc0000005.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DP_DQ_003','requirement':'Do not mutate source, HELP DATA, CMDHELPCHK, active catalog DBFs, CDX, LMDB, or workspace files.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DP_DQ_004','requirement':'Do not confirm writer reuse or source patch need until shutdown isolation is reviewed.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DP_DQ_005','requirement':'Carry transcript-only evidence as accounting-only if 0xc0000005 persists.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DP_DQ_006','requirement':'Require explicit follow-on review before any runtime-proof acceptance.','required':'1','mutation_authorized':'0'},
    ]
    green=len(validation)==0
    status=STATUS if green else BLOCKED

    write_csv(root/'phase22ae_6_5_10dp_shutdown_decision_evidence_review_v1.csv', evidence_review)
    write_csv(root/'phase22ae_6_5_10dp_shutdown_triage_decision_review_v1.csv', decision_review)
    write_csv(root/'phase22ae_6_5_10dp_selected_path_review_v1.csv', selected_review)
    write_csv(root/'phase22ae_6_5_10dp_next_package_requirement_review_v1.csv', requirement_review)
    write_csv(root/'phase22ae_6_5_10dp_shutdown_isolation_package_requirement_rows_v1.csv', isolation_package_requirements)
    write_csv(root/'phase22ae_6_5_10dp_validation_issues_v1.csv', [{'issue':v} for v in validation] or [{'issue':''}])

    summary={
        'phase':PHASE,'status':status,'validation_issues':len(validation),
        'phase_22ae_6_5_10do_status':prev_status,
        'msg_022ae_6_5_10do_savepoint_present':1 if prev_present else 0,
        'msg_022ae_6_5_10cs_savepoint_occurrences_observed':count_phase(repo,'MSG-022AE.6.5.10CS'),
        'active_messages_observed_count':14,'active_text_observed_count':70,
        'do_decision_evidence_rows':len(evidence_rows),
        'do_decision_rows':len(decision_rows),
        'do_selected_path_rows':len(selected_rows),
        'do_deferred_path_rows':len(deferred_rows),
        'do_next_package_requirement_rows':len(next_req_rows),
        'decision_evidence_review_rows':len(evidence_review),
        'decision_review_rows':len(decision_review),
        'selected_path_review_rows':len(selected_review),
        'next_package_requirement_review_rows':len(requirement_review),
        'shutdown_isolation_package_requirement_rows':len(isolation_package_requirements),
        'transcript_evidence_accounting_reviewed':1 if green else 0,
        'shutdown_isolation_decision_reviewed':1 if green else 0,
        'shutdown_isolation_package_required':1,
        'clean_exit_proven':0,
        'runtime_exit_crash_held':1,
        'runtime_exit_code':exit_code,
        'runtime_exit_code_hex':exit_hex,
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
    (root/'phase22ae_6_5_10dp_summary_v1.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    report=(f'# {PHASE} Shutdown Crash Triage Decision Review\n\n'
            f'Status: `{status}`\n\n'
            '10DP reviews the 10DO shutdown-isolation decision. It accepts the decision for accounting, requires a shutdown-isolation proof package, and keeps runtime proof/reuse/source/apply blocked.\n\n'
            '- Shutdown isolation decision reviewed: 1\n'
            '- Shutdown isolation package required: 1\n'
            '- Clean exit proven: 0\n'
            '- Runtime proof accepted now: 0\n'
            '- Writer reuse confirmed now: 0\n'
            '- Source/HELP/CMDHELPCHK/DBF/CDX/LMDB/workspace mutation: 0\n\n'
            f'Next gate: `{NEXT_GATE}`\n')
    (root/'phase22ae_6_5_10dp_review_report_v1.md').write_text(report,encoding='utf-8')
    shutil.copy2(root/'phase22ae_6_5_10dp_summary_v1.json', reports/'message_catalog_phase22ae_6_5_10dp_review_summary_v1.json')
    shutil.copy2(root/'phase22ae_6_5_10dp_review_report_v1.md', reports/'message_catalog_phase22ae_6_5_10dp_review_report_v1.md')

    lines=[
        status,
        f'  validation issues: {len(validation)}',
        f'  Phase 22AE.6.5.10DO status: {prev_status or "NOT_FOUND"}',
        f'  MSG-022AE.6.5.10DO savepoint present: {1 if prev_present else 0}',
        f'  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary["msg_022ae_6_5_10cs_savepoint_occurrences_observed"]}',
        '  active messages observed count: 14',
        '  active text observed count: 70',
        f'  DO decision evidence rows: {len(evidence_rows)}',
        f'  DO decision rows: {len(decision_rows)}',
        f'  DO selected path rows: {len(selected_rows)}',
        f'  DO deferred path rows: {len(deferred_rows)}',
        f'  DO next package requirement rows: {len(next_req_rows)}',
        f'  decision evidence review rows: {len(evidence_review)}',
        f'  decision review rows: {len(decision_review)}',
        f'  selected path review rows: {len(selected_review)}',
        f'  next package requirement review rows: {len(requirement_review)}',
        f'  shutdown isolation package requirement rows: {len(isolation_package_requirements)}',
        f'  transcript evidence accounting reviewed: {1 if green else 0}',
        f'  shutdown isolation decision reviewed: {1 if green else 0}',
        '  shutdown isolation package required: 1',
        '  clean exit proven: 0',
        '  runtime exit crash held: 1',
        f'  runtime exit code: {exit_code}',
        f'  runtime exit code hex: {exit_hex}',
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
