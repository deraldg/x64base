#!/usr/bin/env python3
"""
Append MSG-014B boundary correction after Phase 14.

This does not rewrite MSG-014. It appends a corrective savepoint that clarifies
that inactive candidate CDX creation was allowed and observed, while active
catalog mutations remained forbidden.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-messaging-savepoint", action="store_true")
    args = ap.parse_args()

    if not args.accept_messaging_savepoint:
        print("[MSG-014B] Refusing without --accept-messaging-savepoint", file=sys.stderr)
        return 2

    repo = Path(args.repo_root).resolve()
    generic = repo / "tools/messaging/append_messaging_savepoint.py"
    if not generic.exists():
        print(f"[MSG-014B] Missing generic savepoint tool: {generic}", file=sys.stderr)
        return 2

    cmd = [
        sys.executable, str(generic),
        "--repo-root", str(repo),
        "--savepoint-id", "MSG-014B",
        "--lane", "MESSAGING",
        "--status", "MESSAGE_CATALOG_PHASE14_BOUNDARY_CORRECTION_RECORDED",
        "--phase", "Phase 14 boundary wording correction",
        "--summary", "Corrects the MSG-014 boundary wording. Phase 14 intentionally created inactive candidate CDX files; no active catalog mutation or promotion occurred.",
        "--messages", "12",
        "--text-rows", "60",
        "--locales", "de;en-US;es;fr;it",
        "--validation-issues", "0",
        "--next-gate", "HOLD_OR_AUTHORIZE_PHASE15_CANDIDATE_LMDB_PLAN_OR_RUNTIME_CDX_READBACK",
        "--source-reports", "docs/messaging/reports/message_catalog_phase14_status_summary_v1.csv;docs/messaging/reports/message_catalog_phase14_boundary_ledger_v1.csv",
        "--allowed-candidate-mutations", "inactive candidate CDX files created under docs/messaging/candidates/phase14_inactive_candidate_cdx_execution/indexes; candidate DBF/DBT copies under the same inactive candidate workspace",
        "--forbidden-active-mutations", "no active DBF/catalog mutation; no active CDX/index mutation; no LMDB creation; no HELP DATA mutation; no CMDHELPCHK mutation; no source-mining mutation; no source edits; no active catalog promotion",
        "--accept-messaging-savepoint",
    ]
    return subprocess.call(cmd)

if __name__ == "__main__":
    raise SystemExit(main())
