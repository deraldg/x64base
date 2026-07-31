#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_GREEN"

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
        print("[MSG-022Y] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22y_runtime_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022Y] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022Y",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22Y SET MESSAGE PROOF status text routing patch",
        "--summary", "Guarded source patch and focused smoke green: SET MESSAGE PROOF status text routed through catalog-aware helpers with invariant fallback; boundary text preserved; no active catalog/HELP/CMDHELPCHK mutation.",
        "--next-gate", row.get("NEXT_GATE", "RERUN_PHASE22V_REGRESSION_PACK_AFTER_PHASE22Y_OR_HOLD"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22y_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22y_source_mutation_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22y_runtime_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22y_runtime_gate_check_v1.csv;docs/messaging/runlog/MSG-022Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE.md",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "authorized source mutation in src/cli/cmd_set.cpp only; candidate message rows staged as reports only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no command registry mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
