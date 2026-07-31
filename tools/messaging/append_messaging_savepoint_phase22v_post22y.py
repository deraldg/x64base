#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22V_POST22Y_REGRESSION_CLOSEOUT_GREEN_SOURCE_HELD"
SAVEPOINT_ID = "MSG-022V-POST-22Y"

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
        print(f"[{SAVEPOINT_ID}] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22v_post22y_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[{SAVEPOINT_ID}] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", SAVEPOINT_ID,
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22V post-22Y regression closeout",
        "--summary", "Post-22Y regression closeout green: Phase 22V regression pack rerun confirms MESSAGE_LOCALE_SET, UNSUPPORTED_MESSAGE_LOCALE, HELP_HINT_COMMAND, proof gating, provider active_dbf, placeholder substitution, FOXHELP fallback zero, and no active catalog/HELP/CMDHELPCHK mutation after the Phase 22Y proof-status patch.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22Z_NEXT_RUNTIME_SEAM_OR_CATALOG_ROW_PROMOTION_PLAN"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22v_post22y_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22v_post22y_seam_status_v1.csv;docs/messaging/reports/message_catalog_phase22v_post22y_metrics_v1.csv;docs/messaging/reports/message_catalog_phase22v_post22y_gate_check_v1.csv;docs/messaging/reports/message_catalog_phase22v_post22y_boundary_ledger_v1.csv;docs/messaging/runlog/MSG-022V_RUNTIME_ROUTING_REGRESSION_SMOKE.md",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22V post-22Y closeout is report/savepoint only",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no command registry mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
