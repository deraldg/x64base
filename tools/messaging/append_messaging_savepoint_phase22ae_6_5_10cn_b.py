#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT = "MSG-022AE.6.5.10CN-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CN_B_OPTION_B_REUSE_PROOF_DECISION_PACKAGE_GREEN_CAPTURE_ACCEPTED_REUSE_NOT_CONFIRMED_SOURCE_HELD"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def summary(repo: Path) -> dict:
    p = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10cn_b_status_summary_v1.csv"
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
        print("[MSG-022AE.6.5.10CN-B] Refusing without --accept-side-branch-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10CN-B] Status is not green: {status}")
        return 1

    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10CN-B] Side-branch savepoint already appears in journal; refusing duplicate append.")
        return 0

    entry = f"""
## {SAVEPOINT} -- {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Official latest before CN-B: {s.get('OFFICIAL_LATEST_SAVEPOINT_BEFORE_CN_B','')}
- Candidate output capture accepted: {s.get('CANDIDATE_OUTPUT_CAPTURE_ACCEPTED','')}
- Selected decision: {s.get('SELECTED_DECISION','')}
- Reuse path selected now: {s.get('REUSE_PATH_SELECTED_NOW','')}
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
- Latest pointer changed by CN-B: {s.get('LATEST_POINTER_CHANGED_BY_CN_B','')}
- Targeted invocation proof required: {s.get('TARGETED_INVOCATION_PROOF_REQUIRED','')}
- Next gate: {s.get('NEXT_GATE','')}

Note: CN-B is a side-branch decision savepoint. It does not move message_savepoint_latest_v1.json.
"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10CN-B] Side-branch savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
