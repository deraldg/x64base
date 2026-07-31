#!/usr/bin/env python3
"""Append Phase 17 Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE17_PROMOTION_READINESS_REVIEW_GREEN_PROMOTION_HELD"

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
        print("[MSG-017] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase17_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-017] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Promotion-readiness review green, promotion held: x64 candidate DBF/CDX/LMDB proof is green, "
        "but active promotion is held pending Phase 18 locale spine candidate extension."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-017",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 17 promotion-readiness and schema-scope review",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE18_LOCALE_SPINE_CANDIDATE_EXTENSION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase17_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase17_scope_decisions_v1.csv;docs/messaging/reports/message_catalog_phase17_candidate_table_scope_v1.csv;docs/messaging/reports/message_catalog_phase17_phase18_locale_spine_plan_v1.csv;docs/messaging/reports/message_catalog_phase17_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none in Phase 17; review/reporting only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no active catalog promotion",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
