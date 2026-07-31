#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_2_ALTERNATIVE_SANDBOX_WRITE_PATH_PLAN_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.2] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_2_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.2] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.2",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.2 alternative sandbox write path plan",
        "--summary", "Alternative sandbox write path plan green: 22AE.6.1 safely confirmed the old path appends rows without populated keys; 22AE.6.2 keeps active promotion closed and selects sandbox-only alternative write proof variants.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_2_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_2_alternative_path_matrix_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_3_candidate_proof_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_2_forbidden_paths_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_2_boundary_ledger_v1.csv",
        "--messages", "12",
        "--text-rows", "60",
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; plan/report only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
