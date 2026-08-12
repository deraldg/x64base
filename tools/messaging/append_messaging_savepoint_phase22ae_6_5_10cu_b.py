from __future__ import annotations
import argparse,csv
from datetime import datetime, timezone
from pathlib import Path
SAVEPOINT="MSG-022AE.6.5.10CU-B"
GREEN="MESSAGE_CATALOG_PHASE22AE_6_5_10CU_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_PROOF_REVIEW_GREEN_DBF_CDX_LMDB_READBACK_PROVEN"
def rt(p): return p.read_text(encoding="utf-8",errors="replace") if p.exists() else ""
def wt(p,s): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding="utf-8",newline="\n")
def summary(repo):
    p=repo/"docs/messaging/reports/message_catalog_phase22ae_6_5_10cu_b_status_summary_v1.csv"
    try:
        with p.open("r",encoding="utf-8-sig",newline="") as f:
            r=list(csv.DictReader(f)); return r[0] if r else {}
    except Exception: return {}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",required=True); ap.add_argument("--accept-side-branch-savepoint",action="store_true"); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); s=summary(repo); status=s.get("STATUS","")
    if not a.accept_side_branch_savepoint: print("[MSG-022AE.6.5.10CU-B] Refusing without --accept-side-branch-savepoint."); return 1
    if status!=GREEN: print(f"[MSG-022AE.6.5.10CU-B] Status is not green: {status}"); return 1
    journal=repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"; old=rt(journal)
    if SAVEPOINT in old: print("[MSG-022AE.6.5.10CU-B] Side-branch savepoint already appears in journal; refusing duplicate append."); return 0
    entry=f"""
## {SAVEPOINT} -- {status}

- Timestamp UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')}
- Corrected concept: {s.get('CORRECTED_CONCEPT','')}
- CT-B status green: {s.get('CT_B_STATUS_GREEN','')}
- CT-B savepoint present: {s.get('CT_B_SAVEPOINT_PRESENT','')}
- Tables passed: {s.get('TABLES_PASSED','')}/{s.get('TABLES_TOTAL','')}
- Tags passed: {s.get('TAGS_PASSED','')}/{s.get('TAGS_TOTAL','')}
- Artifacts observed: {s.get('ARTIFACTS_OBSERVED','')}/{s.get('ARTIFACTS_TOTAL','')}
- Native table materialization confirmed now: {s.get('NATIVE_TABLE_MATERIALIZATION_CONFIRMED_NOW','')}
- Reuse path confirmed now: {s.get('REUSE_PATH_CONFIRMED_NOW','')}
- HELP DATA apply executed: {s.get('HELP_DATA_APPLY_EXECUTED','')}
- CMDHELPCHK apply executed: {s.get('CMDHELPCHK_APPLY_EXECUTED','')}
- Latest pointer changed by CU-B: {s.get('LATEST_POINTER_CHANGED_BY_CU_B','')}
- Next gate: {s.get('NEXT_GATE','')}
"""
    wt(journal,old.rstrip()+"\n\n"+entry.lstrip())
    print("[MSG-022AE.6.5.10CU-B] Side-branch savepoint appended."); print(f"  journal: {journal}"); print("  latest pointer changed: 0"); return 0
if __name__=="__main__": raise SystemExit(main())
