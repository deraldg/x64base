#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AB_CATALOG_ROW_CANDIDATE_READBACK_GREEN_SOURCE_HELD"

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
        print("[MSG-022AB] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ab_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AB] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AB",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AB catalog row candidate readback",
        "--summary", "Candidate readback green: 2 candidate message rows and 10 candidate text rows validated for MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE; all five locales and placeholder/invariant contracts pass; target active counts 14 messages and 70 text rows; no source or active catalog mutation.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ab_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ab_candidate_artifact_readback_v1.csv;docs/messaging/reports/message_catalog_phase22ab_candidate_locale_coverage_readback_v1.csv;docs/messaging/reports/message_catalog_phase22ab_candidate_placeholder_contract_readback_v1.csv;docs/messaging/reports/message_catalog_phase22ab_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "en-US;es;fr;de;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22AB readback only",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no command registry mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
