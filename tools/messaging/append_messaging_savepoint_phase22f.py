#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22F_ACTIVE_DBF_ROW_LOAD_PROVIDER_SMOKE_GREEN"

def read_first(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()
    if not args.accept_messaging_savepoint:
        print("[MSG-022F] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase22f_runtime_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022F] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Active DBF row-load provider smoke green: SET MESSAGE CATALOG CHECK reports mode active_dbf, active catalog loaded yes, "
        "12 active message rows, 60 active text rows, with read-only/no-writeback boundary."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022F",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22F active DBF row-load provider smoke",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22G_SET_LANGUAGE_ACTIVE_CATALOG_LOOKUP"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22f_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22f_source_mutation_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22f_runtime_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22f_runtime_gate_check_v1.csv;docs/messaging/runlog/MSG-022F_ACTIVE_DBF_LOAD_PROVIDER_SMOKE.md",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22F runtime smoke only after source provider patch apply",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
