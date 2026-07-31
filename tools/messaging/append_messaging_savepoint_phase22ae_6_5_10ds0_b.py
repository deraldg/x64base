from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT = "MSG-022AE.6.5.10DS0-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DS0_B_TOOLING_BOUNDARY_HELP_APPLY_INTENT_CLARIFICATION_GREEN_NO_ACTIVE_APPLY_NO_TOOL_PROMOTION"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def summary(repo: Path) -> dict:
    path = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10ds0_b_status_summary_v1.csv"
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
        print("[MSG-022AE.6.5.10DS0-B] Refusing without --accept-side-branch-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10DS0-B] Status is not green: {status}")
        return 1
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10DS0-B] Side-branch savepoint already appears in journal; refusing duplicate append.")
        return 0
    entry = f"""
## {SAVEPOINT} — {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Intent clarified: {row.get('INTENT_CLARIFIED','')}
- Active HELP infusion authorized now: {row.get('ACTIVE_HELP_INFUSION_AUTHORIZED_NOW','')}
- Active DBF/CDX/LMDB write authorized now: {row.get('ACTIVE_DBF_CDX_LMDB_WRITE_AUTHORIZED_NOW','')}
- C++ source edit authorized now: {row.get('CXX_SOURCE_EDIT_AUTHORIZED_NOW','')}
- Permanent Python/tool promotion authorized now: {row.get('PERMANENT_PYTHON_TOOL_PROMOTION_AUTHORIZED_NOW','')}
- DS-B allowed as policy-only next: {row.get('DS_B_ALLOWED_AS_POLICY_ONLY_NEXT','')}
- Dry-run authorized now: {row.get('DRY_RUN_AUTHORIZED_NOW','')}
- Apply execution authorized now: {row.get('APPLY_EXECUTION_AUTHORIZED_NOW','')}
- Latest pointer changed by DS0-B: {row.get('LATEST_POINTER_CHANGED_BY_DS0_B','')}
- Next gate: {row.get('NEXT_GATE','')}
"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10DS0-B] Side-branch savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
