#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,subprocess,sys
from pathlib import Path
ALLOWED={'MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_GREEN_CHECK_AND_GET_PROVEN','MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_GREEN_CHECK_PROVEN_GET_SYNTAX_REVIEW'}
def first_row(path: Path):
    with path.open('r',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    return rows[0] if rows else {}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--accept-messaging-savepoint',action='store_true'); args=ap.parse_args()
    if not args.accept_messaging_savepoint:
        print('[MSG-022AE.6.5.10AQ] Refusing without --accept-messaging-savepoint',file=sys.stderr); return 2
    repo=Path(args.repo_root).resolve(); row=first_row(repo/'docs/messaging/reports/message_catalog_phase22ae_6_5_10aq_validate_status_summary_v1.csv')
    status=row.get('STATUS','')
    if status not in ALLOWED:
        print(f'[MSG-022AE.6.5.10AQ] Refusing savepoint: expected one of {sorted(ALLOWED)}, got {status}',file=sys.stderr); return 2
    if row.get('SET_MESSAGE_CATALOG_CHECK_PROVEN')!='1':
        print('[MSG-022AE.6.5.10AQ] Refusing savepoint: CHECK surface not proven',file=sys.stderr); return 2
    generic=repo/'tools/messaging/append_messaging_savepoint.py'
    cmd=[sys.executable,str(generic),'--repo-root',str(repo),'--savepoint-id','MSG-022AE.6.5.10AQ','--lane','MESSAGING','--status',status,'--phase','Phase 22AE.6.5.10AQ SET MESSAGE CATALOG read-only contract proof','--summary','10AQ directly probed SET MESSAGE CATALOG CHECK/GET read-only surfaces advertised by MSGMGR while preserving active SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70.','--next-gate',row.get('NEXT_GATE',''),'--source-reports','docs/messaging/reports/message_catalog_phase22ae_6_5_10aq_stage_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10aq_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10aq_surface_contract_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10aq_runtime_observations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10aq_boundary_ledger_v1.csv','--messages',row.get('ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROBE','14'),'--text-rows',row.get('ACTIVE_TEXT_HEADER_COUNT_AFTER_PROBE','70'),'--locales','en-US;es;fr;de;it','--validation-issues',row.get('VALIDATION_ISSUES','0'),'--allowed-candidate-mutations','none; read-only SET MESSAGE CATALOG contract proof','--forbidden-active-mutations','no active DBF mutation; no source edits; no alias mutation; no HELP DATA mutation; no CMDHELPCHK mutation','--accept-messaging-savepoint']
    return subprocess.call(cmd)
if __name__=='__main__': raise SystemExit(main())
