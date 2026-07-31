#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AR_MESSAGE_MANAGER_CONSUMER_CLOSEOUT_GREEN_CONTINUE_READY_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AR] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ar_revised_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AR] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AR",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AR revised Message Manager consumer closeout",
        "--summary", "10AR closed the Message Manager consumer proof lane while keeping continuation open: MSGMGR is canonical, SET MESSAGE CATALOG CHECK/GET are proven read surfaces, active catalog remains 14/70, and workspace profile proof is the recommended next lane. DTSCHEMA/DTSHEMA spelling is deferred polish.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ar_revised_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ar_revised_closeout_items_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ar_revised_workspace_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ar_revised_next_options_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ar_revised_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_OBSERVED_COUNT", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_OBSERVED_COUNT", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only revised closeout",
        "--forbidden-active-mutations", "no active DBF mutation; no source edits; no alias mutation; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
