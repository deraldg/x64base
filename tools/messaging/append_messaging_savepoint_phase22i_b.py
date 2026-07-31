#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path
EXP="MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_SMOKE_GREEN"
def first(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f: 
        r=list(csv.DictReader(f))
    return r[0] if r else {}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root", required=True); ap.add_argument("--accept-messaging-savepoint", action="store_true"); args=ap.parse_args()
    if not args.accept_messaging_savepoint:
        print("[MSG-022I-B] Refusing without --accept-messaging-savepoint", file=sys.stderr); return 2
    repo=Path(args.repo_root).resolve(); row=first(repo/"docs/messaging/reports/message_catalog_phase22i_b_runtime_status_summary_v1.csv")
    if row.get("STATUS","") != EXP:
        print(f"[MSG-022I-B] Refusing savepoint: expected {EXP}, got {row.get('STATUS','')}", file=sys.stderr); return 2
    generic=repo/"tools/messaging/append_messaging_savepoint.py"
    cmd=[sys.executable,str(generic),"--repo-root",str(repo),"--savepoint-id","MSG-022I-B","--lane","MESSAGING","--status",row.get("STATUS",""),"--phase","Phase 22I-B controlled runtime emission diagnostic command","--summary","Controlled runtime emission smoke green: SET MESSAGE EMIT HELP_HINT_COMMAND emitted active DBF-backed text for locale es through explicit diagnostic command, with read-only/no-writeback boundary.","--next-gate",row.get("NEXT_GATE","HOLD_OR_AUTHORIZE_PHASE22J_PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW"),"--source-reports","docs/messaging/reports/message_catalog_phase22i_b_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22i_b_source_mutation_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22i_b_runtime_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22i_b_runtime_gate_check_v1.csv;docs/messaging/runlog/MSG-022I_B_CONTROLLED_EMIT_SMOKE.md","--messages",row.get("MESSAGES","12"),"--text-rows",row.get("TEXT_ROWS","60"),"--locales",row.get("LOCALES","de;en-US;es;fr;it"),"--validation-issues",row.get("VALIDATION_ISSUES","0"),"--allowed-candidate-mutations","none; Phase 22I-B runtime validation after authorized source patch","--forbidden-active-mutations","no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no manualgen mutation; no datadict/SelfDoc mutation","--accept-messaging-savepoint"]
    return subprocess.call(cmd)
if __name__=="__main__": raise SystemExit(main())
