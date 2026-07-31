#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DD_NATIVE_WRITER_EXACT_PATH_RESOLUTION_PACKAGE_GREEN_EXACT_SOURCE_LOCATIONS_STAGED_SOURCE_HELD"

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
        print("[MSG-022AE.6.5.10DD] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2
    repo = Path(args.repo_root).resolve()
    if journal_has(repo, "MSG-022AE.6.5.10DD"):
        print("[MSG-022AE.6.5.10DD] Savepoint already appears in journal; refusing duplicate append.")
        return 0
    row = first(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10dd_status_summary_v1.csv")
    if row.get("STATUS") != GREEN:
        print(f"[MSG-022AE.6.5.10DD] Refusing savepoint: got {row.get('STATUS','')}", file=sys.stderr)
        return 2
    if row.get("HELP_DATA_APPLY_EXECUTED") != "0" or row.get("CMDHELPCHK_APPLY_EXECUTED") != "0":
        print("[MSG-022AE.6.5.10DD] Refusing savepoint: apply executed unexpectedly", file=sys.stderr)
        return 2
    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.10DD",
        "--lane", "MESSAGING",
        "--status", row["STATUS"],
        "--phase", "Phase 22AE.6.5.10DD native writer exact path resolution package",
        "--summary", "10DD staged exact source locations/function contexts for high-value 10DC candidates. No reuse was confirmed, no source patch need was proven, no apply was authorized, and no protected mutation occurred.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DE_NATIVE_WRITER_EXACT_PATH_RESOLUTION_REVIEW"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_10dd_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10dd_exact_path_resolution_rows_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10dd_target_resolution_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_10dd_boundary_ledger_v1.csv",
        "--messages", str(row.get("ACTIVE_MESSAGES_OBSERVED_COUNT", "14")),
        "--text-rows", str(row.get("ACTIVE_TEXT_OBSERVED_COUNT", "70")),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", str(row.get("VALIDATION_ISSUES", "0")),
        "--allowed-candidate-mutations", "docs/messaging exact path resolution artifacts and reports only",
        "--forbidden-active-mutations", "no DotTalk runtime execution; no source edits; no active DBF mutation; no CDX/LMDB mutation; no workspace mutation; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
