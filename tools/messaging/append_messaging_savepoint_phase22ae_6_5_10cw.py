#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_NATIVE_WRITER_NEXT_INVESTIGATION_SCOPE_REVIEW_GREEN_PROBE_STAGING_PACKAGE_REQUIRED_SOURCE_HELD"

def first(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        r = list(csv.DictReader(f))
    return r[0] if r else {}

def journal_has(repo: Path, sid: str) -> bool:
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    return journal.exists() and sid in journal.read_text(encoding="utf-8", errors="replace")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()
    if not args.accept_messaging_savepoint:
        print("[MSG-022AE.6.5.10CW] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2
    repo = Path(args.repo_root).resolve()
    if journal_has(repo, "MSG-022AE.6.5.10CW"):
        print("[MSG-022AE.6.5.10CW] Savepoint already appears in journal; refusing duplicate append.")
        return 0
    row = first(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10cw_status_summary_v1.csv")
    if row.get("STATUS") != GREEN:
        print(f"[MSG-022AE.6.5.10CW] Refusing savepoint: got {row.get('STATUS','')}", file=sys.stderr)
        return 2
    if row.get("HELP_DATA_APPLY_EXECUTED") != "0" or row.get("CMDHELPCHK_APPLY_EXECUTED") != "0":
        print("[MSG-022AE.6.5.10CW] Refusing savepoint: apply executed unexpectedly", file=sys.stderr)
        return 2
    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10CW",
        "--lane", "MESSAGING",
        "--status", row["STATUS"],
        "--phase", "Phase 22AE.6.5.10CW native writer next investigation scope review",
        "--summary", "10CW reviewed the 10CV next investigation scope and required a 10CX probe staging package. No runtime probes, source edits, HELP DATA/CMDHELPCHK apply, or protected mutation occurred.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CX_NATIVE_WRITER_PROBE_STAGING_PACKAGE"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10cw_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10cw_scope_review_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10cw_probe_plan_review_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10cw_probe_staging_requirements_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10cw_boundary_ledger_v1.csv",
        "--messages", str(row.get("ACTIVE_MESSAGES_OBSERVED_COUNT", "14")),
        "--text-rows", str(row.get("ACTIVE_TEXT_OBSERVED_COUNT", "70")),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", str(row.get("VALIDATION_ISSUES", "0")),
        "--allowed-candidate-mutations", "docs/messaging native writer next investigation scope review artifacts and reports only",
        "--forbidden-active-mutations", "no runtime execution; no source edits; no active DBF mutation; no CDX/LMDB mutation; no workspace mutation; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
