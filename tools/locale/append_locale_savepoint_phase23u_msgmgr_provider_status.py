#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from datetime import datetime, timezone
SID="LOC-023U-MSGMGR-PROVIDER-STATUS"
OK="LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS_BUILD_SMOKE_GREEN"
def rows(p):
    if not p.exists(): return []
    with p.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def first(p):
    r=rows(p); return r[0] if r else {}
def append_csv(p,row,fields):
    p.parent.mkdir(parents=True,exist_ok=True); exists=p.exists()
    with p.open("a",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
        if not exists: w.writeheader()
        w.writerow({k:row.get(k,"") for k in fields})
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",required=True); ap.add_argument("--accept-locale-savepoint",action="store_true"); ap.add_argument("--allow-duplicate-correction",action="store_true"); a=ap.parse_args()
    if not a.accept_locale_savepoint: print(f"[{SID}] Refusing without --accept-locale-savepoint"); return 2
    repo=Path(a.repo_root).resolve(); reports=repo/"docs/locale/reports"; s=first(reports/"locale_phase23u_msgmgr_provider_status_validation_summary_v1.csv"); status=s.get("STATUS","")
    if status!=OK: print(f"[{SID}] Refusing savepoint: expected {OK}, got {status}"); return 2
    idx=reports/"locale_savepoint_thread_index_v1.csv"; existing=[r for r in rows(idx) if r.get("savepoint_id")==SID]; same=[r for r in existing if r.get("status")==status]
    if same and not a.allow_duplicate_correction:
        print(f"[{SID}] ALREADY_SAVEPOINTED"); print(f"  existing rows: {len(existing)}"); print(f"  same-status rows: {len(same)}"); print("  no journal append performed"); return 0
    now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    sp={"timestamp_utc":now,"savepoint_id":SID,"lane":"LOCALE","status":status,"phase":"Phase 23U MSGMGR provider status","validation_issues":s.get("VALIDATION_ISSUES",""),"build_proof":s.get("BUILD_PROOF",""),"provider_mode_proof":s.get("PROVIDER_MODE_PROOF",""),"message_dbf_root_proof":s.get("MESSAGE_DBF_ROOT_PROOF",""),"message_index_root_proof":s.get("MESSAGE_INDEX_ROOT_PROOF",""),"message_lmdb_root_proof":s.get("MESSAGE_LMDB_ROOT_PROOF",""),"message_schema_active_path_proof":s.get("MESSAGE_SCHEMA_ACTIVE_PATH_PROOF",""),"next_gate":s.get("NEXT_GATE",""),"journal_anchor":SID,"source_reports":"docs/locale/LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS.md;docs/locale/reports/locale_phase23u_msgmgr_provider_status_validation_summary_v1.csv;docs/locale/runlog/LOC-023U_MSGMGR_PROVIDER_STATUS_BUILD_AND_SMOKE_PROOF.md","boundary_summary":"MSGMGR STATUS reports active DBF provider mode and Messaging DBF/CDX/LMDB roots; no active schema/DBF/CDX/LMDB/HELP/CMDHELPCHK/manualgen/Data Dictionary/SelfDoc mutation"}
    sp["entry_sha256"]=hashlib.sha256(json.dumps(sp,sort_keys=True,ensure_ascii=False).encode("utf-8")).hexdigest()
    journal=repo/"docs/locale/LOCALE_SAVEPOINT_JOURNAL.md"; journal.parent.mkdir(parents=True,exist_ok=True)
    with journal.open("a",encoding="utf-8",newline="\n") as f:
        f.write(f"\n## {SID} - {now}\n\nStatus: `{status}`\n\nPhase: Phase 23U MSGMGR provider status\n\nBoundary: status reporting only; no active catalog/protected mutation.\n\nEntry SHA256: `{sp['entry_sha256']}`\n")
    (reports/"locale_savepoint_latest_v1.json").write_text(json.dumps(sp,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    append_csv(idx,{"timestamp_utc":now,"savepoint_id":SID,"lane":"LOCALE","status":status},["timestamp_utc","savepoint_id","lane","status"])
    print(f"[{SID}] Locale savepoint appended."); print(f"  journal: {journal}"); print(f"  index: {idx}"); print(f"  latest: {reports/'locale_savepoint_latest_v1.json'}"); print(f"  entry_sha256: {sp['entry_sha256']}")
    return 0
if __name__=="__main__": raise SystemExit(main())
