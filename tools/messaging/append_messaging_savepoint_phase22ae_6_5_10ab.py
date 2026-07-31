#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AB_FULL70_TEXT_SEQUENCE_RESULT_CLASSIFICATION_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AB] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ab_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AB] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AB",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AB full70 text sequence result classification",
        "--summary", "10AB classified full70 text-only ZAP/import as proven, candidate10 and baseline60 as proven, and redirected the investigation to the two-table promotion sequence. Full active promotion retry remains closed.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AC_TWO_TABLE_PROMOTION_SEQUENCE_PLAN"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ab_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ab_evidence_matrix_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ab_full70_text_result_classification_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ab_next_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ab_boundary_ledger_v1.csv",
        "--messages", "12",
        "--text-rows", "60",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only full70 text sequence result classification",
        "--forbidden-active-mutations", "no full active promotion retry; no active DBF mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
