
from __future__ import annotations
import argparse, csv, hashlib, json, shutil
from pathlib import Path
from datetime import datetime, timezone

OK="MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR_STAGED_SOURCE_HELD"
BAD="MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR_BLOCKED"
NEXT="RUN_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR_RUNTIME_THEN_VALIDATE"

def read_rows(p):
    if not p.exists(): return []
    with p.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def first(p):
    r=read_rows(p); return r[0] if r else {}
def wcsv(p, rows, fields):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in fields})
def rel(p, repo):
    try: return str(p.relative_to(repo)).replace("\\","/")
    except Exception: return str(p).replace("\\","/")
def sha(p):
    if not p.exists() or not p.is_file(): return ""
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()
def dir_sha(p):
    if not p.exists(): return ("",0,0)
    if p.is_file(): return (sha(p),1,p.stat().st_size)
    files=sorted(x for x in p.rglob("*") if x.is_file())
    h=hashlib.sha256(); total=0
    for x in files:
        h.update(str(x.relative_to(p)).replace("\\","/").encode("utf-8"))
        h.update(sha(x).encode("ascii"))
        total += x.stat().st_size
    return (h.hexdigest(), len(files), total)
def fp(repo):
    out=[]
    roots=[
        ("active_msg",repo/"dottalkpp/data/messaging"),
        ("active_index_msg",repo/"dottalkpp/data/indexes/messaging"),
        ("active_lmdb_msg",repo/"dottalkpp/data/lmdb/messaging"),
        ("default_index",repo/"dottalkpp/data/indexes"),
        ("default_lmdb",repo/"dottalkpp/data/lmdb"),
    ]
    for prefix,root in roots:
        for name in ["SYSTEM_MESSAGES","SYSTEM_MESSAGE_TEXT"]:
            for p in sorted(root.glob(name+"*")) if root.exists() else []:
                if p.is_dir():
                    h,c,b=dir_sha(p)
                    out.append({"ROLE":prefix+"_"+p.name,"PATH":rel(p,repo),"KIND":"dir","EXISTS":1,"BYTES":b,"SHA256":h,"FILES":c})
                elif p.is_file():
                    out.append({"ROLE":prefix+"_"+p.name,"PATH":rel(p,repo),"KIND":"file","EXISTS":1,"BYTES":p.stat().st_size,"SHA256":sha(p),"FILES":1})
    return out
