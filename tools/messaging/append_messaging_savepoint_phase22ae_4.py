#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE_STAGED_SOURCE_HELD"

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
        print("[MSG-022AE.4] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_4_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.4] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.4",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.4 memo-aware active catalog promotion package",
        "--summary", "Memo-aware promotion package staged green: generated guarded DotTalk++ USE/APPEND/REPLACE candidate DTS for the two 22Y proof-status symbols and ten locale text rows; no active mutation in 22AE.4.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_4_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_4_package_artifact_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_4_candidate_dts_content_validation_v1.csv;docs/messaging/reports/message_catalog_phase22ae_4_execution_guards_v1.csv;docs/messaging/reports/message_catalog_phase22ae_4_boundary_ledger_v1.csv",
        "--messages", "12",
        "--text-rows", "60",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "package files under docs/messaging/apply only; candidate DTS not executed",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
