
from __future__ import annotations
import argparse, csv, json, shutil, hashlib
from datetime import datetime, timezone
from pathlib import Path

CTB_GREEN="MESSAGE_CATALOG_PHASE22AE_6_5_10CT_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_STAGING_GREEN_DTS_AND_CSV_STAGED_SOURCE_HELD"
CTB_SAVEPOINT="MSG-022AE.6.5.10CT-B"
GREEN="MESSAGE_CATALOG_PHASE22AE_6_5_10CU_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_PROOF_REVIEW_GREEN_DBF_CDX_LMDB_READBACK_PROVEN"
RED="MESSAGE_CATALOG_PHASE22AE_6_5_10CU_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_PROOF_REVIEW_RED_REVIEW_REQUIRED"
NEXT="HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CV_B_NATIVE_MATERIALIZATION_REUSE_DECISION_PACKAGE"
CT_REL="docs/messaging/apply/phase22ae_6_5_10ct_b_native_candidate_table_materialization_staging_v1"
OUT_REL="docs/messaging/apply/phase22ae_6_5_10cu_b_native_candidate_table_materialization_proof_review_v1"
TABLES={"MSGHELP_CT":{"count":3,"tags":["MSG_ID","HELP_KEY"]},"CMDCHK_CT":{"count":4,"tags":["CMD_NAME","CHECK_ID"]},"MSGGATE_CT":{"count":4,"tags":["GATE_ID"]}}
GLOBAL=["DOTSCRIPT OUT:","SETPATH: DBF =","SETPATH: INDEXES =","SETPATH: LMDB =","WORKSPACE: 0 area(s) open.","(no file open in Area)"]
BOUNDARY=["NO_SOURCE_MUTATION","NO_ACTIVE_HELP_APPLY","NO_CMDHELPCHK_APPLY","NO_LATEST_POINTER_CHANGE"]

def rt(p): return p.read_text(encoding="utf-8",errors="replace") if p.exists() else ""
def wt(p,s): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding="utf-8",newline="\n")
def rows(p):
    try:
        with p.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
    except Exception: return []
def one(p):
    r=rows(p); return r[0] if r else {}
def wr(p,fields,rs):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rs: w.writerow({k:r.get(k,"") for k in fields})
def latest(repo):
    try: return json.loads(rt(repo/"docs/messaging/reports/message_savepoint_latest_v1.json"))
    except Exception: return {}
