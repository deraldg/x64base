#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

PHASE = "22AE.6.5.10DS"
MSG_ID = "MSG-022AE.6.5.10DS"
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DS_DOTSCRIPT_SHUTDOWN_EXIT_CRASH_FIX_PLAN_PACKAGE_GREEN_FIX_PLAN_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DS_DOTSCRIPT_SHUTDOWN_EXIT_CRASH_FIX_PLAN_PACKAGE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DT_DOTSCRIPT_SHUTDOWN_EXIT_CRASH_FIX_PLAN_REVIEW"
PREV_MSG = "MSG-022AE.6.5.10DR"
PREV_STATUS_TOKEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DR_SHUTDOWN_ISOLATION_PROOF_REVIEW_GREEN_GENERAL_SHUTDOWN_EXIT_CRASH_CONFIRMED_SOURCE_HELD"


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

def journal_has(repo: Path, msg: str) -> bool:
    journal = repo / 'docs' / 'messaging' / 'MESSAGING_SAVEPOINT_JOURNAL.md'
    return msg in read_text(journal)

def find_status(repo: Path, token: str) -> str:
    reports = repo / 'docs' / 'messaging' / 'reports'
    roots = [reports, repo / 'docs' / 'messaging' / 'apply' / 'phase22ae_6_5_10dr_shutdown_isolation_proof_review_v1']
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob('*'):
            if not p.is_file():
                continue
            name = p.name.lower()
            if ('10dr' not in name) and ('latest' not in name):
                continue
            text = read_text(p)
            for line in text.splitlines():
                if token in line:
                    return line.strip()
            if token in text:
                return token
    return ''

