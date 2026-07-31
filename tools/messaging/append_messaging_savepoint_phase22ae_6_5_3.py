#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,subprocess,sys
from pathlib import Path
OK={'MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_GREEN_TWO_TABLE_REBUILD_PROVEN','MESSAGE_CATALOG_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF_GREEN_REBUILD_NOT_PROVEN_FIELD_MAP_REVIEW'}
def first(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        r=list(csv.DictReader(f)); return r[0] if r else {}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',required=True); ap.add_argument('--accept-messaging-savepoint',action='store_true'); a=ap.parse_args()
    if not a.accept_messaging_savepoint: print('[MSG-022AE.6.5.3] Refusing without --accept-messaging-savepoint',file=sys.stderr); return 2
    repo=Path(a.repo_root).resolve(); row=first(repo/'docs/messaging/reports/message_catalog_phase22ae_6_5_3_validate_status_summary_v1.csv'); st=row.get('STATUS','')
    if st not in OK: print(f'[MSG-022AE.6.5.3] Refusing savepoint: expected one of {sorted(OK)}, got {st}',file=sys.stderr); return 2
    gen=repo/'tools/messaging/append_messaging_savepoint.py'
    cmd=[sys.executable,str(gen),'--repo-root',str(repo),'--savepoint-id','MSG-022AE.6.5.3','--lane','MESSAGING','--status',st,'--phase','Phase 22AE.6.5.3 full candidate rebuild sandbox proof','--summary','6.5.3 full candidate rebuild sandbox proof completed using broad field mapping; active promotion remains closed unless two-table rebuild is proven.','--next-gate',row.get('NEXT_GATE',''),'--source-reports','docs/messaging/reports/message_catalog_phase22ae_6_5_3_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_3_rebuild_result_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_3_tail_rows_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_3_validate_boundary_ledger_v1.csv','--messages',row.get('SANDBOX_MESSAGE_ROWS_AFTER',''),'--text-rows',row.get('SANDBOX_TEXT_ROWS_AFTER',''),'--locales','en-US;es;fr;de;it','--validation-issues',row.get('VALIDATION_ISSUES','0'),'--allowed-candidate-mutations','isolated sandbox DBF import only','--forbidden-active-mutations','no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation','--accept-messaging-savepoint']
    return subprocess.call(cmd)
if __name__=='__main__': raise SystemExit(main())
