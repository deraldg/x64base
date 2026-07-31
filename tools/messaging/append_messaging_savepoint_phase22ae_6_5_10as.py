#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_GREEN_WORKSPACE_RESTORED"

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
        print("[MSG-022AE.6.5.10AS] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10as_validate_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AS] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AS",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AS messaging workspace profile proof",
        "--summary", "10AS proved the active messaging catalog can be opened as a workspace, saved to a dedicated workspace profile, closed, loaded, and restored with SYSTEM_MESSAGE_TEXT=70 and SYSTEM_MESSAGES=14. Only the dedicated workspace profile mutation was authorized.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AT_MESSAGING_WORKSPACE_AND_CONSUMER_SUMMARY"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10as_stage_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10as_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10as_runtime_observations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10as_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROOF", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_HEADER_COUNT_AFTER_PROOF", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "dedicated workspace profile only",
        "--forbidden-active-mutations", "no active DBF mutation; no CDX/LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
