#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_OK = {
    "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_GREEN_VARIANT_PROVEN",
    "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_GREEN_NO_VARIANT_PROVEN",
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
        print("[MSG-022AE.6.3] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_3_validate_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status not in STATUS_OK:
        print(f"[MSG-022AE.6.3] Refusing savepoint: expected one of {sorted(STATUS_OK)}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.3",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.3 alternative sandbox write proof",
        "--summary", "Alternative sandbox write proof completed across isolated sandbox clones. Active catalog was untouched. Results identify whether any write variant populated required keys or whether deeper command-surface write semantics review is required.",
        "--next-gate", row.get("NEXT_GATE", ""),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_3_validate_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_3_variant_results_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_3_tail_rows_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_3_runtime_observations_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_3_validate_boundary_ledger_v1.csv",
        "--messages", row.get("VARIANTS_TESTED", ""),
        "--text-rows", row.get("VARIANTS_WITH_COUNTS_MOVED", ""),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "sandbox variant copies under docs/messaging/sandbox only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
