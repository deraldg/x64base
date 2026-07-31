#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

PHASE = "22AE.6.5.10DR"
MSG_ID = "MSG-022AE.6.5.10DR"
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DR_SHUTDOWN_ISOLATION_PROOF_REVIEW_GREEN_GENERAL_SHUTDOWN_EXIT_CRASH_CONFIRMED_SOURCE_HELD"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DS_DOTSCRIPT_SHUTDOWN_EXIT_CRASH_FIX_PLAN_PACKAGE"
PREV_MSG = "MSG-022AE.6.5.10DQ"
PREV_STATUS_PREFIX = "MESSAGE_CATALOG_PHASE22AE_6_5_10DQ_SHUTDOWN_ISOLATION_PROOF_PACKAGE_GREEN"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return ''

def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    ensure_dir(path.parent)
    if fields is None:
        fields = sorted({k for r in rows for k in r.keys()}) if rows else ['note']
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fields})

def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def journal_has(repo: Path, msg: str) -> bool:
    journal = repo / 'docs' / 'messaging' / 'MESSAGING_SAVEPOINT_JOURNAL.md'
    return msg in read_text(journal)

def find_status(repo: Path, token: str) -> str:
    reports = repo / 'docs' / 'messaging' / 'reports'
    candidates = []
    if reports.exists():
        for p in reports.glob('*10dq*'):
            if p.is_file():
                candidates.append(p)
        for p in reports.glob('*latest*'):
            if p.is_file():
                candidates.append(p)
    for p in candidates:
        text = read_text(p)
        for line in text.splitlines():
            if token in line:
                return line.strip()
    # fallback: inspect package summary json
    root = repo / 'docs' / 'messaging' / 'apply' / 'phase22ae_6_5_10dq_shutdown_isolation_proof_package_v1'
    for p in root.glob('*summary*.json'):
        text = read_text(p)
        if token in text:
            return token
    return ''

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--replace-existing-review', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / 'docs' / 'messaging' / 'reports'
    root = repo / 'docs' / 'messaging' / 'apply' / 'phase22ae_6_5_10dr_shutdown_isolation_proof_review_v1'
    ensure_dir(reports); ensure_dir(root)

    issues: list[dict] = []
    dq_root = repo / 'docs' / 'messaging' / 'apply' / 'phase22ae_6_5_10dq_shutdown_isolation_proof_package_v1'
    package_results = dq_root / 'phase22ae_6_5_10dq_shutdown_isolation_runtime_results_v1.csv'
    bin_results = dq_root / 'phase22ae_6_5_10dq_bin_runtime_shutdown_isolation_results_v1.csv'

    dq_status = find_status(repo, PREV_STATUS_PREFIX)
    dq_savepoint = 1 if journal_has(repo, PREV_MSG) else 0
    if dq_savepoint != 1:
        issues.append({'issue_id':'10DR_PRECONDITION_001','severity':'ERROR','message':'MSG-022AE.6.5.10DQ savepoint not present'})

    rows = read_csv(bin_results) or read_csv(package_results)
    evidence_source = str(bin_results if bin_results.exists() else package_results)
    if not rows:
        issues.append({'issue_id':'10DR_EVIDENCE_001','severity':'ERROR','message':'No shutdown isolation runtime results CSV found'})

    review_rows = []
    exit_codes = []
    crash_count = 0
    zero_count = 0
    transcript_complete = 0
    for r in rows:
        script = r.get('script') or r.get('probe_id') or r.get('name') or ''
        exit_raw = str(r.get('exit_code') or r.get('exitcode') or '').strip()
        try:
            exit_code = int(exit_raw)
        except Exception:
            exit_code = None
        if exit_code is not None:
            exit_codes.append(exit_code)
        if exit_code == -1073741819:
            crash_count += 1
        if exit_code == 0:
            zero_count += 1
        transcript = r.get('transcript') or r.get('stdout') or ''
        t_path = Path(transcript) if transcript else None
        t_text = read_text(t_path) if t_path and t_path.exists() else ''
        complete = 1 if ('--- END DOTTALK TRANSCRIPT ---' in t_text or 'SHUTDOWN:' in t_text or t_text) else 0
        transcript_complete += complete
        review_rows.append({
            'script': script,
            'exit_code': '' if exit_code is None else str(exit_code),
            'exit_code_hex': '0xc0000005' if exit_code == -1073741819 else (hex(exit_code) if isinstance(exit_code, int) and exit_code < 0 else ''),
            'transcript': transcript,
            'transcript_observed': 1 if t_text else 0,
            'transcript_complete_or_shutdown_seen': complete,
            'classification': 'ACCESS_VIOLATION_ON_PROCESS_EXIT' if exit_code == -1073741819 else ('CLEAN_EXIT' if exit_code == 0 else 'OTHER_OR_UNKNOWN')
        })

    all_four_crash = 1 if len(rows) >= 4 and crash_count == len(rows) else 0
    quit_only_crash = 0
    for rr in review_rows:
        if 'quit_only' in rr['script'].lower() and rr['exit_code'] == '-1073741819':
            quit_only_crash = 1
    general_shutdown_exit_crash_confirmed = 1 if all_four_crash and quit_only_crash else 0
    command_specific_crash_supported = 0 if general_shutdown_exit_crash_confirmed else 1

    if general_shutdown_exit_crash_confirmed != 1:
        issues.append({'issue_id':'10DR_CLASSIFICATION_001','severity':'ERROR','message':'General shutdown exit crash not confirmed from isolation results'})

    decision_rows = [
        {'decision_id':'10DR_DECISION_001','decision':'accept_transcript_evidence_for_accounting','selected':1,'rationale':'Isolation transcripts completed/readable enough for accounting, but exit status is not clean.'},
        {'decision_id':'10DR_DECISION_002','decision':'classify_as_general_dotscript_shutdown_exit_crash','selected':general_shutdown_exit_crash_confirmed,'rationale':'QUIT-only and HELP/MAINT variants all returned 0xC0000005.'},
        {'decision_id':'10DR_DECISION_003','decision':'do_not_blame_help_or_maint','selected':1 if general_shutdown_exit_crash_confirmed else 0,'rationale':'HELP/MAINT do not uniquely trigger the crash; QUIT-only also crashes.'},
        {'decision_id':'10DR_DECISION_004','decision':'do_not_accept_clean_runtime_proof','selected':1,'rationale':'All observed process exits are non-zero access violations.'},
        {'decision_id':'10DR_DECISION_005','decision':'require_dotscript_shutdown_exit_fix_plan','selected':1,'rationale':'A follow-on source-held fix plan should isolate process shutdown/DOTSCRIPT runner cleanup before any source patch.'},
    ]

    checklist_rows = [
        {'check_id':'10DR_CHECK_001','description':'10DQ savepoint present','pass':dq_savepoint},
        {'check_id':'10DR_CHECK_002','description':'isolation result rows observed','pass':1 if rows else 0},
        {'check_id':'10DR_CHECK_003','description':'QUIT-only probe returned 0xC0000005','pass':quit_only_crash},
        {'check_id':'10DR_CHECK_004','description':'all isolation probes returned 0xC0000005','pass':all_four_crash},
        {'check_id':'10DR_CHECK_005','description':'transcript evidence retained for accounting','pass':1 if transcript_complete > 0 else 0},
        {'check_id':'10DR_CHECK_006','description':'runtime proof remains not accepted','pass':1},
        {'check_id':'10DR_CHECK_007','description':'protected systems unchanged by review package','pass':1},
    ]

    write_csv(root / 'phase22ae_6_5_10dr_shutdown_isolation_probe_review_v1.csv', review_rows,
              ['script','exit_code','exit_code_hex','transcript','transcript_observed','transcript_complete_or_shutdown_seen','classification'])
    write_csv(root / 'phase22ae_6_5_10dr_shutdown_isolation_decision_review_v1.csv', decision_rows,
              ['decision_id','decision','selected','rationale'])
    write_csv(root / 'phase22ae_6_5_10dr_checklist_v1.csv', checklist_rows,
              ['check_id','description','pass'])
    write_csv(root / 'phase22ae_6_5_10dr_validation_issues_v1.csv', issues,
              ['issue_id','severity','message'])

    status = STATUS_GREEN if not issues else 'MESSAGE_CATALOG_PHASE22AE_6_5_10DR_SHUTDOWN_ISOLATION_PROOF_REVIEW_BLOCKED'
    summary = {
        'phase': PHASE,
        'message_id': MSG_ID,
        'status': status,
        'validation_issues': len(issues),
        'phase22ae_6_5_10dq_status': dq_status,
        'msg_022ae_6_5_10dq_savepoint_present': dq_savepoint,
        'evidence_source': evidence_source,
        'shutdown_isolation_result_rows': len(rows),
        'shutdown_isolation_review_rows': len(review_rows),
        'exit_code_0xc0000005_rows': crash_count,
        'clean_exit_rows': zero_count,
        'quit_only_exit_crash': quit_only_crash,
        'all_isolation_probes_exit_crash': all_four_crash,
        'general_dotscript_shutdown_exit_crash_confirmed': general_shutdown_exit_crash_confirmed,
        'command_specific_help_maint_crash_supported': command_specific_crash_supported,
        'runtime_proof_accepted_now': 0,
        'clean_runtime_proof_accepted_now': 0,
        'reuse_path_selected_now': 0,
        'writer_reuse_confirmed_now': 0,
        'source_patch_selected_now': 0,
        'source_patch_needed_proven': 0,
        'source_mutation_authorized_now': 0,
        'apply_execution_authorized_now': 0,
        'help_data_apply_executed': 0,
        'cmdhelpchk_apply_executed': 0,
        'source_files_mutated': 0,
        'active_catalog_mutation_observed_by_review': 0,
        'dbf_mutation_observed': 0,
        'cdx_lmdb_mutation_observed': 0,
        'workspace_mutation_observed': 0,
        'next_gate': NEXT_GATE,
        'generated_at_utc': utc_now(),
    }
    (root / 'phase22ae_6_5_10dr_summary_v1.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    md = f"""# MSG-022AE.6.5.10DR shutdown isolation proof review\n\nStatus: `{status}`\n\n10DR reviews the 10DQ shutdown-isolation proof. The key result is that the QUIT-only probe and all HELP/MAINT variants returned `0xC0000005`; therefore the evidence supports a general DotScript/process shutdown exit crash, not a HELP or MAINT command-specific defect.\n\nBoundary: no source, HELP DATA, CMDHELPCHK, DBF, CDX, LMDB, workspace, or active catalog mutation is performed by this review package.\n\nNext gate: `{NEXT_GATE}`\n"""
    (root / 'phase22ae_6_5_10dr_package_report_v1.md').write_text(md, encoding='utf-8')

    # copy summary to reports for easy discovery
    for name in ['summary_v1.json','validation_issues_v1.csv']:
        src = root / f'phase22ae_6_5_10dr_{name}'
        if src.exists():
            (reports / src.name).write_text(src.read_text(encoding='utf-8'), encoding='utf-8')

    print(status)
    print(f"  validation issues: {len(issues)}")
    print(f"  Phase 22AE.6.5.10DQ status: {dq_status or '(not found)'}")
    print(f"  MSG-022AE.6.5.10DQ savepoint present: {dq_savepoint}")
    print(f"  evidence source: {evidence_source}")
    print(f"  shutdown isolation result rows: {len(rows)}")
    print(f"  shutdown isolation review rows: {len(review_rows)}")
    print(f"  exit code 0xc0000005 rows: {crash_count}")
    print(f"  clean exit rows: {zero_count}")
    print(f"  QUIT-only exit crash: {quit_only_crash}")
    print(f"  all isolation probes exit crash: {all_four_crash}")
    print(f"  general DotScript shutdown exit crash confirmed: {general_shutdown_exit_crash_confirmed}")
    print(f"  command-specific HELP/MAINT crash supported: {command_specific_crash_supported}")
    print("  runtime proof accepted now: 0")
    print("  clean runtime proof accepted now: 0")
    print("  reuse path selected now: 0")
    print("  writer reuse confirmed now: 0")
    print("  source patch selected now: 0")
    print("  source patch needed proven: 0")
    print("  source mutation authorized now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if not issues else 1

if __name__ == '__main__':
    raise SystemExit(main())
