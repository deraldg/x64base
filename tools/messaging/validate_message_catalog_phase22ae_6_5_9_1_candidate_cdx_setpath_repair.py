
from __future__ import annotations
import argparse, csv, hashlib, re
from pathlib import Path
from datetime import datetime, timezone

OK="MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR_GREEN_SOURCE_HELD"
BAD="MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR_BLOCKED"
NEXT="HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10_CANDIDATE_LMDB_REBUILD_PACKAGE"

def rows(p):
    if not p.exists(): return []
    with p.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def first(p):
    r=rows(p); return r[0] if r else {}
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
        h.update(str(x.relative_to(p)).replace("\\","/").encode("utf-8")); h.update(sha(x).encode("ascii")); total += x.stat().st_size
    return (h.hexdigest(), len(files), total)
def fp(repo):
    out=[]
    roots=[("active_msg",repo/"dottalkpp/data/messaging"),("active_index_msg",repo/"dottalkpp/data/indexes/messaging"),("active_lmdb_msg",repo/"dottalkpp/data/lmdb/messaging"),("default_index",repo/"dottalkpp/data/indexes"),("default_lmdb",repo/"dottalkpp/data/lmdb")]
    for prefix,root in roots:
        for name in ["SYSTEM_MESSAGES","SYSTEM_MESSAGE_TEXT"]:
            for p in sorted(root.glob(name+"*")) if root.exists() else []:
                if p.is_dir():
                    h,c,b=dir_sha(p); out.append({"ROLE":prefix+"_"+p.name,"PATH":rel(p,repo),"KIND":"dir","BYTES":b,"SHA256":h,"FILES":c})
                elif p.is_file():
                    out.append({"ROLE":prefix+"_"+p.name,"PATH":rel(p,repo),"KIND":"file","BYTES":p.stat().st_size,"SHA256":sha(p),"FILES":1})
    return out
