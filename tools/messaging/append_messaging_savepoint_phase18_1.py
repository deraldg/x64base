#!/usr/bin/env python3
"""Append Phase 18.1 Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE18_1_ACTIVE_PROMOTION_GREEN"

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
        print("[MSG-018.1] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase18_1_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-018.1] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Active Messaging catalog promotion green after memo-sidecar repair: proven x64 DBF/CDX/LMDB candidate promoted to active messaging data layout. "
        f"DBF files promoted: {row.get('ACTIVE_DBF_FILES_PROMOTED','')}; DBF sidecars promoted: {row.get('ACTIVE_DBF_SIDECARS_PROMOTED','')}; "
        f"CDX files promoted: {row.get('ACTIVE_CDX_FILES_PROMOTED','')}; LMDB file rows promoted: {row.get('ACTIVE_LMDB_FILE_ROWS_PROMOTED','')}. "
        "HELP/CMDHELPCHK/source/manualgen/datadict unchanged."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-018.1",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 18.1 active Messaging catalog promotion repair",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_RUN_PHASE18_ACTIVE_READBACK_SMOKE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase18_1_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase18_1_promotion_inventory_v1.csv;docs/messaging/reports/message_catalog_phase18_1_backup_inventory_v1.csv;docs/messaging/reports/message_catalog_phase18_1_boundary_ledger_v1.csv;docs/messaging/reports/message_catalog_phase18_1_active_paths_v1.csv;docs/messaging/reports/message_catalog_phase18_1_candidate_sidecar_inventory_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--boundary-summary", "authorized active Messaging catalog promotion: active messaging DBF/CDX/LMDB artifacts were replaced from the proven x64 candidate; memo sidecars discovered by same-stem scan; no HELP DATA, CMDHELPCHK, source-mining, source, manualgen, datadict, or unrelated active catalog mutation",
        "--allowed-candidate-mutations", "none; Phase 18.1 consumes candidate artifacts",
        "--forbidden-active-mutations", "no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no manualgen mutation; no datadict/SelfDoc mutation; no unrelated active catalog mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
