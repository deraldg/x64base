#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT = "MSG-022AE.6.5.10CS-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN_GREEN_REPORT_ONLY_SOURCE_HELD"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def summary(repo: Path) -> dict:
    p = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10cs_b_status_summary_v1.csv"
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[0] if rows else {}
    except Exception:
        return {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-side-branch-savepoint", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    s = summary(repo)
    status = s.get("STATUS","")
    if not args.accept_side_branch_savepoint:
        print("[MSG-022AE.6.5.10CS-B] Refusing without --accept-side-branch-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10CS-B] Status is not green: {status}")
        return 1

    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10CS-B] Side-branch savepoint already appears in journal; refusing duplicate append.")
        return 0

    entry = f"""
## {SAVEPOINT} -- {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Official latest before CS-B: {s.get('OFFICIAL_LATEST_SAVEPOINT_BEFORE_CS_B','')}
- Active candidate invocation plan required: {s.get('ACTIVE_CANDIDATE_INVOCATION_PLAN_REQUIRED','')}
- Chosen surface rows: {s.get('CHOSEN_SURFACE_ROWS','')}
- Invocation plan rows: {s.get('INVOCATION_PLAN_ROWS','')}
- Refusal guard rows: {s.get('REFUSAL_GUARD_ROWS','')}
- Active candidate invocation planned: {s.get('ACTIVE_CANDIDATE_INVOCATION_PLANNED','')}
- Active candidate invocation executed by CS-B: {s.get('ACTIVE_CANDIDATE_INVOCATION_EXECUTED_BY_CS_B','')}
- Reuse path confirmed now: {s.get('REUSE_PATH_CONFIRMED_NOW','')}
- Source patch needed proven: {s.get('SOURCE_PATCH_NEEDED_PROVEN','')}
- Source mutation authorized now: {s.get('SOURCE_MUTATION_AUTHORIZED_NOW','')}
- Apply execution authorized now: {s.get('APPLY_EXECUTION_AUTHORIZED_NOW','')}
- HELP DATA apply executed: {s.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {s.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Active catalog mutation observed: {s.get('ACTIVE_CATALOG_MUTATION_OBSERVED','')}
- DBF mutation observed: {s.get('DBF_MUTATION_OBSERVED','')}
- CDX/LMDB mutation observed: {s.get('CDX_LMDB_MUTATION_OBSERVED','')}
- Workspace mutation observed: {s.get('WORKSPACE_MUTATION_OBSERVED','')}
- Latest pointer changed by CS-B: {s.get('LATEST_POINTER_CHANGED_BY_CS_B','')}
- Next gate: {s.get('NEXT_GATE','')}

Note: CS-B is a side-branch plan savepoint. It does not move message_savepoint_latest_v1.json.
"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10CS-B] Side-branch savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
