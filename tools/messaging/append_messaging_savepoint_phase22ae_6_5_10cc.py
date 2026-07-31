#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CC_TARGET_SPECIFIC_NATIVE_APPLY_BUILD_PLAN_REVIEW_GREEN_DISCOVERY_PACKAGE_REQUIRED_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10CC] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2
    repo = Path(args.repo_root).resolve()
    row = first(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10cc_status_summary_v1.csv")
    if row.get("STATUS") != GREEN:
        print(f"[MSG-022AE.6.5.10CC] Refusing savepoint: got {row.get('STATUS','')}", file=sys.stderr)
        return 2
    if row.get("HELP_DATA_APPLY_EXECUTED") != "0" or row.get("CMDHELPCHK_APPLY_EXECUTED") != "0":
        print("[MSG-022AE.6.5.10CC] Refusing savepoint: apply executed unexpectedly", file=sys.stderr)
        return 2
    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10CC",
        "--lane", "MESSAGING",
        "--status", row["STATUS"],
        "--phase", "Phase 22AE.6.5.10CC target-specific native apply build plan review",
        "--summary", "10CC reviewed the native apply build plan and required a dedicated native HELP/CMDHELPCHK writer discovery package. No protected mutation occurred.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CD_NATIVE_HELP_CMDHELPCHK_WRITER_DISCOVERY_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10cc_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10cc_target_build_plan_review_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10cc_native_writer_family_review_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10cc_discovery_package_requirements_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10cc_boundary_ledger_v1.csv",
        "--messages", str(row.get("ACTIVE_MESSAGES_OBSERVED_COUNT", "14")),
        "--text-rows", str(row.get("ACTIVE_TEXT_OBSERVED_COUNT", "70")),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", str(row.get("VALIDATION_ISSUES", "0")),
        "--allowed-candidate-mutations", "docs/messaging target-specific native apply build-plan review artifacts and reports only",
        "--forbidden-active-mutations", "no source edits; no active DBF mutation; no CDX/LMDB mutation; no workspace mutation; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
