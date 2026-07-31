#!/usr/bin/env python3
"""Append Phase 15X Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE15X_X64_CANDIDATE_REBUILD_GREEN"

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
        print("[MSG-015X] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase15x_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-015X] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Corrective x64 candidate rebuild green: SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT rebuilt as native x64 candidates, "
        "with precomputed compound-key workaround fields MSGLOCALE and SYMBOLLOC. LMDB remains held."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-015X",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 15X x64 candidate table rebuild",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE16_X64_CANDIDATE_LMDB_BUILD"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase15x_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase15x_gate_check_v1.csv;docs/messaging/reports/message_catalog_phase15x_boundary_ledger_v1.csv;docs/messaging/runlog/MSG-015X_X64_RUNTIME_PROOF.md",
        "--messages", str(row.get("MESSAGES", "12")),
        "--text-rows", str(row.get("TEXT_ROWS", "60")),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", str(row.get("VALIDATION_ISSUES", "0")),
        "--allowed-candidate-mutations", "inactive candidate x64 DBFs created under docs/messaging/candidates/phase15x_x64_candidate_rebuild/dbf; optional candidate x64 CDX files under the matching indexes path",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no LMDB creation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no active catalog promotion",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
