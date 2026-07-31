#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22R_HELP_HINT_ROUTING_PLAN_GREEN_SOURCE_HELD"

def first_row(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--accept-messaging-savepoint", action="store_true")
    args = parser.parse_args()

    if not args.accept_messaging_savepoint:
        print("[MSG-022R] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22r_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022R] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022R",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22R HELP hint routing plan",
        "--summary", "Report-only HELP hint routing plan green: selected narrow HELP_HINT_COMMAND seam for next active-provider routing patch, with HELP DATA/CMDHELPCHK/command registry/manualgen/datadict mutations explicitly out of scope.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22S_HELP_HINT_RUNTIME_ROUTING_PATCH"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22r_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22r_candidate_help_routing_seams_v1.csv;docs/messaging/reports/message_catalog_phase22r_selected_help_hint_routing_plan_v1.csv;docs/messaging/reports/message_catalog_phase22r_phase22s_proof_requirements_v1.csv;docs/messaging/reports/message_catalog_phase22r_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22R report-only HELP hint routing plan",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no command registry mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
