#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AG_GUARDED_FINAL_PROMOTION_PLAN_FROM_10AD_PATTERN_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AG] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ag_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AG] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AG",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AG guarded final promotion plan from 10AD pattern",
        "--summary", "10AG staged a plan-only final promotion package from the proven 10AD V1 pattern. Final active execution remains closed for 10AH authorization.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ag_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ag_final_promotion_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ag_acceptance_gates_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ag_rollback_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ag_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_BASELINE_HEADER_COUNT", "12"),
        "--text-rows", row.get("ACTIVE_TEXT_BASELINE_HEADER_COUNT", "60"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "docs/messaging/apply/phase22ae_6_5_10ag plan artifacts only",
        "--forbidden-active-mutations", "no final active promotion execution; no active DBF mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
