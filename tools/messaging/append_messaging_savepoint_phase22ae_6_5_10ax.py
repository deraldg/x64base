#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

ALLOWED = {
    "MESSAGE_CATALOG_PHASE22AE_6_5_10AX_MSGMGR_HELP_CANDIDATE_REVIEW_GREEN_CANDIDATE_ACCEPTED_SOURCE_HELD",
    "MESSAGE_CATALOG_PHASE22AE_6_5_10AX_MSGMGR_HELP_CANDIDATE_REVIEW_GREEN_CANDIDATE_REVIEW_ITEMS_SOURCE_HELD",
}

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
        print("[MSG-022AE.6.5.10AX] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ax_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status not in ALLOWED:
        print(f"[MSG-022AE.6.5.10AX] Refusing savepoint: expected one of {sorted(ALLOWED)}, got {status}", file=sys.stderr)
        return 2
    if row.get("HELP_DATA_APPLY_AUTHORIZED") != "0" or row.get("CMDHELPCHK_APPLY_AUTHORIZED") != "0":
        print("[MSG-022AE.6.5.10AX] Refusing savepoint: apply authorization must remain 0", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AX",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AX MSGMGR HELP candidate review",
        "--summary", "10AX reviewed the 10AW MSGMGR HELP candidate and classified readiness for guarded HELP/CMDHELPCHK apply planning while keeping apply authorization at 0.",
        "--next-gate", row.get("NEXT_GATE", ""),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10ax_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ax_candidate_review_checklist_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ax_surface_disposition_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ax_apply_readiness_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10ax_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_OBSERVED_COUNT", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_OBSERVED_COUNT", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; review-only",
        "--forbidden-active-mutations", "no active DBF mutation; no CDX/LMDB mutation; no workspace mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
