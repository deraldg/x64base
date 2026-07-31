#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_GREEN_ACTIVE_PROMOTED"

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
        print("[MSG-022AE.6.5.10AH] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ah_finalize_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AH] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2
    if row.get("ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROMOTION") != "14" or row.get("ACTIVE_TEXT_HEADER_COUNT_AFTER_PROMOTION") != "70":
        print("[MSG-022AE.6.5.10AH] Refusing savepoint: active header counts are not 14/70", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AH",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AH guarded final promotion execution",
        "--summary", "10AH executed the guarded final active promotion using the proven 10AD V1 pattern and left SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70 active. Rollback backup is retained for post-promotion validation.",
        "--next-gate", row.get("NEXT_GATE", "APPEND_MSG_022AE_6_5_10AH_SAVEPOINT_THEN_AUTHORIZE_10AI_POST_PROMOTION_FRESH_READBACK"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ah_prepare_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ah_finalize_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ah_runtime_observations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ah_active_fingerprint_delta_promotion_v1.csv",
        "--messages", "14",
        "--text-rows", "70",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "active SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT promoted to 14/70 by explicit authorization",
        "--forbidden-active-mutations", "no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
