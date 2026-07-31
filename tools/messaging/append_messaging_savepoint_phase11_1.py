#!/usr/bin/env python3
"""Append Phase 11.1 repair Messaging savepoint using installed generic savepoint contract."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION_GREEN"

def read_first(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()

    if not args.accept_messaging_savepoint:
        print("[MSG-011R] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase11_status_summary_v1.csv"
    row = read_first(summary)
    if row.get("STATUS", "") != STATUS_EXPECTED:
        print(f"[MSG-011R] Refusing: Phase 11 summary not green: {row.get('STATUS','')}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Phase 11.1 repair green: inactive candidate DBF/DBT files regenerated with corrected memo pointers. "
        "This corrects the Phase 12 parity failure where memo-backed TEXT rows read back blank. "
        "Active catalog promotion remains unauthorized; no CDX/LMDB/HELP/CMDHELPCHK/source-mining mutation."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-011R",
        "--status", "MESSAGE_CATALOG_PHASE11_1_MEMO_POINTER_REPAIR_GREEN",
        "--phase", "Phase 11.1 memo pointer repair for inactive candidate DBF execution",
        "--summary", summary_text,
        "--next-gate", "RERUN_PHASE12_CANDIDATE_DBF_ROW_PARITY",
        "--source-report", "docs/messaging/reports/message_catalog_phase11_status_summary_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
