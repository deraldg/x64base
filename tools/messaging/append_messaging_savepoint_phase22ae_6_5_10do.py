#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
from datetime import datetime, timezone
PHASE='MSG-022AE.6.5.10DO'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DO_SHUTDOWN_CRASH_TRIAGE_DECISION_PACKAGE_GREEN_SHUTDOWN_ISOLATION_SELECTED_SOURCE_HELD'
NEXT_GATE='HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DP_SHUTDOWN_CRASH_TRIAGE_DECISION_REVIEW'

def now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--accept-messaging-savepoint',action='store_true')
    args=ap.parse_args(); repo=Path(args.repo_root).resolve()
    if not args.accept_messaging_savepoint:
        print(f'[{PHASE}] Refusing without --accept-messaging-savepoint'); return 2
    docs=repo/'docs/messaging'; reports=docs/'reports'; docs.mkdir(parents=True,exist_ok=True); reports.mkdir(parents=True,exist_ok=True)
    journal=docs/'MESSAGING_SAVEPOINT_JOURNAL.md'
    txt=journal.read_text(encoding='utf-8',errors='replace') if journal.exists() else '# Messaging Savepoint Journal\n'
    if PHASE in txt:
        print(f'[{PHASE}] Messaging savepoint already present; duplicate append skipped.'); return 0
    ts=now_iso()
    entry=f"\n## {PHASE} - {ts}\n\n- status: {STATUS}\n- next_gate: {NEXT_GATE}\n- boundary: report-only/source-held; shutdown-isolation decision staged; runtime proof/reuse/apply/source mutations remain blocked.\n"
    sha=hashlib.sha256(entry.encode('utf-8')).hexdigest()
    with journal.open('a',encoding='utf-8') as f: f.write(entry+f"- entry_sha256: {sha}\n")
    index=reports/'message_savepoint_thread_index_v1.csv'; exists=index.exists()
    with index.open('a',newline='',encoding='utf-8') as f:
        fields=['phase','status','next_gate','timestamp_utc','entry_sha256']
        w=csv.DictWriter(f,fieldnames=fields)
        if not exists: w.writeheader()
        w.writerow({'phase':PHASE,'status':STATUS,'next_gate':NEXT_GATE,'timestamp_utc':ts,'entry_sha256':sha})
    latest=reports/'message_savepoint_latest_v1.json'
    latest.write_text(json.dumps({'phase':PHASE,'status':STATUS,'next_gate':NEXT_GATE,'timestamp_utc':ts,'entry_sha256':sha},indent=2),encoding='utf-8')
    print(f'[{PHASE}] Messaging savepoint appended.')
    print(f'  journal: {journal}')
    print(f'  index: {index}')
    print(f'  latest: {latest}')
    print(f'  entry_sha256: {sha}')
    return 0
if __name__=='__main__': raise SystemExit(main())
