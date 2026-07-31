#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json
from pathlib import Path
PHASE='MSG-022AE.6.5.10DJB'
STATUS='MESSAGE_CATALOG_PHASE22AE_6_5_10DJB_RUNTIME_PROOF_CRASH_REVIEW_AND_CLEAN_RERUN_STAGING_GREEN_CRASH_RECORDED_CLEAN_SCRIPT_STAGED_SOURCE_HELD'
SUMMARY_REL='docs/messaging/apply/phase22ae_6_5_10djb_runtime_proof_crash_review_and_clean_rerun_staging_v1/phase22ae_6_5_10djb_summary_v1.json'
NEXT_GATE='HOLD_OR_RUN_PHASE22AE_6_5_10DJB_CLEAN_RUNTIME_PROOF_AND_CAPTURE_TRANSCRIPT'
def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def read(p):
    try: return p.read_text(encoding='utf-8', errors='replace')
    except FileNotFoundError: return ''
def present(repo):
    return any(PHASE in read(repo/x) for x in ['docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md','docs/messaging/reports/message_savepoint_thread_index_v1.csv','docs/messaging/reports/message_savepoint_latest_v1.json'])
def update_index(path, entry):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size>0:
        with path.open('r',newline='',encoding='utf-8-sig') as f: reader=csv.DictReader(f); rows=list(reader); fields=list(reader.fieldnames or [])
    else: rows=[]; fields=[]
    for f in ['phase','savepoint','status','next_gate','timestamp_utc','entry_sha256','summary_path']:
        if f not in fields: fields.append(f)
    row={k:'' for k in fields}
    for k,v in entry.items():
        if k in row: row[k]=v
    for alt in ['id','savepoint_id','message_savepoint','phase_id']:
        if alt in row: row[alt]=PHASE
    if 'status' in row: row['status']=STATUS
    rows.append(row)
    with path.open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--accept-messaging-savepoint',action='store_true'); args=ap.parse_args()
    if not args.accept_messaging_savepoint: raise SystemExit('Refusing to append without --accept-messaging-savepoint')
    repo=Path(args.repo_root).resolve()
    if present(repo): print(f'[{PHASE}] Messaging savepoint already present; duplicate append skipped.'); return 0
    sp=repo/SUMMARY_REL
    if not sp.exists(): raise SystemExit(f'10DJB summary not found: {sp}')
    summary=json.loads(sp.read_text(encoding='utf-8'))
    if summary.get('status') != STATUS: raise SystemExit(f'10DJB summary is not green: {summary.get("status")}')
    ts=now(); body='\n'.join([f'## {PHASE}','',f'- timestamp_utc: {ts}',f'- status: {STATUS}',f'- summary: {SUMMARY_REL}',f'- next_gate: {NEXT_GATE}','- boundary: 10DJA crash/non-clean runtime proof recorded; clean no-REM runtime proof rerun staged only; runtime not executed by package; source/HELP/CMDHELPCHK/DBF/CDX/LMDB/workspace mutation 0',''])
    sha=hashlib.sha256(body.encode()).hexdigest(); journal=repo/'docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md'; journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open('a',encoding='utf-8') as f: f.write(body)
    entry={'phase':PHASE,'savepoint':PHASE,'status':STATUS,'next_gate':NEXT_GATE,'timestamp_utc':ts,'entry_sha256':sha,'summary_path':SUMMARY_REL}
    update_index(repo/'docs/messaging/reports/message_savepoint_thread_index_v1.csv', entry)
    latest=repo/'docs/messaging/reports/message_savepoint_latest_v1.json'; latest.parent.mkdir(parents=True,exist_ok=True); latest.write_text(json.dumps({**entry,'summary':summary},indent=2,sort_keys=True),encoding='utf-8')
    print(f'[{PHASE}] Messaging savepoint appended.'); print(f'  journal: {journal}'); print(f'  index: {repo / "docs/messaging/reports/message_savepoint_thread_index_v1.csv"}'); print(f'  latest: {latest}'); print(f'  entry_sha256: {sha}')
    return 0
if __name__=='__main__': raise SystemExit(main())
