
from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path
SAVEPOINT = "MSG-022AE.6.5.10DJ-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DJ_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_STAGING_GREEN_MANUAL_READ_ONLY_PROBES_STAGED_NO_EXECUTION"
def txt(p: Path) -> str: return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
def out(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8", newline="\n")
def one(repo: Path) -> dict:
    p = repo / "docs/messaging/reports/message_catalog_phase22ae_6_5_10dj_b_status_summary_v1.csv"
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[0] if rows else {}
    except Exception: return {}
def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo-root", required=True); ap.add_argument("--accept-side-branch-savepoint", action="store_true"); a = ap.parse_args()
    repo = Path(a.repo_root).resolve(); row = one(repo); status = row.get("STATUS","")
    if not a.accept_side_branch_savepoint:
        print("[MSG-022AE.6.5.10DJ-B] Refusing without --accept-side-branch-savepoint."); return 1
    if status != GREEN:
        print(f"[MSG-022AE.6.5.10DJ-B] Status is not green: {status}"); return 1
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"; old = txt(journal)
    if SAVEPOINT in old:
        print("[MSG-022AE.6.5.10DJ-B] Side-branch savepoint already appears in journal; refusing duplicate append."); return 0
    entry = f"""
## {SAVEPOINT} — {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Target verification probe staging created: {row.get('TARGET_VERIFICATION_PROBE_STAGING_CREATED','')}
- Read-only probe script staged: {row.get('READ_ONLY_PROBE_SCRIPT_STAGED','')}
- Probe script rows: {row.get('PROBE_SCRIPT_ROWS','')}
- Probe executed by DJ-B package: {row.get('PROBE_EXECUTED_BY_DJ_B_PACKAGE','')}
- Active HELP DATA target selected now: {row.get('ACTIVE_HELP_DATA_TARGET_SELECTED_NOW','')}
- Active CMDHELPCHK target selected now: {row.get('ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW','')}
- Apply execution authorized now: {row.get('APPLY_EXECUTION_AUTHORIZED_NOW','')}
- HELP DATA apply executed: {row.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {row.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Latest pointer changed by DJ-B: {row.get('LATEST_POINTER_CHANGED_BY_DJ_B','')}
- Next gate: {row.get('NEXT_GATE','')}
"""
    out(journal, old.rstrip() + "\n\n" + entry.lstrip())
    print("[MSG-022AE.6.5.10DJ-B] Side-branch savepoint appended.")
    print(f"  journal: {journal}")
    print("  latest pointer changed: 0")
    return 0
if __name__ == "__main__": raise SystemExit(main())
