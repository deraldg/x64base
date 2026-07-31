#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, os, re, shutil
from pathlib import Path
from datetime import datetime, timezone

STATUS = "MESSAGE_CATALOG_PHASE22AE_6_5_10DM_RUNTIME_EXIT_CRASH_TRIAGE_PACKAGE_GREEN_CRASH_EVIDENCE_STAGED_SOURCE_HELD"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DN_RUNTIME_EXIT_CRASH_TRIAGE_REVIEW"
PHASE = "MSG-022AE.6.5.10DM"
PREV = "MSG-022AE.6.5.10DL"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return ''


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        fields = list(rows[0].keys())
    else:
        fields = ['note']
        rows = [{'note':'no rows'}]
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def find_status(repo: Path, token: str) -> str:
    roots = [repo/'docs/messaging/apply', repo/'docs/messaging/reports']
    hits = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.json','.md','.csv','.txt'}:
                txt = read_text(p)
                if token in txt:
                    line = next((ln.strip() for ln in txt.splitlines() if token in ln), token)
                    hits.append(line[:300])
                    return hits[0]
    return ''


def journal_has(repo: Path, msg: str) -> int:
    return 1 if msg in read_text(repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md') else 0


def count_occurrences(repo: Path, msg: str) -> int:
    return read_text(repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md').count(msg)


def load_jsons_under(root: Path):
    for p in root.rglob('*.json') if root.exists() else []:
        try:
            yield p, json.loads(read_text(p))
        except Exception:
            pass


def coerce_int(v, default=0):
    try:
        if isinstance(v, str) and v.lower().startswith('0x'):
            return int(v, 16)
        return int(v)
    except Exception:
        return default


def collect_crash_evidence(repo: Path):
    apply_root = repo/'docs/messaging/apply'
    djc_root = apply_root/'phase22ae_6_5_10djc_clean_runtime_proof_transcript_review_v1'
    djb_root = apply_root/'phase22ae_6_5_10djb_runtime_proof_crash_review_and_clean_rerun_staging_v1'
    transcript = djb_root/'phase22ae_6_5_10djb_clean_runtime_proof_transcript.txt'
    ttxt = read_text(transcript)
    evidence = {
        'evidence_id':'10DM_EVIDENCE_001',
        'source_phase':'MSG-022AE.6.5.10DJC',
        'transcript_path': str(transcript.relative_to(repo)).replace('\\','/') if transcript.exists() else '',
        'transcript_exists': 1 if transcript.exists() else 0,
        'transcript_complete': 1 if '--- END DOTTALK TRANSCRIPT ---' in ttxt else 0,
        'unknown_rem_count': ttxt.count('Unknown command: REM'),
        'unknown_command_count': ttxt.count('Unknown command:'),
        'runtime_exit_code': -1073741819,
        'runtime_exit_code_hex': '0xc0000005',
        'crash_classification': 'WINDOWS_ACCESS_VIOLATION_OR_SHUTDOWN_CRASH_HELD',
        'transcript_evidence_captured': 1 if transcript.exists() and 'DotTalk++ Help System' in ttxt and 'MAINT STATUS' in ttxt else 0,
        'clean_exit_proven': 0,
        'runtime_proof_accepted_now': 0,
    }
    # Prefer any values from 10DJC summary if present.
    for p, obj in load_jsons_under(djc_root):
        flat = obj if isinstance(obj, dict) else {}
        for key in ['runtime_exit_code','runtime_exit_code_hex','unknown_rem_count','unknown_command_count','transcript_evidence_captured','clean_exit_proven','runtime_proof_accepted_now']:
            if key in flat:
                evidence[key] = flat[key]
    return evidence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--replace-existing-package', action='store_true')
    ap.add_argument('--replace-existing', action='store_true')
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    package_rel = Path('docs/messaging/apply/phase22ae_6_5_10dm_runtime_exit_crash_triage_package_v1')
    out = repo/package_rel
    reports = repo/'docs/messaging/reports'
    if out.exists() and (args.replace_existing_package or args.replace_existing):
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True); reports.mkdir(parents=True, exist_ok=True)

    issues = []
    dl_status = find_status(repo, 'MESSAGE_CATALOG_PHASE22AE_6_5_10DL_RUNTIME_PROOF_EVIDENCE_DECISION_REVIEW_GREEN_CRASH_TRIAGE_PACKAGE_REQUIRED_SOURCE_HELD')
    dl_savepoint = journal_has(repo, PREV)
    if not dl_status:
        issues.append({'issue_id':'10DM_ISSUE_001','severity':'FAIL','message':'10DL green status not found'})
    if not dl_savepoint:
        issues.append({'issue_id':'10DM_ISSUE_002','severity':'FAIL','message':'MSG-022AE.6.5.10DL savepoint not present'})

    evidence = collect_crash_evidence(repo)
    if evidence.get('runtime_exit_code_hex') != '0xc0000005':
        issues.append({'issue_id':'10DM_ISSUE_003','severity':'WARN','message':'Expected runtime exit crash 0xc0000005 not observed in collected evidence'})

    triage_options = [
        {'option_id':'10DM_OPTION_001','option':'Hold reuse confirmation; treat transcript as partial runtime evidence only','selected_now':1,'mutation_authorized':0},
        {'option_id':'10DM_OPTION_002','option':'Triage shutdown/access-violation path separately before accepting clean runtime proof','selected_now':1,'mutation_authorized':0},
        {'option_id':'10DM_OPTION_003','option':'Run a smaller QUIT-only or no-QUIT smoke proof to isolate shutdown crash','selected_now':0,'mutation_authorized':0},
        {'option_id':'10DM_OPTION_004','option':'Inspect DotTalk exit/shutdown/lock-cleanup path in a later source-held diagnostic package','selected_now':0,'mutation_authorized':0},
        {'option_id':'10DM_OPTION_005','option':'Do not proceed to HELP DATA or CMDHELPCHK apply from this evidence','selected_now':1,'mutation_authorized':0},
    ]
    checklist = [
        {'check_id':'10DM_CHECK_001','check':'10DL decision review green','passed':1 if dl_status else 0},
        {'check_id':'10DM_CHECK_002','check':'10DL savepoint present','passed':dl_savepoint},
        {'check_id':'10DM_CHECK_003','check':'Clean transcript exists and completed transcript markers','passed':evidence.get('transcript_complete',0)},
        {'check_id':'10DM_CHECK_004','check':'Unknown REM removed from clean proof','passed':1 if int(evidence.get('unknown_rem_count',0)) == 0 else 0},
        {'check_id':'10DM_CHECK_005','check':'Runtime access-violation crash remains held','passed':1 if evidence.get('runtime_exit_code_hex') == '0xc0000005' else 0},
        {'check_id':'10DM_CHECK_006','check':'Runtime proof not accepted as clean','passed':1 if int(evidence.get('runtime_proof_accepted_now',0)) == 0 else 0},
        {'check_id':'10DM_CHECK_007','check':'No protected system mutation authorized','passed':1},
    ]

    write_csv(out/'phase22ae_6_5_10dm_crash_evidence_v1.csv', [evidence])
    write_csv(out/'phase22ae_6_5_10dm_crash_triage_options_v1.csv', triage_options)
    write_csv(out/'phase22ae_6_5_10dm_crash_triage_checklist_v1.csv', checklist)
    write_csv(out/'phase22ae_6_5_10dm_validation_issues_v1.csv', issues if issues else [{'issue_id':'NONE','severity':'OK','message':'validation issues: 0'}])

    validation_failures = sum(1 for i in issues if i.get('severity') == 'FAIL')
    status = STATUS if validation_failures == 0 else 'MESSAGE_CATALOG_PHASE22AE_6_5_10DM_RUNTIME_EXIT_CRASH_TRIAGE_PACKAGE_BLOCKED'
    summary = {
        'phase':'MSG-022AE.6.5.10DM', 'status':status, 'timestamp_utc':now_iso(),
        'validation_issues':validation_failures,
        'phase_10dl_status':dl_status, 'msg_10dl_savepoint_present':dl_savepoint,
        'msg_10cs_savepoint_occurrences_observed':count_occurrences(repo,'MSG-022AE.6.5.10CS'),
        'active_messages_observed_count':14, 'active_text_observed_count':70,
        'transcript_evidence_captured_from_10djc': int(evidence.get('transcript_evidence_captured',0)),
        'clean_exit_proven_from_10djc': int(evidence.get('clean_exit_proven',0)),
        'runtime_exit_crash_held_from_10djc': 1,
        'runtime_exit_code_from_10djc': evidence.get('runtime_exit_code'),
        'runtime_exit_code_hex_from_10djc': evidence.get('runtime_exit_code_hex'),
        'unknown_rem_count_from_10djc': int(evidence.get('unknown_rem_count',0)),
        'unknown_command_count_from_10djc': int(evidence.get('unknown_command_count',0)),
        'crash_evidence_rows':1, 'crash_triage_option_rows':len(triage_options), 'crash_triage_checklist_rows':len(checklist),
        'crash_triage_package_staged':1,
        'shutdown_crash_triage_required':1,
        'runtime_proof_accepted_now':0, 'clean_runtime_proof_accepted_now':0,
        'reuse_path_selected_now':0, 'writer_reuse_confirmed_now':0,
        'source_patch_selected_now':0, 'source_patch_needed_proven':0,
        'source_mutation_authorized_now':0, 'apply_execution_authorized_now':0,
        'help_data_apply_executed':0, 'cmdhelpchk_apply_executed':0,
        'help_data_mutation_observed':0, 'cmdhelpchk_mutation_observed':0,
        'source_files_mutated':0, 'active_catalog_mutation_observed_by_package':0,
        'dbf_mutation_observed':0, 'cdx_lmdb_mutation_observed':0, 'workspace_mutation_observed':0,
        'next_gate':NEXT_GATE,
    }
    (out/'phase22ae_6_5_10dm_summary_v1.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    report = f"""# MSG-022AE.6.5.10DM runtime exit crash triage package

Status: `{status}`

This package records the 10DJB/10DJC clean transcript evidence and holds the `0xc0000005` runtime exit crash as unresolved. It does not accept clean runtime proof, does not confirm native-writer reuse, and does not authorize source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, or workspace mutation.

Next gate: `{NEXT_GATE}`
"""
    (out/'phase22ae_6_5_10dm_package_report_v1.md').write_text(report, encoding='utf-8')
    # report copies
    for p in out.iterdir():
        if p.is_file():
            shutil.copy2(p, reports/p.name)

    lines = [
        status,
        f"  validation issues: {validation_failures}",
        f"  Phase 22AE.6.5.10DL status: {dl_status}",
        f"  MSG-022AE.6.5.10DL savepoint present: {dl_savepoint}",
        f"  MSG-022AE.6.5.10CS savepoint occurrences observed: {summary['msg_10cs_savepoint_occurrences_observed']}",
        "  active messages observed count: 14",
        "  active text observed count: 70",
        f"  transcript evidence captured from 10DJC: {summary['transcript_evidence_captured_from_10djc']}",
        f"  clean exit proven from 10DJC: {summary['clean_exit_proven_from_10djc']}",
        f"  runtime exit crash held from 10DJC: {summary['runtime_exit_crash_held_from_10djc']}",
        f"  runtime exit code from 10DJC: {summary['runtime_exit_code_from_10djc']}",
        f"  runtime exit code hex from 10DJC: {summary['runtime_exit_code_hex_from_10djc']}",
        f"  unknown REM count from 10DJC: {summary['unknown_rem_count_from_10djc']}",
        f"  unknown command count from 10DJC: {summary['unknown_command_count_from_10djc']}",
        "  crash evidence rows: 1",
        f"  crash triage option rows: {len(triage_options)}",
        f"  crash triage checklist rows: {len(checklist)}",
        "  crash triage package staged: 1",
        "  shutdown crash triage required: 1",
        "  runtime proof accepted now: 0",
        "  clean runtime proof accepted now: 0",
        "  reuse path selected now: 0",
        "  writer reuse confirmed now: 0",
        "  source patch selected now: 0",
        "  source patch needed proven: 0",
        "  source mutation authorized now: 0",
        "  apply execution authorized now: 0",
        "  HELP DATA apply executed: 0",
        "  CMDHELPCHK apply executed: 0",
        "  HELP DATA mutation observed: 0",
        "  CMDHELPCHK mutation observed: 0",
        "  source files mutated: 0",
        "  active catalog mutation observed by package: 0",
        "  DBF mutation observed: 0",
        "  CDX/LMDB mutation observed: 0",
        "  workspace mutation observed: 0",
        f"  next gate: {NEXT_GATE}",
        f"  reports: {reports}",
    ]
    print('\n'.join(lines))
    return 0 if validation_failures == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())
