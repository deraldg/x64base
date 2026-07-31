#!/usr/bin/env python3
"""Convenience wrapper for the green Phase 9 Messaging checkpoint."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def main() -> int:
    script = Path(__file__).with_name("append_messaging_savepoint.py")
    args = sys.argv[1:]
    if "--repo-root" not in args:
        raise SystemExit("Usage: append_messaging_savepoint_phase9.py --repo-root <repo> --accept-messaging-savepoint")
    cmd = [
        sys.executable,
        str(script),
        "--savepoint-id", "MSG-009",
        "--status", "MESSAGING-PHASE9-INACTIVE-CANDIDATE-STAGING-GREEN",
        "--phase", "Phase 9 inactive candidate DBF staging artifacts",
        "--summary", "Inactive candidate message catalog staging completed with 12 messages, 60 text rows, five locales, zero validation issues, and zero DBF/CDX/LMDB/active catalog promotion mutation.",
        "--next-gate", "HOLD_OR_AUTHORIZE_PHASE10_CANDIDATE_DBF_EXECUTION_PLAN",
        "--source-report", "docs/messaging/reports/message_catalog_phase9_status_summary_v1.csv",
        "--source-report", "docs/messaging/reports/message_catalog_phase9_candidate_artifact_inventory_v1.csv",
        "--source-report", "docs/messaging/reports/message_catalog_phase9_gate_check_v1.csv",
        "--source-report", "docs/messaging/reports/message_catalog_phase9_boundary_ledger_v1.csv",
    ] + args
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