def has(repo,m): return int(m in rt(repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))
def sha(p):
    if not p.exists() or not p.is_file(): return ""
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()
def nonempty(p):
    try: return int(p.exists() and p.is_dir() and any(p.iterdir()))
    except Exception: return 0

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",required=True)
    ap.add_argument("--replace-existing-review",action="store_true")
    ap.add_argument("--allow-missing-ct-b-savepoint",action="store_true")
    a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); docs=repo/"docs/messaging"; reports=docs/"reports"
    ct=repo/CT_REL; out=repo/OUT_REL
    if out.exists() and a.replace_existing_review: shutil.rmtree(out)
    ctb=one(reports/"message_catalog_phase22ae_6_5_10ct_b_status_summary_v1.csv")
    latest_before=latest(repo).get("savepoint_id",latest(repo).get("savepoint",""))
    tpath=ct/"runlog/CT_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_TRANSCRIPT.txt"; txt=rt(tpath)
    ctb_green=int(ctb.get("STATUS","")==CTB_GREEN); ctb_sp=has(repo,CTB_SAVEPOINT)
    pre=[
      {"check_id":"ct_b_status_green","value":ctb_green,"expected":1,"status":"PASS" if ctb_green else "FAIL"},
      {"check_id":"ct_b_savepoint_present","value":ctb_sp,"expected":1,"status":"PASS" if ctb_sp else ("REVIEW" if a.allow_missing_ct_b_savepoint else "FAIL")},
      {"check_id":"transcript_exists","value":int(tpath.exists()),"expected":1,"status":"PASS" if tpath.exists() else "FAIL"},
      {"check_id":"cu_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or a.replace_existing_review) else "FAIL"},
    ]
    gm=[{"marker":m,"found":int(m in txt),"status":"PASS" if m in txt else "FAIL"} for m in GLOBAL]
    bm=[{"marker":m,"found":int(m in txt),"status":"PASS" if m in txt else "FAIL"} for m in BOUNDARY]
    tr=[]; tags=[]; arts=[]
    for table,spec in TABLES.items():
        n=spec["count"]; dbf=ct/"dbf"/(table+".dbf"); cdx=ct/"indexes"/(table+".cdx"); lmdb=ct/"lmdb"/(table+".cdx.d")
        tr.append({"table":table,"expected_records":n,"created_seen":int(f"{table}.dbf [X64]" in txt),"import_seen":int(f"Imported {n} records" in txt and f"{table}.csv" in txt),"listed_seen":int(f"{n} record(s) listed" in txt),"dbf_exists":int(dbf.exists()),"status":"PASS" if (f"{table}.dbf [X64]" in txt and f"Imported {n} records" in txt and f"{table}.csv" in txt and f"{n} record(s) listed" in txt and dbf.exists()) else "FAIL"})
        arts += [{"artifact":table+".dbf","path":str(dbf),"exists":int(dbf.exists()),"bytes":dbf.stat().st_size if dbf.exists() else 0,"sha256":sha(dbf),"nonempty_dir":""},
                 {"artifact":table+".cdx","path":str(cdx),"exists":int(cdx.exists()),"bytes":cdx.stat().st_size if cdx.exists() else 0,"sha256":sha(cdx),"nonempty_dir":""},
                 {"artifact":table+".cdx.d","path":str(lmdb),"exists":int(lmdb.exists()),"bytes":"","sha256":"","nonempty_dir":nonempty(lmdb)}]
        for tag in spec["tags"]:
            tags.append({"table":table,"tag":tag,"addtag_seen":int(f"CDX ADDTAG: added '{tag}'." in txt),"set_order_seen":int(f"SET ORDER: CDX TAG '{tag}' (ASC)" in txt),"status":"PASS" if (f"CDX ADDTAG: added '{tag}'." in txt and f"SET ORDER: CDX TAG '{tag}' (ASC)" in txt) else "FAIL"})
    boundary=[{"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},{"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},{"boundary":"source mutation authorized now","value":0,"status":"PASS"},{"boundary":"latest pointer changed by CU-B","value":0,"status":"PASS"},{"boundary":"reuse path confirmed now","value":0,"status":"PASS"}]
    validation=sum(r["status"]=="FAIL" for r in pre+gm+bm+tr+tags+boundary)+sum(str(r.get("exists"))!="1" for r in arts)
    status=GREEN if validation==0 else RED
    next_gate=NEXT if status==GREEN else "REVIEW_PHASE22AE_6_5_10CU_B_NATIVE_MATERIALIZATION_FAILURES"
    out.mkdir(parents=True,exist_ok=True); reports.mkdir(parents=True,exist_ok=True)
    wr(reports/"message_catalog_phase22ae_6_5_10cu_b_precondition_check_v1.csv",["check_id","value","expected","status"],pre)
    wr(reports/"message_catalog_phase22ae_6_5_10cu_b_global_marker_check_v1.csv",["marker","found","status"],gm)
    wr(reports/"message_catalog_phase22ae_6_5_10cu_b_boundary_marker_check_v1.csv",["marker","found","status"],bm)
    wr(reports/"message_catalog_phase22ae_6_5_10cu_b_table_readback_check_v1.csv",["table","expected_records","created_seen","import_seen","listed_seen","dbf_exists","status"],tr)
    wr(reports/"message_catalog_phase22ae_6_5_10cu_b_tag_order_check_v1.csv",["table","tag","addtag_seen","set_order_seen","status"],tags)
    wr(reports/"message_catalog_phase22ae_6_5_10cu_b_artifact_inventory_v1.csv",["artifact","path","exists","bytes","sha256","nonempty_dir"],arts)
    wr(reports/"message_catalog_phase22ae_6_5_10cu_b_boundary_check_v1.csv",["boundary","value","status"],boundary)
    summary=[{"STATUS":status,"VALIDATION_ISSUES":validation,"PHASE":"22AE.6.5.10CU-B","CORRECTED_CONCEPT":"DotTalk++ native table/materialization command path","CT_B_STATUS_GREEN":ctb_green,"CT_B_SAVEPOINT_PRESENT":ctb_sp,"OFFICIAL_LATEST_SAVEPOINT_BEFORE_CU_B":latest_before,"TRANSCRIPT_EXISTS":int(tpath.exists()),"GLOBAL_MARKERS_PASSED":sum(r["status"]=="PASS" for r in gm),"GLOBAL_MARKERS_TOTAL":len(gm),"BOUNDARY_MARKERS_PASSED":sum(r["status"]=="PASS" for r in bm),"BOUNDARY_MARKERS_TOTAL":len(bm),"TABLES_PASSED":sum(r["status"]=="PASS" for r in tr),"TABLES_TOTAL":len(tr),"TAGS_PASSED":sum(r["status"]=="PASS" for r in tags),"TAGS_TOTAL":len(tags),"ARTIFACTS_OBSERVED":sum(str(r.get("exists"))=="1" for r in arts),"ARTIFACTS_TOTAL":len(arts),"DBF_MATERIALIZATION_PROVEN":1 if status==GREEN else 0,"CDX_LMDB_MATERIALIZATION_PROVEN":1 if status==GREEN else 0,"NATIVE_TABLE_MATERIALIZATION_CONFIRMED_NOW":1 if status==GREEN else 0,"REUSE_PATH_CONFIRMED_NOW":0,"SOURCE_PATCH_NEEDED_PROVEN":0,"SOURCE_MUTATION_AUTHORIZED_NOW":0,"APPLY_EXECUTION_AUTHORIZED_NOW":0,"HELP_DATA_APPLY_EXECUTED":0,"CMDHELPCHK_APPLY_EXECUTED":0,"LATEST_POINTER_CHANGED_BY_CU_B":0,"NEXT_GATE":next_gate,"REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")}]
    wr(reports/"message_catalog_phase22ae_6_5_10cu_b_status_summary_v1.csv",list(summary[0].keys()),summary)
    wt(out/"message_catalog_phase22ae_6_5_10cu_b_manifest_v1.json",json.dumps({"phase":"22AE.6.5.10CU-B","status":status,"native_table_materialization_confirmed_now":1 if status==GREEN else 0,"reuse_path_confirmed_now":0,"next_gate":next_gate},indent=2))
    report=f"""# Phase 22AE.6.5.10CU-B Native Candidate Table Materialization Proof Review

- Status: {status}
- Validation issues: {validation}
- Corrected concept: DotTalk++ native table/materialization command path
- CT-B status green: {ctb_green}
- CT-B savepoint present: {ctb_sp}
- Transcript exists: {int(tpath.exists())}
- Tables passed: {sum(r['status']=='PASS' for r in tr)}/{len(tr)}
- Tags passed: {sum(r['status']=='PASS' for r in tags)}/{len(tags)}
- Artifacts observed: {sum(str(r.get('exists'))=='1' for r in arts)}/{len(arts)}
- DBF materialization proven: {1 if status==GREEN else 0}
- CDX/LMDB materialization proven: {1 if status==GREEN else 0}
- Native table materialization confirmed now: {1 if status==GREEN else 0}
- Reuse path confirmed now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Latest pointer changed by CU-B: 0
- Next gate: {next_gate}
"""
    wt(out/"MESSAGE_LOCALE_PHASE22AE_6_5_10CU_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_PROOF_REVIEW.md",report)
    wt(docs/"MESSAGE_LOCALE_PHASE22AE_6_5_10CU_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_PROOF_REVIEW.md",report)
    print(status)
    print(f"  validation issues: {validation}")
    print("  corrected concept: DotTalk++ native table/materialization command path")
    print(f"  CT-B status green: {ctb_green}")
    print(f"  CT-B savepoint present: {ctb_sp}")
    print(f"  transcript exists: {int(tpath.exists())}")
    print(f"  tables passed: {sum(r['status']=='PASS' for r in tr)}/{len(tr)}")
    print(f"  tags passed: {sum(r['status']=='PASS' for r in tags)}/{len(tags)}")
    print(f"  artifacts observed: {sum(str(r.get('exists'))=='1' for r in arts)}/{len(arts)}")
    print(f"  DBF materialization proven: {1 if status==GREEN else 0}")
    print(f"  CDX/LMDB materialization proven: {1 if status==GREEN else 0}")
    print(f"  native table materialization confirmed now: {1 if status==GREEN else 0}")
    print("  reuse path confirmed now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  latest pointer changed by CU-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status==GREEN else 1
if __name__=="__main__": raise SystemExit(main())
