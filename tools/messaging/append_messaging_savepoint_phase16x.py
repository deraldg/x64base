#!/usr/bin/env python3
"""Append Phase 16X Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE16X_X64_CANDIDATE_LMDB_BUILD_GREEN"

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
        print("[MSG-016X] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase16x_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-016X] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "x64 candidate LMDB build green: BUILDLMDB created candidate-only MDB/LMDB artifacts over the Phase 15X x64 messaging candidate. "
        f"MDB files: {row.get('LMDB_MDB_FILES','')}; data.mdb files: {row.get('LMDB_DATA_MDB_FILES','')}; env dirs: {row.get('LMDB_ENV_DIRS','')}. "
        "No active catalog promotion."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-016X",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 16X x64 candidate LMDB build",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE17_PROMOTION_READINESS_REVIEW"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase16x_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase16x_lmdb_artifact_inventory_v1.csv;docs/messaging/reports/message_catalog_phase16x_gate_check_v1.csv;docs/messaging/reports/message_catalog_phase16x_boundary_ledger_v1.csv;docs/messaging/runlog/MSG-016X_X64_LMDB_RUNTIME_PROOF.md",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "inactive x64 candidate LMDB/MDB artifacts created under docs/messaging/candidates/phase15x_x64_candidate_rebuild/lmdb",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no active catalog promotion",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
