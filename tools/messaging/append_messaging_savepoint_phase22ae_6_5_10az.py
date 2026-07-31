#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path
GREEN="MESSAGE_CATALOG_PHASE22AE_6_5_10AZ_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PACKAGE_GREEN_BACKUP_AND_DRYRUN_READY_APPLY_NOT_EXECUTED"
def first(path):
    with open(path,"r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    return rows[0] if rows else {}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",required=True)
    ap.add_argument("--accept-messaging-savepoint",action="store_true")
    a=ap.parse_args()
    if not a.accept_messaging_savepoint:
        print("[MSG-022AE.6.5.10AZ] Refusing without --accept-messaging-savepoint",file=sys.stderr); return 2
    repo=Path(a.repo_root).resolve()
    row=first(repo/"docs/messaging/reports/message_catalog_phase22ae_6_5_10az_status_summary_v1.csv")
    if row.get("STATUS")!=GREEN:
        print(f"[MSG-022AE.6.5.10AZ] Refusing savepoint: got {row.get('STATUS','')}",file=sys.stderr); return 2
    if row.get("HELP_DATA_APPLY_EXECUTED")!="0" or row.get("CMDHELPCHK_APPLY_EXECUTED")!="0":
        print("[MSG-022AE.6.5.10AZ] Refusing savepoint: apply executed",file=sys.stderr); return 2
    generic=repo/"tools/messaging/append_messaging_savepoint.py"
    cmd=[sys.executable,str(generic),"--repo-root",str(repo),"--savepoint-id","MSG-022AE.6.5.10AZ",
         "--lane","MESSAGING","--status",row["STATUS"],
         "--phase","Phase 22AE.6.5.10AZ MSGMGR HELP/CMDHELPCHK guarded apply package",
         "--summary","10AZ packaged guarded HELP/CMDHELPCHK apply readiness with target discovery, backups, disabled templates, and dry-run artifacts. No HELP DATA or CMDHELPCHK apply was executed.",
         "--next-gate",row.get("NEXT_GATE","HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BA_MSGMGR_HELP_CMDHELPCHK_APPLY_EXECUTION"),
         "--source-reports","docs/messaging/reports/message_catalog_phase22ae_6_5_10az_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10az_target_discovery_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10az_backup_manifest_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10az_dryrun_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10az_apply_readiness_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10az_boundary_ledger_v1.csv",
         "--messages",str(row.get("ACTIVE_MESSAGES_OBSERVED_COUNT","14")),"--text-rows",str(row.get("ACTIVE_TEXT_OBSERVED_COUNT","70")),
         "--locales","en-US;es;fr;de;it","--validation-issues",str(row.get("VALIDATION_ISSUES","0")),
         "--allowed-candidate-mutations","docs/messaging apply package, backups, disabled templates, candidate snapshot, and reports only",
         "--forbidden-active-mutations","no active DBF mutation; no CDX/LMDB mutation; no workspace mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
         "--accept-messaging-savepoint"]
    return subprocess.call(cmd)
if __name__=="__main__":
    raise SystemExit(main())
