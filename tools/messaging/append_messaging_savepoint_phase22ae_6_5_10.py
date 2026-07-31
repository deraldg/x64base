#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_GREEN_RUNTIME_IMPORT_RECORDED_READBACK_REQUIRED"

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
        print("[MSG-022AE.6.5.10] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10 guarded active promotion execution",
        "--summary", "6.5.10 executed guarded active messaging catalog promotion through DotTalk++ runtime ZAP/reopen/IMPORT, recorded active DBF header counts 14/70, and requires 6.5.11 active provider readback/runtime validation.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_11_ACTIVE_CATALOG_READBACK_AND_RUNTIME_VALIDATION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10_runtime_observations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10_active_fingerprint_delta_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10_finalize_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGE_HEADER_COUNT", ""),
        "--text-rows", row.get("ACTIVE_TEXT_HEADER_COUNT", ""),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "active messaging DBF/catalog mutation via DotTalk++ runtime after explicit authorization",
        "--forbidden-active-mutations", "no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
