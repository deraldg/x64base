#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22X_SET_MESSAGE_PROOF_STATUS_TEXT_ROUTING_PLAN_GREEN_SOURCE_HELD"

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
        print("[MSG-022X] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22x_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022X] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022X",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22X SET MESSAGE PROOF status text routing plan",
        "--summary", "Report-only routing plan green: planned MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE for SET MESSAGE PROOF status text; no source/catalog/HELP/CMDHELPCHK mutation.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_CATALOG_AND_SOURCE_PATCH"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22x_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22x_symbol_contract_plan_v1.csv;docs/messaging/reports/message_catalog_phase22x_anchor_plan_v1.csv;docs/messaging/reports/message_catalog_phase22x_future_patch_plan_v1.csv;docs/messaging/reports/message_catalog_phase22x_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22X report-only status text routing plan",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no command registry mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
