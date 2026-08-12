#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT = "MSG-022AE.6.5.10CJ-OPTIONB-RECON"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CJ_OPTION_B_BRANCH_RECONCILIATION_GREEN_REPORT_ONLY_BRANCH_COLLISION_DOCUMENTED"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def read_summary(repo: Path) -> dict:
    p = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10cj_option_b_reconciliation_status_summary_v1.csv"
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[0] if rows else {}
    except Exception:
        return {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-reconciliation-savepoint", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    summary = read_summary(repo)
    status = summary.get("STATUS","")

    if not args.accept_reconciliation_savepoint:
        print("[MSG-022AE.6.5.10CJ-OPTIONB-RECON] Refusing without --accept-reconciliation-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10CJ-OPTIONB-RECON] Status is not green: {status}")
        return 1

    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10CJ-OPTIONB-RECON] Reconciliation savepoint already appears in journal; refusing duplicate append.")
        return 0

    entry = f"""
## {SAVEPOINT} -- {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Current CJ status: {summary.get('CURRENT_CJ_STATUS','')}
- Current selected option: {summary.get('CURRENT_SELECTED_OPTION','')}
- Existing CJ targeted-discovery savepoint present: {summary.get('OLDER_CJ_TARGETED_DISCOVERY_SAVEPOINT_PRESENT','')}
- CK present in journal: {summary.get('CK_PRESENT_IN_JOURNAL','')}
- CL present/latest: {summary.get('CL_PRESENT_OR_LATEST','')}
- Latest savepoint before reconciliation: {summary.get('LATEST_SAVEPOINT','')}
- Branch collision detected: {summary.get('BRANCH_COLLISION_DETECTED','')}
- Journal append executed by reconciliation run: {summary.get('JOURNAL_APPEND_EXECUTED_BY_RUN','')}
- Latest pointer changed by reconciliation: {summary.get('LATEST_POINTER_CHANGED_BY_RUN','')}
- Source files mutated: {summary.get('SOURCE_FILES_MUTATED','')}
- HELP DATA apply executed: {summary.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {summary.get('CMDHELPCHK_APPLY_EXECUTED','')}
- DBF mutation observed: {summary.get('DBF_MUTATION_OBSERVED','')}
- CDX/LMDB mutation observed: {summary.get('CDX_LMDB_MUTATION_OBSERVED','')}
- Workspace mutation observed: {summary.get('WORKSPACE_MUTATION_OBSERVED','')}
- Next gate: {summary.get('NEXT_GATE','')}

Note: this reconciliation savepoint is an addendum. It does not move message_savepoint_latest_v1.json and does not supersede the existing CL latest pointer.
"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10CJ-OPTIONB-RECON] Reconciliation savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
