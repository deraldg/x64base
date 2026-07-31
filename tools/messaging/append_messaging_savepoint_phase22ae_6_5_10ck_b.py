#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT = "MSG-022AE.6.5.10CK-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CK_B_OPTION_B_NATIVE_WRITER_WRAPPER_CONTRACT_PROOF_PLAN_GREEN_SIDE_BRANCH_SOURCE_HELD"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def summary(repo: Path) -> dict:
    p = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ck_b_status_summary_v1.csv"
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
        print("[MSG-022AE.6.5.10CK-B] Refusing without --accept-side-branch-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10CK-B] Status is not green: {status}")
        return 1

    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10CK-B] Side-branch savepoint already appears in journal; refusing duplicate append.")
        return 0

    entry = f"""
## {SAVEPOINT} — {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Side branch: {s.get('SELECTED_BRANCH','')}
- Official latest before CK-B: {s.get('OFFICIAL_LATEST_SAVEPOINT_BEFORE_CK_B','')}
- Reconciliation savepoint present: {s.get('RECONCILIATION_SAVEPOINT_PRESENT','')}
- Wrapper/contract requirement rows: {s.get('WRAPPER_CONTRACT_REQUIREMENT_ROWS','')}
- Proof plan rows: {s.get('PROOF_PLAN_ROWS','')}
- Refusal guard rows: {s.get('REFUSAL_GUARD_ROWS','')}
- Reuse path selected now: {s.get('REUSE_PATH_SELECTED_NOW','')}
- Reuse path confirmed now: {s.get('REUSE_PATH_CONFIRMED_NOW','')}
- Wrapper proof executed now: {s.get('WRAPPER_PROOF_EXECUTED_NOW','')}
- Source mutation authorized now: {s.get('SOURCE_MUTATION_AUTHORIZED_NOW','')}
- Apply execution authorized now: {s.get('APPLY_EXECUTION_AUTHORIZED_NOW','')}
- HELP DATA apply executed: {s.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {s.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Source files mutated: {s.get('SOURCE_FILES_MUTATED','')}
- Active catalog mutation observed: {s.get('ACTIVE_CATALOG_MUTATION_OBSERVED','')}
- Latest pointer changed by CK-B: {s.get('LATEST_POINTER_CHANGED_BY_CK_B','')}
- Next gate: {s.get('NEXT_GATE','')}

Note: CK-B is a side-branch savepoint. It does not move message_savepoint_latest_v1.json.
"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10CK-B] Side-branch savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
