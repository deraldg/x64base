#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_OK = "MESSAGE_CATALOG_PHASE22AE_6_5_6_1_WORK_AREA_SELECT_IMPORT_PROOF_GREEN_NATIVE_14_70_KEYS_MEMO_REVIEW"

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
        print("[MSG-022AE.6.5.6.1] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_6_1_validate_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_OK:
        print(f"[MSG-022AE.6.5.6.1] Refusing savepoint: expected {STATUS_OK}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.6.1",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.6.1 work-area SELECT native IMPORT proof",
        "--summary", "6.5.6.1 proved native DotTalk++ IMPORT CSV in a fresh isolated sandbox with explicit SELECT/work-area discipline, absolute DBF/CSV paths, 14/70 rows, exact candidate keys, no already-open warning, and active catalog clean.",
        "--next-gate", row.get("NEXT_GATE", ""),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_6_1_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_6_1_native_import_result_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_6_1_found_message_keys_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_6_1_found_text_keys_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_6_1_validate_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGE_ROWS_AFTER", ""),
        "--text-rows", row.get("TEXT_ROWS_AFTER", ""),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "fresh isolated sandbox DBF/memo writes through DotTalk++ native IMPORT only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
