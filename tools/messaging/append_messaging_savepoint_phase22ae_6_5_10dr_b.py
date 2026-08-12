from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT = "MSG-022AE.6.5.10DR-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DR_B_SOURCE_LOCALE_HELP_ONLY_DRY_RUN_ELIGIBILITY_PLAN_GREEN_SCOPE_NARROWED_DRY_RUN_STILL_HELD"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def summary(repo: Path) -> dict:
    path = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10dr_b_status_summary_v1.csv"
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[0] if rows else {}
    except Exception:
        return {}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--accept-side-branch-savepoint", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    row = summary(repo)
    status = row.get("STATUS", "")
    if not args.accept_side_branch_savepoint:
        print("[MSG-022AE.6.5.10DR-B] Refusing without --accept-side-branch-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10DR-B] Status is not green: {status}")
        return 1
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10DR-B] Side-branch savepoint already appears in journal; refusing duplicate append.")
        return 0
    entry = f"""
## {SAVEPOINT} -- {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Source-locale HELP-only eligibility plan created: {row.get('SOURCE_LOCALE_HELP_ONLY_ELIGIBILITY_PLAN_CREATED','')}
- HELP candidate rows: {row.get('HELP_CANDIDATE_ROWS','')}
- Source-locale HELP rows: {row.get('SOURCE_LOCALE_HELP_ROWS','')}
- Localized HELP rows held: {row.get('LOCALIZED_HELP_ROWS_HELD','')}
- Source-locale HELP scope eligible for next policy plan: {row.get('SOURCE_LOCALE_HELP_SCOPE_ELIGIBLE_FOR_NEXT_POLICY_PLAN','')}
- Source-locale HELP dry-run authorized now: {row.get('SOURCE_LOCALE_HELP_DRY_RUN_AUTHORIZED_NOW','')}
- Dry-run authorized now: {row.get('DRY_RUN_AUTHORIZED_NOW','')}
- Apply execution authorized now: {row.get('APPLY_EXECUTION_AUTHORIZED_NOW','')}
- HELP DATA apply executed: {row.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {row.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Latest pointer changed by DR-B: {row.get('LATEST_POINTER_CHANGED_BY_DR_B','')}
- Next gate: {row.get('NEXT_GATE','')}
"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10DR-B] Side-branch savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
