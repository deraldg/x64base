from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT = "MSG-022AE.6.5.10CY-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CY_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_VALIDATION_GREEN_MAPPED_CANDIDATES_VALIDATED_APPLY_HELD"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def summary(repo: Path) -> dict:
    path = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10cy_b_status_summary_v1.csv"
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
        print("[MSG-022AE.6.5.10CY-B] Refusing without --accept-side-branch-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10CY-B] Status is not green: {status}")
        return 1

    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10CY-B] Side-branch savepoint already appears in journal; refusing duplicate append.")
        return 0

    entry = f"""
## {SAVEPOINT} — {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Output artifacts passed: {row.get('OUTPUT_ARTIFACTS_PASSED','')}/{row.get('OUTPUT_ARTIFACTS_TOTAL','')}
- Field checks passed: {row.get('FIELD_CHECKS_PASSED','')}/{row.get('FIELD_CHECKS_TOTAL','')}
- Row checks passed: {row.get('ROW_CHECKS_PASSED','')}/{row.get('ROW_CHECKS_TOTAL','')}
- Candidate mapping validated now: {row.get('CANDIDATE_MAPPING_VALIDATED_NOW','')}
- Apply ready: {row.get('APPLY_READY','')}
- HELP DATA apply executed: {row.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {row.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Latest pointer changed by CY-B: {row.get('LATEST_POINTER_CHANGED_BY_CY_B','')}
- Next gate: {row.get('NEXT_GATE','')}
"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10CY-B] Side-branch savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
