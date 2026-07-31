#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BY_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_RUN_AND_READBACK_GREEN_EXECUTION_HELD_NATIVE_IMPLEMENTATION_REQUIRED"

def first(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        r = list(csv.DictReader(f))
    return r[0] if r else {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()
    if not args.accept_messaging_savepoint:
        print("[MSG-022AE.6.5.10BY] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2
    repo = Path(args.repo_root).resolve()
    row = first(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10by_status_summary_v1.csv")
    if row.get("STATUS") != GREEN:
        print(f"[MSG-022AE.6.5.10BY] Refusing savepoint: got {row.get('STATUS','')}", file=sys.stderr)
        return 2
    if row.get("HELP_DATA_MUTATION_OBSERVED") != "0" or row.get("CMDHELPCHK_MUTATION_OBSERVED") != "0":
        print("[MSG-022AE.6.5.10BY] Refusing savepoint: protected mutation observed unexpectedly", file=sys.stderr)
        return 2
    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10BY",
        "--lane", "MESSAGING",
        "--status", row["STATUS"],
        "--phase", "Phase 22AE.6.5.10BY HELP/CMDHELPCHK guarded apply execution run and readback",
        "--summary", "10BY accepted the apply authorization switch but held execution pending target-specific native/schema-aware apply implementation. No protected HELP DATA or CMDHELPCHK mutation occurred.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BZ_TARGET_SPECIFIC_NATIVE_APPLY_IMPLEMENTATION_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10by_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10by_execution_result_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10by_native_apply_requirements_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10by_readback_observation_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10by_boundary_ledger_v1.csv",
        "--messages", str(row.get("ACTIVE_MESSAGES_COUNT_AFTER", "14")),
        "--text-rows", str(row.get("ACTIVE_TEXT_COUNT_AFTER", "70")),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", str(row.get("VALIDATION_ISSUES", "0")),
        "--allowed-candidate-mutations", "docs/messaging guarded apply run/readback reports only",
        "--forbidden-active-mutations", "no active DBF mutation; no CDX/LMDB mutation; no workspace mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
