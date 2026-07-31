#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AC_TWO_TABLE_PROMOTION_SEQUENCE_PLAN_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AC] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ac_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AC] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AC",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AC two-table promotion sequence plan",
        "--summary", "10AC staged plan-only two-table promotion sequence variants using message14 and text70 inputs, with explicit readback gates and execution closed for 10AD authorization.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_EXECUTION_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ac_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ac_sequence_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ac_variant_templates_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ac_decision_matrix_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ac_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGE14_ROWS", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_BASELINE_HEADER_COUNT", "60"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "docs/messaging/apply/phase22ae_6_5_10ac plan artifacts only",
        "--forbidden-active-mutations", "no two-table execution; no active DBF mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
