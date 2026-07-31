#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION_GREEN"

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
        print("[MSG-022AE.5.4] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_5_4_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.5.4] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.5.4",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.5.4 post-rollback readback and runtime regression",
        "--summary", "Post-rollback validation green: active messaging catalog readback is 12/60, active_dbf provider loads, prior runtime-routing seams still prove through active_dbf/compiled fallback as expected, and no active/source/HELP/CMDHELPCHK mutation occurred.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_REDESIGNED_PROMOTION_PATH_PLAN"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_5_4_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_4_gate_check_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_4_runtime_proof_v1.csv;docs/messaging/reports/message_catalog_phase22ae_5_4_boundary_ledger_v1.csv;docs/messaging/runlog/MSG-022AE_5_4_POST_ROLLBACK_RUNTIME_REGRESSION.md",
        "--messages", row.get("ACTIVE_MESSAGE_COUNT", "12"),
        "--text-rows", row.get("ACTIVE_TEXT_ROW_COUNT", "60"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; readback/runtime validation only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
