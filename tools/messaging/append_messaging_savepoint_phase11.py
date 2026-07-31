#!/usr/bin/env python3
"""Append Phase 11 Messaging savepoint using Messaging Savepoint Thread v1."""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION_GREEN"

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
        print("[MSG-011] Refusing to append savepoint without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase11_status_summary_v1.csv"
    if not summary.exists():
        print(f"[MSG-011] Missing Phase 11 summary: {summary}", file=sys.stderr)
        return 2

    row = read_first_csv(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-011] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    if not generic.exists():
        print(f"[MSG-011] Missing generic savepoint tool: {generic}", file=sys.stderr)
        return 2

    boundary = "inactive candidate DBF/DBT creation allowed and observed; no active DBF catalog mutation; no CDX/index creation; no LMDB creation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no runtime execution; no active catalog promotion"
    source_reports = ";".join([
        "docs/messaging/reports/message_catalog_phase11_status_summary_v1.csv",
        "docs/messaging/reports/message_catalog_phase11_dbf_header_readback_v1.csv",
        "docs/messaging/reports/message_catalog_phase11_candidate_artifact_inventory_v1.csv",
        "docs/messaging/reports/message_catalog_phase11_gate_check_v1.csv",
        "docs/messaging/reports/message_catalog_phase11_boundary_ledger_v1.csv",
    ])

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-011",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 11 inactive candidate DBF execution",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE12_CANDIDATE_CDX_TAG_PLAN_OR_READBACK_RUNTIME_SMOKE"),
        "--source-reports", source_reports,
        "--boundary-summary", boundary,
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