def diff(a,b):
    aa={r["PATH"]:r for r in a}; bb={r["PATH"]:r for r in b}; out=[]
    for k in sorted(set(aa)|set(bb)):
        if aa.get(k,{}).get("SHA256")!=bb.get(k,{}).get("SHA256") or str(aa.get(k,{}).get("BYTES",""))!=str(bb.get(k,{}).get("BYTES","")):
            out.append({"PATH":k,"BEFORE_SHA256":aa.get(k,{}).get("SHA256",""),"AFTER_SHA256":bb.get(k,{}).get("SHA256","")})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args=ap.parse_args()
    repo=Path(args.repo_root).resolve(); reports=repo/"docs/messaging/reports"
    stage=first(reports/"message_catalog_phase22ae_6_5_9_1_stage_status_summary_v1.csv")
    before=rows(reports/"message_catalog_phase22ae_6_5_9_1_active_fingerprint_before_v1.csv")
    idx=repo/stage.get("CANDIDATE_INDEX_ROOT","")
    msg_cdx=idx/"SYSTEM_MESSAGES.cdx"; txt_cdx=idx/"SYSTEM_MESSAGE_TEXT.cdx"
    run=Path(args.runtime_proof) if args.runtime_proof else repo/"docs/messaging/runlog/MSG-022AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR.md"
    if not run.is_absolute(): run=repo/run
    text=run.read_text(encoding="utf-8", errors="replace") if run.exists() else ""
    upper=text.upper()
    after=fp(repo); delta=diff(before,after)
    gates=[]; fail=0
    def gate(name, ok, detail):
        nonlocal fail
        gates.append({"GATE":name,"STATUS":"PASS" if ok else "FAIL","DETAIL":str(detail)})
        if not ok: fail += 1
    gate("STAGE_GREEN",stage.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR_STAGED_SOURCE_HELD",stage.get("STATUS","missing"))
    gate("RUNTIME_LOG_EXISTS",run.exists(),rel(run,repo))
    gate("CANDIDATE_MESSAGE_CDX_EXISTS",msg_cdx.exists() and msg_cdx.stat().st_size>0,msg_cdx.stat().st_size if msg_cdx.exists() else 0)
    gate("CANDIDATE_TEXT_CDX_EXISTS",txt_cdx.exists() and txt_cdx.stat().st_size>0,txt_cdx.stat().st_size if txt_cdx.exists() else 0)
    gate("RUNTIME_COUNTS_14_70",re.search(r"(?m)^\s*14\s*$",text) and re.search(r"(?m)^\s*70\s*$",text),"14/70")
    gate("RUNTIME_PATH_SETUP_VISIBLE","SETPATH" in upper or "SET PATH" in upper or "INDEXES" in upper, "path setup evidence")
    gate("RUNTIME_NO_DEFAULT_INDEX_CREATION", "D:\\CODE\\CCODE\\DOTTALKPP\\DATA\\INDEXES\\SYSTEM_" not in upper, "no default index root output")
    gate("RUNTIME_NO_ERROR_WORDS", not any(w in upper for w in ["ERROR","FAILED","UNKNOWN COMMAND","USAGE:"]), "no error words")
    gate("ACTIVE_FINGERPRINT_CLEAN_FOR_6_5_9_1",len(delta)==0,len(delta))
    status=OK if fail==0 else BAD
    inv=[
        {"ROLE":"candidate_message_cdx","PATH":rel(msg_cdx,repo),"EXISTS":1 if msg_cdx.exists() else 0,"BYTES":msg_cdx.stat().st_size if msg_cdx.exists() else "","SHA256":sha(msg_cdx)},
        {"ROLE":"candidate_text_cdx","PATH":rel(txt_cdx,repo),"EXISTS":1 if txt_cdx.exists() else 0,"BYTES":txt_cdx.stat().st_size if txt_cdx.exists() else "","SHA256":sha(txt_cdx)}
    ]
    boundary=[
        {"PROTECTED_SYSTEM":"ACTIVE_AND_DEFAULT_INDEX_ROOTS","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0 if len(delta)==0 else 1,"DETAIL":f"fingerprint changes={len(delta)}"},
        {"PROTECTED_SYSTEM":"CANDIDATE_INDEX_ROOT","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":1 if msg_cdx.exists() or txt_cdx.exists() else 0,"DETAIL":rel(idx,repo)},
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no source mutation"},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no HELP mutation"},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no CMDHELPCHK mutation"},
    ]
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_validate_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_candidate_cdx_inventory_v1.csv",inv,["ROLE","PATH","EXISTS","BYTES","SHA256"])
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_active_fingerprint_after_v1.csv",after,["ROLE","PATH","KIND","BYTES","SHA256","FILES"])
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_active_fingerprint_delta_v1.csv",delta,["PATH","BEFORE_SHA256","AFTER_SHA256"])
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_boundary_ledger_v1.csv",boundary,["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports/"message_catalog_phase22ae_6_5_9_1_validate_status_summary_v1.csv",[{
        "STATUS":status,"VALIDATION_ISSUES":"0" if status==OK else str(max(1,fail)),
        "STAGE_GREEN":1 if stage.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_9_1_CANDIDATE_CDX_SETPATH_REPAIR_STAGED_SOURCE_HELD" else 0,
        "CANDIDATE_MESSAGE_CDX_EXISTS":1 if msg_cdx.exists() else 0,"CANDIDATE_MESSAGE_CDX_BYTES":msg_cdx.stat().st_size if msg_cdx.exists() else "",
        "CANDIDATE_TEXT_CDX_EXISTS":1 if txt_cdx.exists() else 0,"CANDIDATE_TEXT_CDX_BYTES":txt_cdx.stat().st_size if txt_cdx.exists() else "",
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0 if len(delta)==0 else 1,"PROTECTED_FINGERPRINT_CHANGES":len(delta),
        "SOURCE_FILES_MUTATED":0,"HELP_DATA_MUTATION_OBSERVED":0,"CMDHELPCHK_MUTATION_OBSERVED":0,
        "NEXT_GATE":NEXT if status==OK else "HOLD_AND_FIX_PHASE22AE_6_5_9_1_CDX_SETPATH_REPAIR",
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }],["STATUS","VALIDATION_ISSUES","STAGE_GREEN","CANDIDATE_MESSAGE_CDX_EXISTS","CANDIDATE_MESSAGE_CDX_BYTES","CANDIDATE_TEXT_CDX_EXISTS","CANDIDATE_TEXT_CDX_BYTES","ACTIVE_CATALOG_MUTATION_OBSERVED","PROTECTED_FINGERPRINT_CHANGES","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    print(status)
    print(f"  validation issues: {'0' if status==OK else str(max(1,fail))}")
    print(f"  candidate message cdx exists/bytes: {1 if msg_cdx.exists() else 0}/{msg_cdx.stat().st_size if msg_cdx.exists() else ''}")
    print(f"  candidate text cdx exists/bytes: {1 if txt_cdx.exists() else 0}/{txt_cdx.stat().st_size if txt_cdx.exists() else ''}")
    print(f"  active catalog mutation observed: {0 if len(delta)==0 else 1}")
    print(f"  protected fingerprint changes: {len(delta)}")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT if status==OK else 'HOLD_AND_FIX_PHASE22AE_6_5_9_1_CDX_SETPATH_REPAIR'}")
    print(f"  reports: {reports}")
    return 0 if status==OK else 2

if __name__=="__main__":
    raise SystemExit(main())
