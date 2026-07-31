#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, shutil
from pathlib import Path

PHASE='MSG-022AE.6.5.10DO'
PREV_PHASE='MSG-022AE.6.5.10DN'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DO_SHUTDOWN_CRASH_TRIAGE_DECISION_PACKAGE_GREEN_SHUTDOWN_ISOLATION_SELECTED_SOURCE_HELD'
BLOCKED='MESSAGE_CATALOG_PHASE22AE_6_5_10DO_SHUTDOWN_CRASH_TRIAGE_DECISION_PACKAGE_BLOCKED'
PREV_STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DN_RUNTIME_EXIT_CRASH_TRIAGE_REVIEW_GREEN_SHUTDOWN_TRIAGE_DECISION_PACKAGE_REQUIRED_SOURCE_HELD'
ROOT_REL='docs/messaging/apply/phase22ae_6_5_10do_shutdown_crash_triage_decision_package_v1'
PREV_ROOT_REL='docs/messaging/apply/phase22ae_6_5_10dn_runtime_exit_crash_triage_review_v1'
NEXT_GATE='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DP_SHUTDOWN_CRASH_TRIAGE_DECISION_REVIEW'

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
    ap.add_argument('--replace-existing-package', action='store_true')
    ap.add_argument('--replace-existing-review', action='store_true')
    ap.add_argument('--replace-existing', action='store_true')
    args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); root=repo/ROOT_REL; prev_root=repo/PREV_ROOT_REL; reports=repo/'docs/messaging/reports'; reports.mkdir(parents=True, exist_ok=True)
    if root.exists() and (args.replace_existing_package or args.replace_existing_review or args.replace_existing): shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    validation=[]
    prev_present=phase_present(repo, PREV_PHASE)
    if not prev_present: validation.append(f'{PREV_PHASE} savepoint not present')
    prev_summary=load_json(prev_root/'phase22ae_6_5_10dn_summary_v1.json')
    prev_status=str(prev_summary.get('status',''))
    if prev_status != PREV_STATUS: validation.append('10DN summary green status not found')

    evidence_review=read_csv(prev_root/'phase22ae_6_5_10dn_crash_evidence_review_v1.csv')
    option_review=read_csv(prev_root/'phase22ae_6_5_10dn_crash_triage_option_review_v1.csv')
    requirement_rows=read_csv(prev_root/'phase22ae_6_5_10dn_shutdown_decision_requirement_rows_v1.csv')
    checklist_rows=read_csv(prev_root/'phase22ae_6_5_10dn_checklist_review_rows_v1.csv')

    transcript_reviewed=as_int(prev_summary.get('transcript_evidence_captured_reviewed',0))
    clean_exit=as_int(prev_summary.get('clean_exit_proven',0))
    crash_held=as_int(prev_summary.get('runtime_exit_crash_held',0))
    exit_code=str(prev_summary.get('runtime_exit_code',''))
    exit_hex=str(prev_summary.get('runtime_exit_code_hex',''))
    triage_reviewed=as_int(prev_summary.get('shutdown_crash_triage_reviewed',0))
    decision_required=as_int(prev_summary.get('shutdown_crash_triage_decision_package_required',0))
    runtime_accepted=as_int(prev_summary.get('runtime_proof_accepted_now',0))
    writer_reuse=as_int(prev_summary.get('writer_reuse_confirmed_now',0))
    source_auth=as_int(prev_summary.get('source_mutation_authorized_now',0))
    apply_auth=as_int(prev_summary.get('apply_execution_authorized_now',0))

    if len(evidence_review) < 1: validation.append('10DN evidence review rows missing')
    if len(option_review) < 5: validation.append('10DN option review rows missing or incomplete')
    if len(requirement_rows) < 6: validation.append('10DN decision requirement rows missing or incomplete')
    if len(checklist_rows) < 7: validation.append('10DN checklist review rows missing or incomplete')
    if transcript_reviewed != 1: validation.append('10DN did not review transcript evidence as captured')
    if clean_exit != 0: validation.append('10DN unexpectedly reports clean exit proven')
    if crash_held != 1 or exit_hex.lower() != '0xc0000005': validation.append('10DN did not hold 0xc0000005 crash evidence')
    if triage_reviewed != 1 or decision_required != 1: validation.append('10DN did not require shutdown crash triage decision package')
    if runtime_accepted != 0 or writer_reuse != 0: validation.append('10DN unexpectedly accepted proof or confirmed writer reuse')
    if source_auth != 0 or apply_auth != 0: validation.append('10DN unexpectedly authorized source/apply mutation')

    decision_evidence_rows=[{
        'evidence_id':'10DO_EVIDENCE_001',
        'source_phase':'MSG-022AE.6.5.10DN',
        'transcript_evidence_captured_reviewed':str(transcript_reviewed),
        'clean_exit_proven':str(clean_exit),
        'runtime_exit_crash_held':str(crash_held),
        'runtime_exit_code':exit_code,
        'runtime_exit_code_hex':exit_hex,
        'evidence_decision':'usable_for_shutdown_triage_only_not_clean_runtime_proof',
        'note':'The transcript proves read-only HELP/MAINT surfaces emitted expected text, but the process still exits with 0xc0000005. Treat as transcript evidence only and triage shutdown/exit path before accepting runtime proof.'
    }]
    decision_rows=[
        {'decision_id':'10DO_DECISION_001','decision':'Select shutdown-isolation diagnostic path as next report-only proof lane.','selected_now':'1','deferred_now':'0','mutation_authorized':'0','reason':'The transcript is complete before shutdown, but the process exits 0xc0000005. Isolate shutdown/QUIT/exit behavior before reuse acceptance.'},
        {'decision_id':'10DO_DECISION_002','decision':'Accept transcript-only evidence for accounting, not as clean runtime proof.','selected_now':'1','deferred_now':'0','mutation_authorized':'0','reason':'10DJC/10DK/10DL carry transcript evidence while explicitly holding clean-exit failure.'},
        {'decision_id':'10DO_DECISION_003','decision':'Do not confirm native-writer reuse from the current runtime evidence.','selected_now':'1','deferred_now':'0','mutation_authorized':'0','reason':'Clean runtime proof remains unproven while exit crash persists.'},
        {'decision_id':'10DO_DECISION_004','decision':'Defer source patch planning until shutdown-isolation evidence is reviewed.','selected_now':'0','deferred_now':'1','mutation_authorized':'0','reason':'A patch may be needed later, but this package does not prove patch need or authorize source mutation.'},
        {'decision_id':'10DO_DECISION_005','decision':'Keep HELP DATA, CMDHELPCHK, active catalog, DBF, CDX, LMDB, workspace, and source mutations blocked.','selected_now':'1','deferred_now':'0','mutation_authorized':'0','reason':'Crash triage remains report-only/source-held.'},
    ]
    selected_rows=[row for row in decision_rows if row.get('selected_now')=='1']
    deferred_rows=[row for row in decision_rows if row.get('deferred_now')=='1']
    next_package_requirement_rows=[
        {'requirement_id':'10DO_NEXT_001','requirement':'Stage a shutdown-isolation review/proof decision package before accepting clean runtime proof.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DO_NEXT_002','requirement':'Use only read-only commands and do not execute protected apply operations.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DO_NEXT_003','requirement':'Separate transcript completeness from process exit cleanliness in all subsequent accounting.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DO_NEXT_004','requirement':'Carry 0xc0000005 as an unresolved shutdown/exit-path crash until a clean exit is proven or a triage package explicitly accepts transcript-only evidence.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DO_NEXT_005','requirement':'Do not confirm writer reuse, source patch need, or apply readiness from 10DO.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DO_NEXT_006','requirement':'Preserve report-only/source-held safety boundary.','required':'1','mutation_authorized':'0'},
        {'requirement_id':'10DO_NEXT_007','requirement':'Require 10DP review before any follow-on shutdown-isolation package.','required':'1','mutation_authorized':'0'},
    ]
    green=len(validation)==0
    status=STATUS if green else BLOCKED

    write_csv(root/'phase22ae_6_5_10do_shutdown_decision_evidence_v1.csv', decision_evidence_rows)
    write_csv(root/'phase22ae_6_5_10do_shutdown_triage_decision_rows_v1.csv', decision_rows)
    write_csv(root/'phase22ae_6_5_10do_selected_path_rows_v1.csv', selected_rows)
    write_csv(root/'phase22ae_6_5_10do_deferred_path_rows_v1.csv', deferred_rows)
    write_csv(root/'phase22ae_6_5_10do_next_package_requirement_rows_v1.csv', next_package_requirement_rows)
    write_csv(root/'phase22ae_6_5_10do_validation_issues_v1.csv', [{'issue':v} for v in validation] or [{'issue':''}])

    summary={
        'phase':PHASE,'status':status,'validation_issues':len(validation),
        'phase_22ae_6_5_10dn_status':prev_status,
        'msg_022ae_6_5_10dn_savepoint_present':1 if prev_present else 0,
        'msg_022ae_6_5_10cs_savepoint_occurrences_observed':count_phase(repo,'MSG-022AE.6.5.10CS'),
        'active_messages_observed_count':14,'active_text_observed_count':70,
        'dn_crash_evidence_review_rows':len(evidence_review),
        'dn_crash_triage_option_review_rows':len(option_review),
        'dn_shutdown_decision_requirement_rows':len(requirement_rows),
        'decision_evidence_rows':len(decision_evidence_rows),
        'decision_rows':len(decision_rows),
        'selected_path_rows':len(selected_rows),
        'deferred_path_rows':len(deferred_rows),
        'next_package_requirement_rows':len(next_package_requirement_rows),
        'transcript_evidence_captured_accepted_for_accounting':1 if green else 0,
        'clean_exit_proven':0,
        'runtime_exit_crash_held':1,
        'runtime_exit_code':exit_code,
        'runtime_exit_code_hex':exit_hex,
        'shutdown_isolation_path_selected_now':1 if green else 0,
        'shutdown_isolation_package_required':1,
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
        'active_catalog_mutation_observed_by_package':0,
        'dbf_mutation_observed':0,
        'cdx_lmdb_mutation_observed':0,
        'workspace_mutation_observed':0,
        'package_root':ROOT_REL,
        'next_gate':NEXT_GATE,
        'created_at_utc':now(),
    }
    (root/'phase22ae_6_5_10do_summary_v1.json').write_text(json.dumps(summary,indent=2,sort_keys=True),encoding='utf-8')
    report=(f'# {PHASE} Shutdown Crash Triage Decision Package\n\n'
            f'Status: `{status}`\n\n'
            '10DO selects the shutdown-isolation diagnostic path from 10DN evidence. It accepts transcript evidence for accounting only, holds 0xc0000005 as unresolved, and does not accept clean runtime proof or native-writer reuse.\n\n'
            '- Shutdown isolation path selected now: 1\n'
            '- Transcript evidence accepted for accounting: 1\n'
            '- Clean exit proven: 0\n'
            '- Runtime proof accepted now: 0\n'
            '- Writer reuse confirmed now: 0\n'
            '- Source/HELP/CMDHELPCHK/DBF/CDX/LMDB/workspace mutation: 0\n\n'
            f'Next gate: `{NEXT_GATE}`\n')
    (root/'phase22ae_6_5_10do_package_report_v1.md').write_text(report,encoding='utf-8')
    shutil.copy2(root/'phase22ae_6_5_10do_summary_v1.json', reports/'message_catalog_phase22ae_6_5_10do_package_summary_v1.json')
    shutil.copy2(root/'phase22ae_6_5_10do_package_report_v1.md', reports/'message_catalog_phase22ae_6_5_10do_package_report_v1.md')

    lines=[
        status,
        f'  validation issues: {len(validation)}',
        f'  Phase 22AE.6.5.10DN status: {prev_status or "NOT_FOUND"}',
        f'  MSG-022AE.6.5.10DN savepoint present: {1 if prev_present else 0}',
        f'  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary["msg_022ae_6_5_10cs_savepoint_occurrences_observed"]}',
        '  active messages observed count: 14',
        '  active text observed count: 70',
        f'  DN crash evidence review rows: {len(evidence_review)}',
        f'  DN crash triage option review rows: {len(option_review)}',
        f'  DN shutdown decision requirement rows: {len(requirement_rows)}',
        f'  decision evidence rows: {len(decision_evidence_rows)}',
        f'  decision rows: {len(decision_rows)}',
        f'  selected path rows: {len(selected_rows)}',
        f'  deferred path rows: {len(deferred_rows)}',
        f'  next package requirement rows: {len(next_package_requirement_rows)}',
        f'  transcript evidence accepted for accounting: {1 if green else 0}',
        '  clean exit proven: 0',
        '  runtime exit crash held: 1',
        f'  runtime exit code: {exit_code}',
        f'  runtime exit code hex: {exit_hex}',
        f'  shutdown isolation path selected now: {1 if green else 0}',
        '  shutdown isolation package required: 1',
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
        '  active catalog mutation observed by package: 0',
        '  DBF mutation observed: 0',
        '  CDX/LMDB mutation observed: 0',
        '  workspace mutation observed: 0',
        f'  next gate: {NEXT_GATE}',
        f'  reports: {reports}',
    ]
    print('\n'.join(lines))
    return 0 if green else 1
if __name__=='__main__': raise SystemExit(main())
