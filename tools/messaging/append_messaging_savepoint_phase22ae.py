#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_OK = {
    "MESSAGE_CATALOG_PHASE22AE_ACTIVE_CATALOG_REPLACEMENT_EXECUTED",
    "MESSAGE_CATALOG_PHASE22AE_ACTIVE_CATALOG_REPLACEMENT_ALREADY_PRESENT_NOOP_GREEN",
}

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
        print("[MSG-022AE] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status not in STATUS_OK:
        print(f"[MSG-022AE] Refusing savepoint: expected one of {sorted(STATUS_OK)}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE active catalog replacement execution",
        "--summary", "Active messaging catalog execution completed/backed up: promoted Phase 22Y proof-status catalog rows or confirmed already present; no source, HELP DATA, CMDHELPCHK, command registry, manualgen, or Data Dictionary/SelfDoc mutation. Follow-up readback/runtime validation required.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AF_ACTIVE_CATALOG_READBACK_AND_RUNTIME_VALIDATION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_backup_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_active_mutation_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22ae_row_apply_readback_v1.csv;docs/messaging/reports/message_catalog_phase22ae_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES_BEFORE", "12"),
        "--text-rows", row.get("TEXT_ROWS_BEFORE", "60"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "active messaging DBF row append only, with active roots backed up first",
        "--forbidden-active-mutations", "no source edits; no HELP DATA mutation; no CMDHELPCHK mutation; no command registry mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
