#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AT_MESSAGING_WORKSPACE_AND_CONSUMER_SUMMARY_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AT] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10at_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AT] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AT",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AT messaging workspace and consumer summary",
        "--summary", "10AT summarized the completed Message Manager consumer and workspace profile proof chain: active catalog 14/70, MSGMGR command-house, SET MESSAGE CATALOG CHECK/GET, and dedicated workspace restore proof. It staged next-lane options without mutation.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AU_NEXT_MESSAGING_WORK_LANE_DECISION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10at_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10at_evidence_matrix_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10at_next_options_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10at_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_OBSERVED_COUNT", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_OBSERVED_COUNT", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only summary",
        "--forbidden-active-mutations", "no active DBF mutation; no CDX/LMDB mutation; no workspace mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
