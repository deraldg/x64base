#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path
SAVEPOINT="MSG-022AE.6.5.10CT-B"
GREEN="MESSAGE_CATALOG_PHASE22AE_6_5_10CT_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_STAGING_GREEN_DTS_AND_CSV_STAGED_SOURCE_HELD"
def rt(p): return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
def wt(p,s): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8", newline="\n")
def summary(repo):
    p=repo/"docs/messaging/reports/message_catalog_phase22ae_6_5_10ct_b_status_summary_v1.csv"
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            r=list(csv.DictReader(f)); return r[0] if r else {}
    except Exception: return {}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root", required=True); ap.add_argument("--accept-side-branch-savepoint", action="store_true"); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); s=summary(repo); status=s.get("STATUS","")
    if not a.accept_side_branch_savepoint: print("[MSG-022AE.6.5.10CT-B] Refusing without --accept-side-branch-savepoint."); return 1
    if status != GREEN: print(f"[MSG-022AE.6.5.10CT-B] Status is not green: {status}"); return 1
    journal=repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"; old=rt(journal)
    if SAVEPOINT in old: print("[MSG-022AE.6.5.10CT-B] Side-branch savepoint already appears in journal; refusing duplicate append."); return 0
    entry=f"""
## {SAVEPOINT} — {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Corrected concept: {s.get('CORRECTED_CONCEPT','')}
- Official latest before CT-B: {s.get('OFFICIAL_LATEST_SAVEPOINT_BEFORE_CT_B','')}
- Candidate tables: {s.get('CANDIDATE_TABLES','')}
- Candidate input rows: {s.get('CANDIDATE_INPUT_ROWS','')}
- DTS executed by package: {s.get('DTS_EXECUTED_BY_PACKAGE','')}
- DBF created by package: {s.get('DBF_CREATED_BY_PACKAGE','')}
- CDX/LMDB created by package: {s.get('CDX_LMDB_CREATED_BY_PACKAGE','')}
- Native table materialization confirmed now: {s.get('NATIVE_TABLE_MATERIALIZATION_CONFIRMED_NOW','')}
- HELP DATA apply executed: {s.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {s.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Latest pointer changed by CT-B: {s.get('LATEST_POINTER_CHANGED_BY_CT_B','')}
- Next gate: {s.get('NEXT_GATE','')}

Note: CT-B is a side-branch staging savepoint. It does not move message_savepoint_latest_v1.json.
"""
    wt(journal, old.rstrip()+"\n\n"+entry.lstrip())
    print("[MSG-022AE.6.5.10CT-B] Side-branch savepoint appended."); print(f"  journal: {journal}"); print("  latest pointer changed: 0"); return 0
if __name__=="__main__": raise SystemExit(main())
