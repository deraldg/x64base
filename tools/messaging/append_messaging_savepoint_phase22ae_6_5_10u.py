#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_OK = {
    "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED",
    "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_FAILED_BUT_RESTORED",
}

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
        print("[MSG-022AE.6.5.10U] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status not in STATUS_OK:
        print(f"[MSG-022AE.6.5.10U] Refusing savepoint: expected one of {sorted(STATUS_OK)}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10U",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10U text-only active baseline roundtrip",
        "--summary", "10U executed a text-only active SYSTEM_MESSAGE_TEXT baseline60 roundtrip diagnostic and restored the exact backup before savepoint. Result is recorded in the restore status.",
        "--next-gate", row.get("NEXT_GATE", ""),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10u_prepare_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10u_finalize_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10u_runtime_observations_v1.csv",
        "--messages", "12",
        "--text-rows", row.get("POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT", ""),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "temporary active SYSTEM_MESSAGE_TEXT diagnostic mutation restored before savepoint",
        "--forbidden-active-mutations", "no active SYSTEM_MESSAGES mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
