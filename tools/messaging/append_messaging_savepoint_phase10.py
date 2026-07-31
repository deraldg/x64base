#!/usr/bin/env python3
"""
Append Phase 10 Messaging savepoint.

This uses the generic append_messaging_savepoint.py created by
Messaging Savepoint Thread v1.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE10_CANDIDATE_DBF_EXECUTION_PLAN_GREEN"

def read_first_csv(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()

    if not args.accept_messaging_savepoint:
        print("[MSG-010] Refusing to append savepoint without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary_path = repo / "docs/messaging/reports/message_catalog_phase10_status_summary_v1.csv"
    if not summary_path.exists():
        print(f"[MSG-010] Missing Phase 10 summary: {summary_path}", file=sys.stderr)
        return 2

    row = read_first_csv(summary_path)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-010] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    if not generic.exists():
        print(f"[MSG-010] Missing generic savepoint tool: {generic}", file=sys.stderr)
        return 2

    boundary = "no DBF writes; no CDX/index creation; no LMDB creation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no runtime execution; no active catalog promotion"
    source_reports = ";".join([
        "docs/messaging/reports/message_catalog_phase10_status_summary_v1.csv",
        "docs/messaging/reports/message_catalog_phase10_candidate_dbf_execution_plan_v1.csv",
        "docs/messaging/reports/message_catalog_phase10_candidate_dts_plan_v1.csv",
        "docs/messaging/reports/message_catalog_phase10_readback_validation_plan_v1.csv",
        "docs/messaging/reports/message_catalog_phase10_gate_check_v1.csv",
        "docs/messaging/reports/message_catalog_phase10_boundary_ledger_v1.csv",
    ])

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-010",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 10 candidate DBF execution plan",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION"),
        "--source-reports", source_reports,
        "--boundary-summary", boundary,
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
