#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AY_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PLAN_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AY] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ay_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AY] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2
    if row.get("HELP_DATA_APPLY_AUTHORIZED") != "0" or row.get("CMDHELPCHK_APPLY_AUTHORIZED") != "0":
        print("[MSG-022AE.6.5.10AY] Refusing savepoint: apply authorization must remain 0", file=sys.stderr)
        return 2
    if row.get("HELP_DATA_MUTATION_OBSERVED") != "0" or row.get("CMDHELPCHK_MUTATION_OBSERVED") != "0":
        print("[MSG-022AE.6.5.10AY] Refusing savepoint: HELP/CMDHELPCHK mutation observed", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AY",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AY MSGMGR HELP/CMDHELPCHK guarded apply plan",
        "--summary", "10AY created a guarded apply plan for later MSGMGR HELP DATA and CMDHELPCHK integration. It produced target, sequence, rollback, validation, and disabled-template artifacts with apply authorization still 0.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AZ_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ay_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ay_target_manifest_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ay_apply_sequence_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ay_rollback_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ay_validation_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ay_boundary_ledger_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ay_artifact_manifest_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_OBSERVED_COUNT", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_OBSERVED_COUNT", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "docs/messaging apply plan, disabled templates, candidate snapshot, and reports only",
        "--forbidden-active-mutations", "no active DBF mutation; no CDX/LMDB mutation; no workspace mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