def sp(repo, sid):
    latest=repo/"docs/messaging/reports/message_savepoint_latest_v1.json"
    latest_id=""
    if latest.exists():
        try: latest_id=json.loads(latest.read_text(encoding="utf-8")).get("savepoint_id","")
        except Exception: latest_id=""
    journal=repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text=journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id==sid or sid in text, latest_id

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-candidate-cdx-repair", action="store_true")
    ap.add_argument("--replace-existing-candidate-indexes", action="store_true")
    args=ap.parse_args()
    repo=Path(args.repo_root).resolve()
    reports=repo/"docs/messaging/reports"; reports.mkdir(parents=True, exist_ok=True)
    cand=repo/"docs/messaging/candidates/phase22ae_6_5_8_active_basename_candidate_v1"
    dbf=cand/"dbf"; indexes=cand/"indexes"; lmdb=cand/"lmdb"
    msg=dbf/"SYSTEM_MESSAGES.dbf"; txt=dbf/"SYSTEM_MESSAGE_TEXT.dbf"; dtx=dbf/"SYSTEM_MESSAGE_TEXT.dtx"
    v659=first(reports/"message_catalog_phase22ae_6_5_9_validate_status_summary_v1.csv")
    s658=first(reports/"message_catalog_phase22ae_6_5_8_validate_status_summary_v1.csv")
    sp_ok, latest=sp(repo,"MSG-022AE.6.5.8")
    gates=[]; fail=0
    def gate(name, ok, detail):
        nonlocal fail
        gates.append({"GATE":name,"STATUS":"PASS" if ok else "FAIL","DETAIL":str(detail)})
        if not ok: fail += 1
    gate("PHASE22AE_6_5_8_GREEN",s658.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_AND_READBACK_GREEN_SOURCE_HELD",s658.get("STATUS","missing"))
    gate("MSG_022AE_6_5_8_SAVEPOINT_PRESENT",sp_ok,latest)
    gate("PHASE22AE_6_5_9_BLOCKED_INCIDENT_CAPTURED",v659.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_BLOCKED",v659.get("STATUS","missing"))
    gate("CANDIDATE_CDX_REPAIR_EXPLICITLY_AUTHORIZED",args.allow_candidate_cdx_repair,args.allow_candidate_cdx_repair)
    gate("CANDIDATE_DBF_DTX_PRESENT",msg.exists() and txt.exists() and dtx.exists(),rel(dbf,repo))
    gate("CANDIDATE_INDEX_ROOT_ABSENT_OR_REPLACE_AUTHORIZED",(not indexes.exists()) or args.replace_existing_candidate_indexes,rel(indexes,repo))
    before=fp(repo)
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_active_fingerprint_before_v1.csv",before,["ROLE","PATH","KIND","EXISTS","BYTES","SHA256","FILES"])
    script_rel=""; err=""
    if fail==0:
        try:
            if indexes.exists() and args.replace_existing_candidate_indexes:
                shutil.rmtree(indexes)
            indexes.mkdir(parents=True, exist_ok=True)
            lmdb.mkdir(parents=True, exist_ok=True)
            script=repo/"docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR.dts"
            script.parent.mkdir(parents=True, exist_ok=True)
            dbf_abs=dbf.resolve().as_posix()
            idx_abs=indexes.resolve().as_posix()
            script.write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR.dts",
                "* Candidate-only repair after 6.5.9 SET INDEXES TO failure.",
                "* Uses simple .dts path setup: SETPATH DBF and SETPATH INDEXES.",
                "* Do not use SET CDX or SET INDEXES TO.",
                f"SETPATH DBF {dbf_abs}",
                f"SETPATH INDEXES {idx_abs}",
                "SET PATH",
                "SELECT 0",
                "USE SYSTEM_MESSAGES",
                "CDX CREATE",
                "CDX ADDTAG SYMBOL",
                "CDX ADDTAG STATUS",
                "CDX ADDTAG SRC",
                "SET INDEX TO SYSTEM_MESSAGES",
                "SET ORDER TO TAG SYMBOL",
                "TOP",
                "COUNT",
                "SELECT 0",
                "USE SYSTEM_MESSAGE_TEXT",
                "CDX CREATE",
                "CDX ADDTAG SYMBOL",
                "CDX ADDTAG LOCALE",
                "CDX ADDTAG STATUS",
                "SET INDEX TO SYSTEM_MESSAGE_TEXT",
                "SET ORDER TO TAG SYMBOL",
                "TOP",
                "COUNT",
                "",
            ]), encoding="utf-8")
            script_rel=rel(script,repo)
        except Exception as e:
            err=str(e); fail += 1
    status=OK if fail==0 else BAD
    boundary=[
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no active DBF mutation in 6.5.9.1"},
        {"PROTECTED_SYSTEM":"ACTIVE_AND_DEFAULT_INDEX_ROOTS","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"repair script targets candidate INDEXES slot using SETPATH"},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no LMDB rebuild in 6.5.9.1"},
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no source mutation"},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no HELP mutation"},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no CMDHELPCHK mutation"},
    ]
    inv=[
        {"ROLE":"candidate_dbf_root","PATH":rel(dbf,repo),"EXISTS":1 if dbf.exists() else 0,"BYTES":"","SHA256":""},
        {"ROLE":"candidate_indexes_root","PATH":rel(indexes,repo),"EXISTS":1 if indexes.exists() else 0,"BYTES":"","SHA256":""},
        {"ROLE":"candidate_message_dbf","PATH":rel(msg,repo),"EXISTS":1 if msg.exists() else 0,"BYTES":msg.stat().st_size if msg.exists() else "","SHA256":sha(msg)},
        {"ROLE":"candidate_text_dbf","PATH":rel(txt,repo),"EXISTS":1 if txt.exists() else 0,"BYTES":txt.stat().st_size if txt.exists() else "","SHA256":sha(txt)},
        {"ROLE":"candidate_text_dtx","PATH":rel(dtx,repo),"EXISTS":1 if dtx.exists() else 0,"BYTES":dtx.stat().st_size if dtx.exists() else "","SHA256":sha(dtx)},
    ]
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_stage_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_candidate_inventory_before_v1.csv",inv,["ROLE","PATH","EXISTS","BYTES","SHA256"])
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_boundary_ledger_v1.csv",boundary,["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_stage_status_summary_v1.csv",[{
        "STATUS":status,"VALIDATION_ISSUES":"0" if status==OK else str(max(1,fail)),
        "PHASE22AE_6_5_8_GREEN":1 if s658.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_AND_READBACK_GREEN_SOURCE_HELD" else 0,
        "PHASE22AE_6_5_9_BLOCKED_INCIDENT_CAPTURED":1 if v659.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_BLOCKED" else 0,
        "CANDIDATE_DBF_ROOT":rel(dbf,repo),"CANDIDATE_INDEX_ROOT":rel(indexes,repo),"SCRIPT_PATH":script_rel,
        "CANDIDATE_CDX_REPAIR_AUTHORIZED":1 if args.allow_candidate_cdx_repair else 0,
        "CANDIDATE_LMDB_REBUILD_AUTHORIZED":0,"ACTIVE_PROMOTION_AUTHORIZED":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0,"SOURCE_FILES_MUTATED":0,
        "HELP_DATA_MUTATION_OBSERVED":0,"CMDHELPCHK_MUTATION_OBSERVED":0,
        "ERRORS":err,"NEXT_GATE":NEXT if status==OK else "HOLD_AND_FIX_PHASE22AE_6_5_9_1_STAGE",
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }],["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_8_GREEN","PHASE22AE_6_5_9_BLOCKED_INCIDENT_CAPTURED","CANDIDATE_DBF_ROOT","CANDIDATE_INDEX_ROOT","SCRIPT_PATH","CANDIDATE_CDX_REPAIR_AUTHORIZED","CANDIDATE_LMDB_REBUILD_AUTHORIZED","ACTIVE_PROMOTION_AUTHORIZED","ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","ERRORS","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    print(status)
    print(f"  validation issues: {'0' if status==OK else str(max(1,fail))}")
    print(f"  Phase 22AE.6.5.8 green: {1 if s658.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_AND_READBACK_GREEN_SOURCE_HELD' else 0}")
    print(f"  Phase 22AE.6.5.9 blocked incident captured: {1 if v659.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_BLOCKED' else 0}")
    print(f"  candidate DBF root: {rel(dbf,repo)}")
    print(f"  candidate index root: {rel(indexes,repo)}")
    print(f"  script path: {script_rel}")
    print(f"  candidate CDX repair authorized: {1 if args.allow_candidate_cdx_repair else 0}")
    print("  candidate LMDB rebuild authorized: 0")
    print("  active promotion authorized: 0")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT if status==OK else 'HOLD_AND_FIX_PHASE22AE_6_5_9_1_STAGE'}")
    print(f"  reports: {reports}")
    return 0 if status==OK else 2

if __name__=="__main__":
    raise SystemExit(main())
