#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10S] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10s_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10S] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10S",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10S active text import failure forensic review",
        "--summary", "10S completed report-only forensics on the active SYSTEM_MESSAGE_TEXT import failure after rollback. It compared active, sandbox, backup, CSV, sidecar, index, and LMDB evidence and kept active retry closed.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10T_TEXT_ONLY_ACTIVE_IMPORT_MICRO_PROOF_PLAN"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10s_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10s_import_csv_comparison_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10s_dbf_header_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10s_artifact_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10s_likely_causes_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10s_boundary_ledger_v1.csv",
        "--messages", "12",
        "--text-rows", "60",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only active text import failure forensics",
        "--forbidden-active-mutations", "no active promotion retry; no active DBF mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
