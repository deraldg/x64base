#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_5_1_PARTIAL_PROMOTION_DIAGNOSTIC_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.5.1] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_5_1_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.5.1] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.5.1",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.5.1 partial promotion diagnostic",
        "--summary", "Partial promotion diagnostic green: 22AE.5 moved active counts to 14/70 but required symbols/text keys were not present in key fields; tail row and field inventories captured. No additional active mutation in 22AE.5.1.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_5_2_PARTIAL_PROMOTION_REPAIR_OR_ROLLBACK_PLAN"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_5_1_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_1_system_messages_tail_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_1_system_message_text_tail_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_1_diagnosis_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_1_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGE_ROWS_AFTER", "14"),
        "--text-rows", row.get("TEXT_ROWS_AFTER", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; diagnostic readback only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
