#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from pathlib import Path
from datetime import datetime, timezone
OK="LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS_BUILD_SMOKE_GREEN"
BAD="LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS_BUILD_SMOKE_BLOCKED"
NEXT="HOLD_OR_AUTHORIZE_PHASE23_CLOSEOUT_OR_MAINT_HANDOFF"
RUNLOG=Path("docs/locale/runlog/LOC-023U_MSGMGR_PROVIDER_STATUS_BUILD_AND_SMOKE_PROOF.md")
def rows(p):
    if not p.exists(): return []
    with p.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def first(p):
    r=rows(p); return r[0] if r else {}
def write_csv(p, data, fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        for r in data: w.writerow({k:r.get(k,"") for k in fields})
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",required=True); a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); reports=repo/"docs/locale/reports"; reports.mkdir(parents=True,exist_ok=True)
    app=first(reports/"locale_phase23u_msgmgr_provider_status_apply_summary_v1.csv")
    text=(repo/RUNLOG).read_text(encoding="utf-8",errors="replace") if (repo/RUNLOG).exists() else ""
    u=text.upper(); gates=[]; failures=0
    def gate(n,ok,d):
        nonlocal failures
        gates.append({"GATE":n,"STATUS":"PASS" if ok else "FAIL","DETAIL":d})
        if not ok: failures += 1
    gate("PHASE23U_APPLY_GREEN", app.get("STATUS")=="LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS_SOURCE_PATCH_APPLIED_BUILD_HELD", app.get("STATUS",""))
    gate("RUNLOG_PRESENT",(repo/RUNLOG).exists(),str(RUNLOG))
    gate("BUILD_SUCCESS_PROOF","DOTTALKPP.VCXPROJ ->" in u or "BUILD SUCCEEDED" in u or "BUILT TARGET DOTTALKPP" in u,"build proof")
    gate("MSGMGR_STATUS_PROOF","MSGMGR STATUS" in u and "COMMAND HOUSE" in u and "REGISTERED" in u,"status proof")
    gate("PROVIDER_MODE_PROOF","PROVIDER MODE" in u and "ACTIVE_DBF" in u,"provider mode")
    gate("MESSAGE_DBF_ROOT_PROOF","MESSAGE DBF ROOT" in u and "DOTTALKPP/DATA/MESSAGING" in u,"dbf root")
    gate("MESSAGE_INDEX_ROOT_PROOF","MESSAGE INDEX ROOT" in u and "DOTTALKPP/DATA/INDEXES/MESSAGING" in u,"index root")
    gate("MESSAGE_LMDB_ROOT_PROOF","MESSAGE LMDB ROOT" in u and "DOTTALKPP/DATA/LMDB/MESSAGING" in u,"lmdb root")
    gate("MESSAGE_SCHEMA_ACTIVE_PATH_PROOF","MESSAGING SCHEMA" in u and "DOTTALKPP/DATA/SCHEMAS/MESSAGING/MESSAGE_CATALOG.DTSCHEMA" in u,"schema path")
    gate("READ_ONLY_BOUNDARY_PROOF","NO DBF/CDX/LMDB MUTATION" in u or "NO DBF" in u,"boundary")
    status=OK if failures==0 else BAD
    vals={"STATUS":status,"VALIDATION_ISSUES":failures,"BUILD_PROOF":1 if ("DOTTALKPP.VCXPROJ ->" in u or "BUILD SUCCEEDED" in u or "BUILT TARGET DOTTALKPP" in u) else 0,"MSGMGR_STATUS_PROOF":1 if ("MSGMGR STATUS" in u and "COMMAND HOUSE" in u and "REGISTERED" in u) else 0,"PROVIDER_MODE_PROOF":1 if ("PROVIDER MODE" in u and "ACTIVE_DBF" in u) else 0,"MESSAGE_DBF_ROOT_PROOF":1 if ("MESSAGE DBF ROOT" in u and "DOTTALKPP/DATA/MESSAGING" in u) else 0,"MESSAGE_INDEX_ROOT_PROOF":1 if ("MESSAGE INDEX ROOT" in u and "DOTTALKPP/DATA/INDEXES/MESSAGING" in u) else 0,"MESSAGE_LMDB_ROOT_PROOF":1 if ("MESSAGE LMDB ROOT" in u and "DOTTALKPP/DATA/LMDB/MESSAGING" in u) else 0,"MESSAGE_SCHEMA_ACTIVE_PATH_PROOF":1 if ("MESSAGING SCHEMA" in u and "DOTTALKPP/DATA/SCHEMAS/MESSAGING/MESSAGE_CATALOG.DTSCHEMA" in u) else 0,"NEXT_GATE":NEXT,"REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")}
    write_csv(reports/"locale_phase23u_msgmgr_provider_status_validation_summary_v1.csv",[vals],list(vals.keys()))
    write_csv(reports/"locale_phase23u_msgmgr_provider_status_validation_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    print(status); print(f"  validation issues: {failures}")
    for key in ["BUILD_PROOF","MSGMGR_STATUS_PROOF","PROVIDER_MODE_PROOF","MESSAGE_DBF_ROOT_PROOF","MESSAGE_INDEX_ROOT_PROOF","MESSAGE_LMDB_ROOT_PROOF","MESSAGE_SCHEMA_ACTIVE_PATH_PROOF"]:
        print(f"  {key.lower().replace('_',' ')}: {vals[key]}")
    print(f"  next gate: {NEXT}"); print(f"  reports: {reports}")
    return 0 if status==OK else 2
if __name__=="__main__": raise SystemExit(main())
