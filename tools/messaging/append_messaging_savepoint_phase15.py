#!/usr/bin/env python3
"""Append Phase 15 Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE15_CANDIDATE_LMDB_PLAN_GREEN"

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
        print("[MSG-015] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase15_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-015] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Candidate LMDB plan green: Phase 15 planned future candidate-only LMDB build after Phase 14 CDX proof. "
        f"{row.get('CDX_FILES_AVAILABLE','2')} candidate CDX files available. No LMDB environment created."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-015",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 15 candidate LMDB plan",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE16_INACTIVE_CANDIDATE_LMDB_BUILD"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase15_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase15_candidate_lmdb_build_plan_v1.csv;docs/messaging/reports/message_catalog_phase15_gate_check_v1.csv;docs/messaging/reports/message_catalog_phase15_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none in Phase 15; planning/reporting only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no LMDB creation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no active catalog promotion",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
