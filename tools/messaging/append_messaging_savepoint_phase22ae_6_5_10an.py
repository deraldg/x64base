#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AN_RUNTIME_MESSAGE_CONSUMER_INTEGRATION_PLAN_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10AN] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10an_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.5.10AN] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10AN",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.10AN runtime message consumer integration plan",
        "--summary", "10AN defined the runtime message-consumer lookup contract and recommended a read-only consumer probe before any source/runtime integration. Source integration remains unauthorized.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10an_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10an_lookup_contract_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10an_consumer_surfaces_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10an_readonly_probe_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10an_boundary_ledger_v1.csv",
        "--messages", row.get("ACTIVE_MESSAGES_OBSERVED_COUNT", "14"),
        "--text-rows", row.get("ACTIVE_TEXT_OBSERVED_COUNT", "70"),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report-only runtime consumer integration plan",
        "--forbidden-active-mutations", "no active DBF mutation; no source edits; no runtime consumer source integration; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
