#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

ALLOWED = {
    "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_GREEN_NO_REBUILD_REQUIRED_YET",
    "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_GREEN_REBUILD_DECISION_REVIEW",
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
        print("[MSG-022AE.6.5.10AM] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10am_validate_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status not in ALLOWED:
        print(f"[MSG-022AE.6.5.10AM] Refusing savepoint: expected one of {sorted(ALLOWED)}, got {status}", file=sys.stderr)
        return 2
    if row.get("ARTIFACT_FINGERPRINT_DELTA_ROWS") != "0":
        print("[MSG-022AE.6.5.10AM] Refusing savepoint: artifact fingerprints changed during read-only verification", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AM",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AM read-only index/LMDB verification",
        "--summary", "10AM performed read-only active messaging catalog index/LMDB verification with USE/COUNT/LIST only, leaving active artifacts unchanged and active rows at SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70.",
        "--next-gate", row.get("NEXT_GATE", ""),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10am_stage_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10am_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10am_runtime_observations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10am_artifact_fingerprint_delta_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10am_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_HEADER_COUNT_AFTER_READBACK", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_HEADER_COUNT_AFTER_READBACK", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; read-only index/LMDB verification",
        "--forbidden-active-mutations", "no active DBF mutation; no CDX/LMDB rebuild; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
