#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22M_LOW_RISK_SET_LANGUAGE_RUNTIME_ROUTING_SMOKE_GREEN"

def first_row(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--accept-messaging-savepoint", action="store_true")
    args = parser.parse_args()

    if not args.accept_messaging_savepoint:
        print("[MSG-022M] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22m_runtime_status_summary_v1.csv")
    status = row.get("STATUS", "")

    if status != STATUS_EXPECTED:
        print(f"[MSG-022M] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022M",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22M low-risk SET LANGUAGE runtime message routing",
        "--summary", "First low-risk runtime routing smoke green: SET LANGUAGE/SET LOCALE status output routed through active DBF provider symbol MESSAGE_LOCALE_SET with compiled fallback preserved and read-only/no-writeback boundary.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22N_ROUTING_PROOF_LINE_REVIEW_OR_NEXT_LOW_RISK_SEAM"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22m_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22m_source_mutation_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22m_runtime_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22m_runtime_gate_check_v1.csv;docs/messaging/runlog/MSG-022M_SET_LANGUAGE_ROUTING_SMOKE.md",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; Phase 22M runtime validation after authorized source patch",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
