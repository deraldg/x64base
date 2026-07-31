#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_3_MEMO_AWARE_PROMOTION_PATH_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.3] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_3_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.3] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.3",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.3 memo-aware promotion path",
        "--summary", "Memo-aware promotion path green: direct DBF append is rejected because SYSTEM_MESSAGE_TEXT.TEXT is memo-backed; next active promotion must use a memo-aware runtime/import path. No active catalog/source/HELP/CMDHELPCHK mutation in 22AE.3.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_4_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_3_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_3_active_dbf_memo_probe_v1.csv;docs/messaging/reports/message_catalog_phase22ae_3_active_dbf_field_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_3_memo_aware_promotion_path_v1.csv;docs/messaging/reports/message_catalog_phase22ae_3_boundary_ledger_v1.csv",
        "--messages", "12",
        "--text-rows", "60",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; memo-aware promotion path probe only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
