#!/usr/bin/env python3
"""Append Phase 21 Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE21_RUNTIME_INTEGRATION_REVIEW_GREEN_SOURCE_HELD"

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
        print("[MSG-021] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase21_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-021] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Runtime integration review green, source held: active Messaging catalog is proven and ready for an explicitly authorized read-only runtime catalog provider. "
        "Compiled/static fallback should remain in place."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-021",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 21 runtime Messaging catalog integration review",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22_RUNTIME_CATALOG_SOURCE_INTEGRATION_OR_PHASE23_LOCALE_SPINE_EXTENSION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase21_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase21_runtime_integration_decisions_v1.csv;docs/messaging/reports/message_catalog_phase21_source_scan_v1.csv;docs/messaging/reports/message_catalog_phase21_phase22_runtime_integration_plan_v1.csv;docs/messaging/reports/message_catalog_phase21_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 21 review/reporting only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