def load_10dr_summary(repo: Path) -> dict:
    candidates = [
        repo / 'docs' / 'messaging' / 'apply' / 'phase22ae_6_5_10dr_shutdown_isolation_proof_review_v1' / 'phase22ae_6_5_10dr_summary_v1.json',
        repo / 'docs' / 'messaging' / 'reports' / 'phase22ae_6_5_10dr_summary_v1.json',
    ]
    for p in candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                pass
    return {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--replace-existing-package', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / 'docs' / 'messaging' / 'reports'
    root = repo / 'docs' / 'messaging' / 'apply' / 'phase22ae_6_5_10ds_dotscript_shutdown_exit_crash_fix_plan_package_v1'
    ensure_dir(reports); ensure_dir(root)

    issues: list[dict] = []
    dr_status = find_status(repo, PREV_STATUS_TOKEN)
    dr_savepoint = 1 if journal_has(repo, PREV_MSG) else 0
    if dr_savepoint != 1:
        issues.append({'issue_id':'10DS_PRECONDITION_001','severity':'ERROR','message':'MSG-022AE.6.5.10DR savepoint not present'})
    if not dr_status:
        issues.append({'issue_id':'10DS_PRECONDITION_002','severity':'ERROR','message':'10DR green status not found in reports/apply artifacts'})

    dr_summary = load_10dr_summary(repo)
    general_crash = int(dr_summary.get('general_dotscript_shutdown_exit_crash_confirmed', 0) or 0)
    quit_crash = int(dr_summary.get('quit_only_exit_crash', 0) or 0)
    crash_rows = int(dr_summary.get('exit_code_0xc0000005_rows', 0) or 0)
    clean_rows = int(dr_summary.get('clean_exit_rows', 0) or 0)
    if general_crash != 1:
        issues.append({'issue_id':'10DS_EVIDENCE_001','severity':'ERROR','message':'10DR did not confirm general DotScript shutdown exit crash'})

    evidence_rows = [
        {
            'evidence_id':'10DS_EVIDENCE_001',
            'source_phase':'22AE.6.5.10DR',
            'finding':'general_dotscript_shutdown_exit_crash_confirmed',
            'value':general_crash,
            'detail':'10DR found QUIT-only and all shutdown isolation probes returned 0xC0000005.'
        },
        {
            'evidence_id':'10DS_EVIDENCE_002',
            'source_phase':'22AE.6.5.10DR',
            'finding':'quit_only_exit_crash',
            'value':quit_crash,
            'detail':'QUIT-only probe returned access-violation exit code; HELP/MAINT are not uniquely implicated.'
        },
        {
            'evidence_id':'10DS_EVIDENCE_003',
            'source_phase':'22AE.6.5.10DR',
            'finding':'exit_code_0xc0000005_rows',
            'value':crash_rows,
            'detail':'Observed shutdown-isolation rows with 0xC0000005.'
        },
        {
            'evidence_id':'10DS_EVIDENCE_004',
            'source_phase':'22AE.6.5.10DR',
            'finding':'clean_exit_rows',
            'value':clean_rows,
            'detail':'Clean process exit rows observed by 10DR.'
        },
    ]

    fix_options = [
        {'option_id':'10DS_OPTION_001','option':'hold_no_patch','selected':0,'risk':'low','description':'Hold with crash documented; does not restore clean DotScript runtime-proof exit.'},
        {'option_id':'10DS_OPTION_002','option':'plan_shutdown_exit_instrumentation_only','selected':0,'risk':'low','description':'Stage diagnostics to locate crash in DotScript runner shutdown path before patching.'},
        {'option_id':'10DS_OPTION_003','option':'plan_guarded_source_patch_after_source_location_review','selected':1,'risk':'medium','description':'Prepare a follow-on guarded source investigation/patch plan for DotScript/process shutdown exit handling, with no source mutation in 10DS.'},
        {'option_id':'10DS_OPTION_004','option':'accept_transcript_only_and_continue_reuse','selected':0,'risk':'high','description':'Rejected: transcript evidence exists, but clean runtime proof and reuse remain unproven because exit code is 0xC0000005.'},
        {'option_id':'10DS_OPTION_005','option':'patch_help_or_maint','selected':0,'risk':'high','description':'Rejected: 10DR shows QUIT-only also crashes; HELP/MAINT are not the causal surface.'},
    ]

    selected_plan = [
        {'step_id':'10DS_PLAN_001','sequence':1,'step':'source_discovery','description':'Locate DOTSCRIPT command implementation, runner process lifecycle, QUIT command handling, shutdown.ini processing, global cleanup/destructors, and main exit-code path.'},
        {'step_id':'10DS_PLAN_002','sequence':2,'step':'prove_minimal_repro','description':'Preserve the 10DQ QUIT-only DTS transcript/result as minimal repro: DotScript + QUIT returns 0xC0000005.'},
        {'step_id':'10DS_PLAN_003','sequence':3,'step':'classify_boundary','description':'Keep Messaging/HELP/MAINT/reuse/apply lanes blocked from accepting clean runtime proof until process exit becomes clean.'},
        {'step_id':'10DS_PLAN_004','sequence':4,'step':'prepare_guarded_patch_package','description':'Next source-touching package must update source-comment usage contracts and add/repair shutdown proof tests; 10DS does not patch.'},
        {'step_id':'10DS_PLAN_005','sequence':5,'step':'post_patch_validation','description':'After a separately authorized patch, rerun QUIT-only, HELP+QUIT, MAINT STATUS+QUIT, HELP+MAINT STATUS+QUIT and require exit_code 0.'},
    ]

    investigation_targets = [
        {'target_id':'10DS_TARGET_001','target':'src/cli/cmd_dotscript.cpp','reason':'Likely DOTSCRIPT command surface and script runner lifecycle; verify OUT/transcript service integration did not affect cleanup.', 'source_mutation_now':0},
        {'target_id':'10DS_TARGET_002','target':'src/cli/cmd_quit* or command dispatcher quit handling','reason':'QUIT-only DTS crashes on process exit; inspect quit/shutdown control flow and return semantics.', 'source_mutation_now':0},
        {'target_id':'10DS_TARGET_003','target':'src/cli/shell_transcript.*','reason':'Recent transcript service touches process/runner output capture; inspect destructor/flush ordering only after source discovery.', 'source_mutation_now':0},
        {'target_id':'10DS_TARGET_004','target':'main/CLI application shutdown path','reason':'Access violation may happen after transcript completes, during teardown/destructor/static cleanup, or return from main.', 'source_mutation_now':0},
        {'target_id':'10DS_TARGET_005','target':'shutdown.ini processing/runtime root handling','reason':'Both build and bin roots showed access-violation exit; shutdown.ini is not sufficient to prevent crash, but remains part of shutdown path.', 'source_mutation_now':0},
        {'target_id':'10DS_TARGET_006','target':'tests/dotscript shutdown proof artifact','reason':'Future fix should add repeatable proof for clean DOTSCRIPT process exit on minimal scripts.', 'source_mutation_now':0},
    ]

    checklist = [
        {'check_id':'10DS_CHECK_001','description':'10DR savepoint present','pass':dr_savepoint},
        {'check_id':'10DS_CHECK_002','description':'10DR general shutdown exit crash confirmed','pass':general_crash},
        {'check_id':'10DS_CHECK_003','description':'HELP/MAINT not selected as causal target','pass':1},
        {'check_id':'10DS_CHECK_004','description':'clean runtime proof remains unaccepted','pass':1},
        {'check_id':'10DS_CHECK_005','description':'source patch not authorized in 10DS','pass':1},
        {'check_id':'10DS_CHECK_006','description':'HELP DATA/CMDHELPCHK apply not authorized','pass':1},
        {'check_id':'10DS_CHECK_007','description':'next gate is review before any patch plan execution','pass':1},
    ]

    write_csv(root / 'phase22ae_6_5_10ds_crash_evidence_rollup_v1.csv', evidence_rows,
              ['evidence_id','source_phase','finding','value','detail'])
    write_csv(root / 'phase22ae_6_5_10ds_fix_plan_options_v1.csv', fix_options,
              ['option_id','option','selected','risk','description'])
    write_csv(root / 'phase22ae_6_5_10ds_selected_fix_plan_v1.csv', selected_plan,
              ['step_id','sequence','step','description'])
    write_csv(root / 'phase22ae_6_5_10ds_source_investigation_targets_v1.csv', investigation_targets,
              ['target_id','target','reason','source_mutation_now'])
    write_csv(root / 'phase22ae_6_5_10ds_fix_plan_checklist_v1.csv', checklist,
              ['check_id','description','pass'])
    write_csv(root / 'phase22ae_6_5_10ds_validation_issues_v1.csv', issues,
              ['issue_id','severity','message'])

    status = STATUS_GREEN if not issues else STATUS_BLOCKED
    summary = {
        'phase': PHASE,
        'message_id': MSG_ID,
        'status': status,
        'validation_issues': len(issues),
        'phase22ae_6_5_10dr_status': dr_status,
        'msg_022ae_6_5_10dr_savepoint_present': dr_savepoint,
        'general_dotscript_shutdown_exit_crash_from_10dr': general_crash,
        'quit_only_exit_crash_from_10dr': quit_crash,
        'exit_code_0xc0000005_rows_from_10dr': crash_rows,
        'clean_exit_rows_from_10dr': clean_rows,
        'crash_evidence_rows': len(evidence_rows),
        'fix_plan_option_rows': len(fix_options),
        'selected_fix_plan_rows': len(selected_plan),
        'source_investigation_target_rows': len(investigation_targets),
        'fix_plan_checklist_rows': len(checklist),
        'dotscript_shutdown_exit_fix_plan_staged': 1 if not issues else 0,
        'source_patch_selected_now': 0,
        'source_patch_needed_proven': 0,
        'source_mutation_authorized_now': 0,
        'source_files_mutated': 0,
        'runtime_proof_accepted_now': 0,
        'clean_runtime_proof_accepted_now': 0,
        'reuse_path_selected_now': 0,
        'writer_reuse_confirmed_now': 0,
        'apply_execution_authorized_now': 0,
        'help_data_apply_executed': 0,
        'cmdhelpchk_apply_executed': 0,
        'active_catalog_mutation_observed_by_package': 0,
        'dbf_mutation_observed': 0,
        'cdx_lmdb_mutation_observed': 0,
        'workspace_mutation_observed': 0,
        'next_gate': NEXT_GATE,
        'generated_at_utc': utc_now(),
    }
    (root / 'phase22ae_6_5_10ds_summary_v1.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    report = f"""# MSG-022AE.6.5.10DS DotScript shutdown exit crash fix plan package

Status: `{status}`

10DS stages a report-only fix plan for the DotScript/process shutdown access-violation exit identified by 10DR. It does not patch source. It does not accept clean runtime proof. It does not confirm native writer reuse. It does not apply HELP DATA or CMDHELPCHK.

Key decision: treat this as a general DotScript/process shutdown exit-code defect because the QUIT-only probe also returned `0xC0000005`.

Next gate: `{NEXT_GATE}`
"""
    (root / 'phase22ae_6_5_10ds_package_report_v1.md').write_text(report, encoding='utf-8')

    # copy summary/issues to reports
    for src in [root / 'phase22ae_6_5_10ds_summary_v1.json', root / 'phase22ae_6_5_10ds_validation_issues_v1.csv']:
        if src.exists():
            (reports / src.name).write_text(src.read_text(encoding='utf-8'), encoding='utf-8')

    print(status)
    print(f"  validation issues: {len(issues)}")
    print(f"  Phase 22AE.6.5.10DR status: {dr_status or '(not found)'}")
    print(f"  MSG-022AE.6.5.10DR savepoint present: {dr_savepoint}")
    print(f"  general DotScript shutdown exit crash from 10DR: {general_crash}")
    print(f"  QUIT-only exit crash from 10DR: {quit_crash}")
    print(f"  exit code 0xc0000005 rows from 10DR: {crash_rows}")
    print(f"  clean exit rows from 10DR: {clean_rows}")
    print(f"  crash evidence rows: {len(evidence_rows)}")
    print(f"  fix plan option rows: {len(fix_options)}")
    print(f"  selected fix plan rows: {len(selected_plan)}")
    print(f"  source investigation target rows: {len(investigation_targets)}")
    print(f"  fix plan checklist rows: {len(checklist)}")
    print(f"  DotScript shutdown exit fix plan staged: {summary['dotscript_shutdown_exit_fix_plan_staged']}")
    print("  source patch selected now: 0")
    print("  source patch needed proven: 0")
    print("  source mutation authorized now: 0")
    print("  source files mutated: 0")
    print("  runtime proof accepted now: 0")
    print("  clean runtime proof accepted now: 0")
    print("  reuse path selected now: 0")
    print("  writer reuse confirmed now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  active catalog mutation observed by package: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if not issues else 1

if __name__ == '__main__':
    raise SystemExit(main())
