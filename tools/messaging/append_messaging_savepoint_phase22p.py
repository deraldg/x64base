#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22P_NEXT_LOW_RISK_ROUTING_SEAM_PLAN_GREEN_SOURCE_HELD"

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
        print("[MSG-022P] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22p_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022P] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022P",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22P next low-risk runtime routing seam plan",
        "--summary", "Report-only next-seam plan green: selected SET LANGUAGE unsupported-locale rejection/status path using UNSUPPORTED_MESSAGE_LOCALE as the next low-risk active-provider routing seam.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22Q_UNSUPPORTED_LOCALE_RUNTIME_ROUTING_PATCH"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22p_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22p_candidate_runtime_seams_v1.csv;docs/messaging/reports/message_catalog_phase22p_selected_runtime_routing_plan_v1.csv;docs/messaging/reports/message_catalog_phase22p_phase22q_proof_requirements_v1.csv;docs/messaging/reports/message_catalog_phase22p_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22P report-only next routing seam plan",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
