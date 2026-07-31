#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path
STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AP_EXISTING_CONSUMER_SURFACE_CONTRACT_REVIEW_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AP] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2
    repo = Path(args.repo_root).resolve()
    row = first_row(repo/"docs/messaging/reports/message_catalog_phase22ae_6_5_10ap_status_summary_v1.csv")
    status = row.get("STATUS","")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AP] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2
    generic = repo/"tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic), "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AP", "--lane", "MESSAGING", "--status", status,
        "--phase", "Phase 22AE.6.5.10AP existing consumer surface contract review",
        "--summary", "10AP accepted MSGMGR as the canonical Message Manager command-house surface, kept SET MESSAGE CATALOG CHECK/GET as low-level proof/read surfaces, and deferred aliases/source integration to later explicit gates.",
        "--next-gate", row.get("NEXT_GATE","HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ap_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ap_command_contract_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ap_alias_policy_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ap_low_level_surfaces_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ap_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_OBSERVED_COUNT","14"), "--text-rows", row.get("ACTIVE_TEXT_OBSERVED_COUNT","70"),
        "--locales", "en-US;es;fr;de;it", "--validation-issues", row.get("VALIDATION_ISSUES","0"),
        "--allowed-candidate-mutations", "none; report-only consumer surface contract review",
        "--forbidden-active-mutations", "no active DBF mutation; no source edits; no alias mutation; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
