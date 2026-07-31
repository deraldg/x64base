#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_OK = {
    "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_GREEN_RUNTIME_KEYS_VISIBLE",
    "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_GREEN_RUNTIME_KEYS_NOT_VISIBLE_PATCH_REQUIRED",
}

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
        print("[MSG-022AE.6.5.8] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_8_validate_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status not in STATUS_OK:
        print(f"[MSG-022AE.6.5.8] Refusing savepoint: expected one of {sorted(STATUS_OK)}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.5.8",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.5.8 canonical runtime key probe",
        "--summary", "6.5.8 performed a read-only DotTalk++ runtime LIST ALL key visibility probe against the 6.5.6 sandbox DBFs to distinguish Python/v64 parsing limits from actual runtime field-map failure.",
        "--next-gate", row.get("NEXT_GATE", ""),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_5_8_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_8_runtime_message_key_hits_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_8_runtime_text_key_hits_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_8_runtime_key_result_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_5_8_validate_boundary_ledger_v1.csv",
        "--messages", row.get("MESSAGE_KEYS_FOUND_RUNTIME", ""),
        "--text-rows", row.get("TEXT_KEYS_FOUND_RUNTIME", ""),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; read-only runtime key probe",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
