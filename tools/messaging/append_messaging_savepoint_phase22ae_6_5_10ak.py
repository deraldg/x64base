#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AK_POST_PROMOTION_MESSAGING_CATALOG_CLOSEOUT_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AK] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ak_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AK] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2
    if row.get("ACTIVE_PROMOTION_CLOSEOUT_ACCEPTED") != "1" or row.get("ROLLBACK_REQUIRED") != "0":
        print("[MSG-022AE.6.5.10AK] Refusing savepoint: closeout not accepted or rollback required", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AK",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AK post-promotion messaging catalog closeout",
        "--summary", "10AK closed the active messaging catalog promotion lane at SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70, retained rollback backup as archive evidence, and listed follow-up items for future gates.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AL_FOLLOWUP_INDEX_LMDB_OR_RUNTIME_MESSAGE_CONSUMER_PLAN"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ak_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ak_chain_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ak_closeout_ledger_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ak_retained_artifacts_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ak_boundary_ledger_v1.csv",
        "--messages", "14",
        "--text-rows", "70",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only post-promotion closeout",
        "--forbidden-active-mutations", "no active DBF mutation; no rollback; no backup deletion; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
