#!/usr/bin/env python3
"""Append Phase 13 Messaging savepoint using installed generic savepoint contract."""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE13_CANDIDATE_CDX_TAG_PLAN_GREEN"

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
        print("[MSG-013] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase13_status_summary_v1.csv"
    if not summary.exists():
        print(f"[MSG-013] Missing Phase 13 summary: {summary}", file=sys.stderr)
        return 2

    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-013] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    if not generic.exists():
        print(f"[MSG-013] Missing generic savepoint tool: {generic}", file=sys.stderr)
        return 2

    summary_text = (
        "Candidate CDX tag plan green: Phase 13 planned candidate-only CDX tag execution for Phase 14. "
        f"{row.get('MESSAGES','12')} messages, {row.get('TEXT_ROWS','60')} text rows, locales {row.get('LOCALES','de;en-US;es;fr;it')}, "
        f"validation issues {row.get('VALIDATION_ISSUES','0')}. No CDX/index files created; no LMDB; no active catalog promotion."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-013",
        "--status", status,
        "--phase", "Phase 13 candidate CDX tag plan",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE14_INACTIVE_CANDIDATE_CDX_TAG_EXECUTION"),
        "--source-report", "docs/messaging/reports/message_catalog_phase13_status_summary_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
