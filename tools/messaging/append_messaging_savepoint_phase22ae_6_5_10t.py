#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path
STATUS_EXPECTED='MESSAGE_CATALOG_PHASE22AE_6_5_10T_TEXT_ONLY_ACTIVE_IMPORT_MICRO_PROOF_PLAN_GREEN_SOURCE_HELD'
def first_row(path: Path):
    with path.open('r', encoding='utf-8-sig', newline='') as f: rows=list(csv.DictReader(f))
    return rows[0] if rows else {}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root', required=True); ap.add_argument('--accept-messaging-savepoint', action='store_true'); args=ap.parse_args()
    if not args.accept_messaging_savepoint:
        print('[MSG-022AE.6.5.10T] Refusing without --accept-messaging-savepoint', file=sys.stderr); return 2
    repo=Path(args.repo_root).resolve(); row=first_row(repo/'docs/messaging/reports/message_catalog_phase22ae_6_5_10t_status_summary_v1.csv')
    status=row.get('STATUS','')
    if status != STATUS_EXPECTED:
        print(f'[MSG-022AE.6.5.10T] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}', file=sys.stderr); return 2
    cmd=[sys.executable, str(repo/'tools/messaging/append_messaging_savepoint.py'), '--repo-root', str(repo), '--savepoint-id', 'MSG-022AE.6.5.10T', '--lane', 'MESSAGING', '--status', status, '--phase', 'Phase 22AE.6.5.10T text-only active import micro-proof plan', '--summary', '10T staged a plan-only text-only active import micro-proof, deriving a 60-row baseline roundtrip CSV from the proven full-state text import and leaving execution closed pending explicit 10U authorization.', '--next-gate', row.get('NEXT_GATE','HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_EXECUTION_PACKAGE'), '--source-reports', 'docs/messaging/reports/message_catalog_phase22ae_6_5_10t_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10t_micro_proof_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10t_candidate_artifacts_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10t_risk_register_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10t_boundary_ledger_v1.csv', '--messages', '12', '--text-rows', row.get('BASELINE60_ROWS','60'), '--locales', 'en-US;es;fr;de;it', '--validation-issues', row.get('VALIDATION_ISSUES','0'), '--allowed-candidate-mutations', 'docs/messaging/apply/phase22ae_6_5_10t plan artifacts only', '--forbidden-active-mutations', 'no active text micro proof execution; no active DBF mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation', '--accept-messaging-savepoint']
    return subprocess.call(cmd)
if __name__=='__main__': raise SystemExit(main())
