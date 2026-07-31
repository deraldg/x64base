#!/usr/bin/env python3
"""Append Phase 22B Messaging savepoint using boundary model v2."""
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22B_RUNTIME_PROVIDER_PATCH_CANDIDATE_STAGED_SOURCE_HELD"

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
        print("[MSG-022B] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    summary = repo / "docs/messaging/reports/message_catalog_phase22b_status_summary_v1.csv"
    row = read_first(summary)
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022B] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    summary_text = (
        "Runtime provider source patch candidate staged, source held: corrected helpdata_messages.hpp source surface, "
        "staged candidate message_catalog.hpp/cpp provider boundary, and preserved no-source-mutation boundary."
    )

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022B",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22B runtime provider patch candidate staging",
        "--summary", summary_text,
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22C_APPLY_RUNTIME_PROVIDER_SOURCE_PATCH"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22b_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22b_source_surface_v1.csv;docs/messaging/reports/message_catalog_phase22b_candidate_patch_inventory_v1.csv;docs/messaging/reports/message_catalog_phase22b_decisions_v1.csv;docs/messaging/reports/message_catalog_phase22b_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGES", "12"),
        "--text-rows", row.get("TEXT_ROWS", "60"),
        "--locales", row.get("LOCALES", "de;en-US;es;fr;it"),
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "candidate patch files staged under docs/messaging/patches/phase22b_runtime_provider_candidate",
        "--forbidden-active-mutations", "no source edits; no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no HELP DATA mutation; no CMDHELPCHK mutation; no manualgen mutation; no datadict/SelfDoc mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
