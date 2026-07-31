#!/usr/bin/env python3
"""Append Phase 19 Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE19_ACTIVE_READBACK_SMOKE_GREEN"

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
        print("[MSG-019] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase19_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-019] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Active Messaging readback smoke green: promoted active SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT open as v64 with expected counts. "
        "TEXT M, MSGLOCALE, and SYMBOLLOC present. Active CDX/LMDB query proof deferred as optional follow-up."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-019",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 19 active Messaging readback smoke closeout",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE20_ACTIVE_INDEX_LMDB_QUERY_SMOKE_OR_PHASE18_LOCALE_SPINE_EXTENSION"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase19_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase19_gate_check_v1.csv;docs/messaging/reports/message_catalog_phase19_boundary_ledger_v1.csv;docs/messaging/reports/MESSAGE_CATALOG_PHASE19_ACTIVE_READBACK_SMOKE_CLOSEOUT.md;docs/messaging/runlog/MSG-019_ACTIVE_READBACK_SMOKE.md",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 19 readback validation only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
