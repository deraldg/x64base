#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
MSG_ID = 'MSG-022AE.6.5.10DS'
PHASE = '22AE.6.5.10DS'
STATUS = 'MESSAGE_CATALOG_PHASE22AE_6_5_10DS_DOTSCRIPT_SHUTDOWN_EXIT_CRASH_FIX_PLAN_PACKAGE_GREEN_FIX_PLAN_STAGED_SOURCE_HELD'

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def read_text(p: Path):
    try: return p.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError: return ''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--accept-messaging-savepoint', action='store_true')
    args=ap.parse_args()
    if not args.accept_messaging_savepoint:
        print('Refusing to append without --accept-messaging-savepoint')
        return 2
    repo=Path(args.repo_root).resolve()
    root=repo/'docs'/'messaging'/'apply'/'phase22ae_6_5_10ds_dotscript_shutdown_exit_crash_fix_plan_package_v1'
    summary_path=root/'phase22ae_6_5_10ds_summary_v1.json'
    if not summary_path.exists():
        print(f'MSG-022AE.6.5.10DS summary not found: {summary_path}')
        return 1
    summary=json.loads(summary_path.read_text(encoding='utf-8'))
    if summary.get('status') != STATUS:
        print(f'MSG-022AE.6.5.10DS summary status is not green: {summary.get("status")}')
        return 1
    docs=repo/'docs'/'messaging'
    reports=docs/'reports'
    docs.mkdir(parents=True, exist_ok=True); reports.mkdir(parents=True, exist_ok=True)
    journal=docs/'MESSAGING_SAVEPOINT_JOURNAL.md'
    existing=read_text(journal)
    if MSG_ID in existing:
        print(f'[{MSG_ID}] Messaging savepoint already present; duplicate append skipped.')
        return 0
    entry = {
        'message_id': MSG_ID,
        'phase': PHASE,
        'status': STATUS,
        'next_gate': summary.get('next_gate',''),
        'entry_utc': utc_now(),
        'source_mutation_authorized_now': 0,
        'source_files_mutated': 0,
        'runtime_proof_accepted_now': 0,
        'reuse_path_selected_now': 0,
        'apply_execution_authorized_now': 0,
        'help_data_apply_executed': 0,
        'cmdhelpchk_apply_executed': 0,
        'dbf_mutation_observed': 0,
        'cdx_lmdb_mutation_observed': 0,
        'workspace_mutation_observed': 0,
    }
    payload=json.dumps(entry, sort_keys=True)
    entry_sha=hashlib.sha256(payload.encode('utf-8')).hexdigest()
    with journal.open('a', encoding='utf-8') as f:
        if existing and not existing.endswith('\n'):
            f.write('\n')
        f.write(f'\n## {MSG_ID} - {entry["entry_utc"]}\n\n')
        f.write(f'- status: `{STATUS}`\n')
        f.write(f'- next gate: `{entry["next_gate"]}`\n')
        f.write('- protected mutations: 0\n')
        f.write(f'- entry_sha256: `{entry_sha}`\n')
    latest=reports/'message_savepoint_latest_v1.json'
    entry['entry_sha256']=entry_sha
    latest.write_text(json.dumps(entry, indent=2), encoding='utf-8')
    index=reports/'message_savepoint_thread_index_v1.csv'
    if not index.exists():
        index.write_text('message_id,phase,status,next_gate,entry_utc,entry_sha256\n', encoding='utf-8')
    with index.open('a', encoding='utf-8') as f:
        f.write(f'{MSG_ID},{PHASE},{STATUS},{entry["next_gate"]},{entry["entry_utc"]},{entry_sha}\n')
    print(f'[{MSG_ID}] Messaging savepoint appended.')
    print(f'  journal: {journal}')
    print(f'  index: {index}')
    print(f'  latest: {latest}')
    print(f'  entry_sha256: {entry_sha}')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
