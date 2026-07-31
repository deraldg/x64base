#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_5_3_ACTIVE_CATALOG_ROLLBACK_EXECUTED"

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
        print("[MSG-022AE.5.3] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_5_3_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.5.3] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.5.3",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.5.3 active catalog rollback execution",
        "--summary", "Active messaging catalog rollback executed: archived partial 14/70 state, restored selected 22AE.5 backup, and returned active counts to 12 messages / 60 text rows. No source, HELP DATA, or CMDHELPCHK mutation.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_5_3_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_3_partial_archive_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_3_restore_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_3_boundary_ledger_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_3_gate_check_v1.csv",
        "--messages", row.get("MESSAGE_ROWS_AFTER_ROLLBACK", "12"),
        "--text-rows", row.get("TEXT_ROWS_AFTER_ROLLBACK", "60"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "active messaging DBF/CDX/LMDB rollback from selected backup; partial state archived first",
        "--forbidden-active-mutations", "no source edits; no HELP DATA mutation; no CMDHELPCHK mutation; no command registry mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
