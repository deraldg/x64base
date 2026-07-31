#!/usr/bin/env python3
"""Append Phase 14 Messaging savepoint using installed generic savepoint contract."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE14_INACTIVE_CANDIDATE_CDX_TAG_EXECUTION_GREEN"

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
        print("[MSG-014] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2
    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase14_status_summary_v1.csv"
    if not summary.exists():
        print(f"[MSG-014] Missing Phase 14 summary: {summary}", file=sys.stderr)
        return 2
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-014] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2
    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Candidate-only CDX execution green: "
        f"{row.get('CDX_FILES_CREATED','0')} CDX files created under inactive candidate workspace; "
        f"{row.get('MESSAGES','12')} messages, {row.get('TEXT_ROWS','60')} text rows, locales {row.get('LOCALES','de;en-US;es;fr;it')}. "
        "No LMDB creation and no active catalog promotion."
    )
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-014",
        "--status", status,
        "--phase", "Phase 14 inactive candidate CDX tag execution",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE15_CANDIDATE_LMDB_PLAN_OR_RUNTIME_CDX_READBACK"),
        "--source-report", "docs/messaging/reports/message_catalog_phase14_status_summary_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
