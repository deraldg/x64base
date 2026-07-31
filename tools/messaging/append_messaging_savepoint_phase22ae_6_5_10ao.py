#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

ALLOWED = {
    "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_GREEN_EXISTING_SURFACE_OBSERVED",
    "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_GREEN_CONSUMER_SURFACE_GAP_CONFIRMED",
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
        print("[MSG-022AE.6.5.10AO] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ao_validate_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status not in ALLOWED:
        print(f"[MSG-022AE.6.5.10AO] Refusing savepoint: expected one of {sorted(ALLOWED)}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AO",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AO runtime message consumer read-only probe",
        "--summary", "10AO probed existing HELP/MESSAGE/MSG runtime consumer surfaces read-only while preserving active SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70. Source integration remains unauthorized.",
        "--next-gate", row.get("NEXT_GATE", ""),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ao_stage_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ao_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ao_surface_classification_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ao_runtime_observations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ao_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROBE", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_HEADER_COUNT_AFTER_PROBE", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; runtime consumer read-only probe",
        "--forbidden-active-mutations", "no active DBF mutation; no source edits; no runtime consumer source integration; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
