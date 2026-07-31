#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_7_CANONICAL_FIELD_MAP_REPAIR_REVIEW_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.7] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_7_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.7] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.7",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.7 canonical field-map repair review",
        "--summary", "6.5.7 performed report-only forensic review of why canonical field-map ZAP/IMPORT reached counts but no exact keys. Next path is a runtime-assisted key probe and field-map patch.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_8_CANONICAL_KEY_PROBE_AND_FIELD_MAP_PATCH"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_7_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_7_csv_key_hits_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_7_dbf_key_hits_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_7_tail_row_comparison_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_7_recommendations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_7_boundary_ledger_v1.csv",
        "--messages", row.get("SANDBOX_MESSAGE_ROWS_AFTER_6_5_6", ""),
        "--text-rows", row.get("SANDBOX_TEXT_ROWS_AFTER_6_5_6", ""),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only forensic review",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
