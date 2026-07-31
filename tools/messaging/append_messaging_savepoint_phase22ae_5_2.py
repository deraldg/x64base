#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.5.2] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_5_2_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.5.2] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.5.2",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.5.2 partial promotion repair or rollback plan",
        "--summary", "Repair/rollback plan green: 22AE.5 partial promotion moved counts to 14/70 but required keys are absent; recommended decision is rollback to selected 22AE.5 backup. No active mutation in 22AE.5.2.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_EXECUTION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_5_2_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_2_decision_matrix_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_2_rollback_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_2_backup_selection_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_2_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGE_ROWS_AFTER", "14"),
        "--text-rows", row.get("TEXT_ROWS_AFTER", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; plan/readback only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
