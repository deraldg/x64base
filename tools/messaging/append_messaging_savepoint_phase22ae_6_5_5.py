#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_5_FIELD_MAP_FORENSIC_REVIEW_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.5] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_5_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.5] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.5",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.5 field-map forensic review",
        "--summary", "6.5.5 accepted 6.5.4 as clean counts-only ZAP/IMPORT evidence and selected canonical Phase22AD rows plus explicit DBF field mapping as the next safe path.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_5_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_5_source_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_5_selected_source_assessment_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_5_diagnosis_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_5_recommendations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_5_boundary_ledger_v1.csv",
        "--messages", row.get("SANDBOX_MESSAGE_ROWS_AFTER_6_5_4", ""),
        "--text-rows", row.get("SANDBOX_TEXT_ROWS_AFTER_6_5_4", ""),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only forensic review",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
