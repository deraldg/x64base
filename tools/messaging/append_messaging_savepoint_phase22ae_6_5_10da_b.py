from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

SAVEPOINT = "MSG-022AE.6.5.10DA-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_PROOF_REVIEW_GREEN_DBF_CDX_LMDB_READBACK_PROVEN_APPLY_HELD"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def summary(repo: Path) -> dict:
    path = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10da_b_status_summary_v1.csv"
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
        print("[MSG-022AE.6.5.10DA-B] Refusing without --accept-side-branch-savepoint.")
        return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10DA-B] Status is not green: {status}")
        return 1

    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    old = read_text(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10DA-B] Side-branch savepoint already appears in journal; refusing duplicate append.")
        return 0

    entry = f"""
## {SAVEPOINT} — {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- CZ-B status green: {row.get('CZ_B_STATUS_GREEN','')}
- CZ-B savepoint present: {row.get('CZ_B_SAVEPOINT_PRESENT','')}
- Tables passed: {row.get('TABLES_PASSED','')}/{row.get('TABLES_TOTAL','')}
- Tags passed: {row.get('TAGS_PASSED','')}/{row.get('TAGS_TOTAL','')}
- Artifacts observed: {row.get('ARTIFACTS_OBSERVED','')}/{row.get('ARTIFACTS_TOTAL','')}
- HELP/CMDHELPCHK candidate native materialization proven: {row.get('HELP_CMDHELPCHK_CANDIDATE_NATIVE_MATERIALIZATION_PROVEN','')}
- Apply ready: {row.get('APPLY_READY','')}
- HELP DATA apply executed: {row.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {row.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Latest pointer changed by DA-B: {row.get('LATEST_POINTER_CHANGED_BY_DA_B','')}
- Next gate: {row.get('NEXT_GATE','')}
"""
    write_text(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10DA-B] Side-branch savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
