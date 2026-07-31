#!/usr/bin/env python3
"""Append Phase 22A Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22A_RUNTIME_SOURCE_INTEGRATION_PROBE_GREEN_SOURCE_HELD"

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
        print("[MSG-022A] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase22a_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022A] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Runtime source-integration probe green, source held: source seams mapped and Phase 22B guarded provider patch plan created. "
        "No source files or active catalogs were mutated."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022A",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22A runtime Messaging source-integration probe",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22B_GUARDED_RUNTIME_PROVIDER_SOURCE_PATCH"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22a_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22a_source_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22a_source_pattern_hits_v1.csv;docs/messaging/reports/message_catalog_phase22a_integration_seams_v1.csv;docs/messaging/reports/message_catalog_phase22a_guarded_patch_plan_v1.csv;docs/messaging/reports/message_catalog_phase22a_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22A probe/reporting only",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
