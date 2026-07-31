#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10R] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10r_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10R] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10R",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10R rollback and failure classification",
        "--summary", "6.5.10R classified the guarded active promotion attempt as a partial active failure, confirmed rollback restored the 12/60 baseline, and held active retry pending active text import forensics.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10r_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10r_rollback_runtime_readback_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10r_failure_classification_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10r_recommendations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10r_boundary_ledger_v1.csv",
        "--messages", "12",
        "--text-rows", "60",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only rollback/failure classification",
        "--forbidden-active-mutations", "no active promotion retry; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
