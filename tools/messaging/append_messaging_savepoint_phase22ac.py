#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AC_ACTIVE_CATALOG_REPLACEMENT_WITH_BACKUP_PLAN_GREEN_SOURCE_HELD"

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
        print("[MSG-022AC] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ac_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AC] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AC",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AC active catalog replacement with backup plan",
        "--summary", "Active catalog replacement plan green: 2 candidate message rows and 10 candidate text rows are ready for a later guarded active messaging catalog apply with mandatory backup; target counts 14 messages and 70 text rows; no active mutation in 22AC.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AD_ACTIVE_CATALOG_REPLACEMENT_APPLY_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ac_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ac_active_replacement_backup_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ac_active_roots_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ac_apply_scope_v1.csv;docs/messaging/reports/message_catalog_phase22ac_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "en-US;es;fr;de;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22AC plan only",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no command registry mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
