#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_4_2_BOUNDARY_DELTA_CLASSIFICATION_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.4.2] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_4_2_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.4.2] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.4.2",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.4.2 boundary delta classification",
        "--summary", "Boundary-delta classification green: 6.4.1 remains blocked and unsavepointed; deltas classified; old V1 path reconfirmed as append-without-keys; next path is a fully isolated sandbox proof with sandbox-local index/LMDB pathing.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_4_2_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_2_delta_classification_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_2_root_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_3_isolation_repair_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_2_boundary_ledger_v1.csv",
        "--messages", "12",
        "--text-rows", "60",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report/classification only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
