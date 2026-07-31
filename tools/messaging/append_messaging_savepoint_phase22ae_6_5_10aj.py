#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AJ_POST_PROMOTION_ACCEPTANCE_AND_BACKUP_RETENTION_PLAN_GREEN_SOURCE_HELD"

def first_row(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()
    if not args.accept_messaging_savepoint:
        print("[MSG-022AE.6.5.10AJ] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10aj_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AJ] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2
    if row.get("ACTIVE_PROMOTION_ACCEPTED") != "1" or row.get("ROLLBACK_REQUIRED") != "0":
        print("[MSG-022AE.6.5.10AJ] Refusing savepoint: promotion not accepted or rollback required", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AJ",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AJ post-promotion acceptance and backup retention plan",
        "--summary", "10AJ accepted the promoted active messaging catalog state at SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70, classified rollback as not required, and retained the 10AH rollback backup as archive evidence with no deletion authorized.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AK_POST_PROMOTION_MESSAGING_CATALOG_CLOSEOUT"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10aj_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10aj_acceptance_ledger_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10aj_final_state_declaration_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10aj_backup_retention_policy_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10aj_boundary_ledger_v1.csv",
        "--messages", "14",
        "--text-rows", "70",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only acceptance and backup retention plan",
        "--forbidden-active-mutations", "no active DBF mutation; no rollback; no backup deletion; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)
if __name__ == "__main__":
    raise SystemExit(main())
