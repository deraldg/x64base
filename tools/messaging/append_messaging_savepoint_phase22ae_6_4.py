#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, subprocess, sys
from pathlib import Path

STATUS_EXPECTED = "MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_GREEN_SOURCE_HELD"

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
        print("[MSG-022AE.6.4] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    row = first_row(repo / "docs/messaging/reports/message_catalog_phase22ae_6_4_status_summary_v1.csv")
    status = row.get("STATUS", "")
    if status != STATUS_EXPECTED:
        print(f"[MSG-022AE.6.4] Refusing savepoint: expected {STATUS_EXPECTED}, got {status}", file=sys.stderr)
        return 2

    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-022AE.6.4",
        "--lane", "MESSAGING",
        "--status", status,
        "--phase", "Phase 22AE.6.4 deep command surface write semantics review",
        "--summary", "Deep write-semantics review green: 6.3 remains no-variant-proven, active promotion stays closed, and next path is a single-variant forensic sandbox proof with active/index/lmdb boundary fingerprints.",
        "--next-gate", row.get("NEXT_GATE", "HOLD_OR_AUTHORIZE_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF"),
        "--source-reports", "docs/messaging/reports/message_catalog_phase22ae_6_4_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_enhanced_variant_readback_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_mismatch_review_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_hypothesis_matrix_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_1_next_probe_plan_v1.csv;docs/messaging/reports/message_catalog_phase22ae_6_4_boundary_ledger_v1.csv",
        "--messages", row.get("VARIANTS_REVIEWED", ""),
        "--text-rows", row.get("TWO_TABLE_VARIANTS_PROVEN_BY_ENHANCED_REVIEW", ""),
        "--locales", "en-US;es;fr;de;it",
        "--validation-issues", row.get("VALIDATION_ISSUES", "0"),
        "--allowed-candidate-mutations", "none; report/review only",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no active LMDB mutation; no source edits; no HELP DATA mutation; no CMDHELPCHK mutation",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
