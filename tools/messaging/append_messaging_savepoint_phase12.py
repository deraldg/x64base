#!/usr/bin/env python3
"""Append Phase 12 Messaging savepoint using the installed generic savepoint contract."""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE12_CANDIDATE_DBF_ROW_PARITY_GREEN"

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
        print("[MSG-012] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase12_status_summary_v1.csv"
    if not summary.exists():
        print(f"[MSG-012] Missing Phase 12 summary: {summary}", file=sys.stderr)
        return 2

    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-012] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    if not generic.exists():
        print(f"[MSG-012] Missing generic savepoint tool: {generic}", file=sys.stderr)
        return 2

    summary_text = (
        "Candidate DBF row/memo parity green: "
        f"{row.get('MESSAGES','12')} messages, {row.get('TEXT_ROWS','60')} text rows, "
        f"locales {row.get('LOCALES','de;en-US;es;fr;it')}, validation issues {row.get('VALIDATION_ISSUES','0')}. "
        "Phase 12 reads existing inactive candidate DBF/DBT files only; no new DBF/DBT creation; "
        "no CDX/index creation; no LMDB creation; no active DBF catalog mutation; no HELP DATA mutation; "
        "no CMDHELPCHK mutation; no source-mining mutation; no source edits; no runtime execution; no active catalog promotion."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-012",
        "--status", status,
        "--phase", "Phase 12 candidate DBF row/memo parity readback",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE13_CANDIDATE_CDX_TAG_PLAN"),
        "--source-report", "docs/messaging/reports/message_catalog_phase12_status_summary_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
