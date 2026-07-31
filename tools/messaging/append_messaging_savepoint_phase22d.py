#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22D_BUILD_PROVIDER_BOUNDARY_GREEN"

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
        print("[MSG-022D] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase22d_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022D] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Build/provider boundary closeout green: message_catalog.hpp/cpp present, CMake includes message_catalog.cpp, "
        "and dottalkpp build reported green. Runtime DBF row loading is not yet claimed."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022D",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22D build and provider-boundary closeout",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22E_RUNTIME_PROVIDER_STATUS_COMMAND_SMOKE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22d_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22d_source_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22d_gate_check_v1.csv;docs/messaging/reports/message_catalog_phase22d_boundary_ledger_v1.csv;docs/messaging/runlog/MSG-022D_BUILD_PROVIDER_BOUNDARY.md",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22D validation only",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
