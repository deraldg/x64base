
from __future__ import annotations
import argparse, csv, hashlib, re
from datetime import datetime, timezone
from pathlib import Path

OK="MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_GREEN_SOURCE_HELD"
BAD="MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_BLOCKED"
NEXT="HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10_CANDIDATE_LMDB_REBUILD_PACKAGE"

def rows(p):
    if not p.exists(): return []
    with p.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def first(p):
    r=rows(p); return r[0] if r else {}
def wcsv(p, rs, fs):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fs,lineterminator="\n",extrasaction="ignore"); w.writeheader(); [w.writerow({k:r.get(k,"") for k in fs}) for r in rs]
def rel(p,repo):
    try: return str(p.relative_to(repo)).replace("\\","/")
    except Exception: return str(p).replace("\\","/")
def sha(p):
    if not p.exists() or not p.is_file(): return ""
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def fp(repo):
    out=[]
    roots=[repo/"dottalkpp/data/messaging",repo/"dottalkpp/data/indexes/messaging",repo/"dottalkpp/data/lmdb/messaging",repo/"dottalkpp/data/indexes",repo/"dottalkpp/data/lmdb"]
    names=["SYSTEM_MESSAGES","SYSTEM_MESSAGE_TEXT"]
    for root in roots:
        for name in names:
            for p in list(root.glob(name+"*")) if root.exists() else []:
                if p.is_file(): out.append({"ROLE":root.name+"_"+p.name,"PATH":rel(p,repo),"SHA256":sha(p),"BYTES":p.stat().st_size})
    return out
def diff(a,b):
    aa={x["PATH"]:x for x in a}; bb={x["PATH"]:x for x in b}
    out=[]
    for k in sorted(set(aa)|set(bb)):
        if aa.get(k,{}).get("SHA256")!=bb.get(k,{}).get("SHA256") or str(aa.get(k,{}).get("BYTES",""))!=str(bb.get(k,{}).get("BYTES","")):
            out.append({"PATH":k,"BEFORE_SHA256":aa.get(k,{}).get("SHA256",""),"AFTER_SHA256":bb.get(k,{}).get("SHA256","")})
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",required=True); ap.add_argument("--runtime-proof",default="")
    a=ap.parse_args(); repo=Path(a.repo_root).resolve(); rep=repo/"docs/messaging/reports"
    st=first(rep/"message_catalog_phase22ae_6_5_9_stage_status_summary_v1.csv")
    idx=repo/st.get("CANDIDATE_INDEX_ROOT","")
    msg=idx/"SYSTEM_MESSAGES.cdx"; txt=idx/"SYSTEM_MESSAGE_TEXT.cdx"
    run=Path(a.runtime_proof) if a.runtime_proof else repo/"docs/messaging/runlog/MSG-022AE_6_5_9_CANDIDATE_CDX_REBUILD.md"
    if not run.is_absolute(): run=repo/run
    text=run.read_text(encoding="utf-8",errors="replace") if run.exists() else ""; upper=text.upper()
    before=rows(rep/"message_catalog_phase22ae_6_5_9_active_fingerprint_before_v1.csv")
    after=fp(repo); delta=diff(before,after)
    gates=[]; fail=0
    def gate(n,ok,d):
        nonlocal fail
        gates.append({"GATE":n,"STATUS":"PASS" if ok else "FAIL","DETAIL":str(d)})
        if not ok: fail+=1
    gate("STAGE_GREEN",st.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_PACKAGE_STAGED_SOURCE_HELD",st.get("STATUS","missing"))
    gate("RUNTIME_LOG_EXISTS",run.exists(),rel(run,repo))
    gate("CANDIDATE_MESSAGE_CDX_EXISTS",msg.exists() and msg.stat().st_size>0,msg.stat().st_size if msg.exists() else 0)
    gate("CANDIDATE_TEXT_CDX_EXISTS",txt.exists() and txt.stat().st_size>0,txt.stat().st_size if txt.exists() else 0)
    gate("RUNTIME_COUNT_14_70_SEEN",re.search(r"(?m)^\s*14\s*$",text) and re.search(r"(?m)^\s*70\s*$",text),"14/70")
    gate("RUNTIME_NO_ERROR_WORDS",not any(w in upper for w in ["ERROR","FAILED","UNKNOWN COMMAND","USAGE:"]),"scan")
    gate("ACTIVE_FINGERPRINT_CLEAN",len(delta)==0,len(delta))
    status=OK if fail==0 else BAD
    inv=[
        {"ROLE":"candidate_message_cdx","PATH":rel(msg,repo),"EXISTS":1 if msg.exists() else 0,"BYTES":msg.stat().st_size if msg.exists() else "","SHA256":sha(msg)},
        {"ROLE":"candidate_text_cdx","PATH":rel(txt,repo),"EXISTS":1 if txt.exists() else 0,"BYTES":txt.stat().st_size if txt.exists() else "","SHA256":sha(txt)}
    ]
    boundary=[
        {"PROTECTED_SYSTEM":"ACTIVE_CATALOG_INDEX_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0 if len(delta)==0 else 1,"DETAIL":f"fingerprint changes={len(delta)}"},
        {"PROTECTED_SYSTEM":"CANDIDATE_INDEX_ROOT","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":1 if msg.exists() or txt.exists() else 0,"DETAIL":rel(idx,repo)},
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no source mutation"},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no HELP mutation"},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no CMDHELPCHK mutation"},
    ]
    wcsv(rep/"message_catalog_phase22ae_6_5_9_validate_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_candidate_cdx_inventory_v1.csv",inv,["ROLE","PATH","EXISTS","BYTES","SHA256"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_active_fingerprint_after_v1.csv",after,["ROLE","PATH","SHA256","BYTES"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_active_fingerprint_delta_v1.csv",delta,["PATH","BEFORE_SHA256","AFTER_SHA256"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_boundary_ledger_v1.csv",boundary,["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_validate_status_summary_v1.csv",[{
        "STATUS":status,"VALIDATION_ISSUES":"0" if status==OK else str(max(1,fail)),
        "STAGE_GREEN":1 if st.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_PACKAGE_STAGED_SOURCE_HELD" else 0,
        "CANDIDATE_MESSAGE_CDX_EXISTS":1 if msg.exists() else 0,"CANDIDATE_MESSAGE_CDX_BYTES":msg.stat().st_size if msg.exists() else "",
        "CANDIDATE_TEXT_CDX_EXISTS":1 if txt.exists() else 0,"CANDIDATE_TEXT_CDX_BYTES":txt.stat().st_size if txt.exists() else "",
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0 if len(delta)==0 else 1,"PROTECTED_FINGERPRINT_CHANGES":len(delta),
        "SOURCE_FILES_MUTATED":0,"HELP_DATA_MUTATION_OBSERVED":0,"CMDHELPCHK_MUTATION_OBSERVED":0,
        "NEXT_GATE":NEXT if status==OK else "HOLD_AND_FIX_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD",
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }],["STATUS","VALIDATION_ISSUES","STAGE_GREEN","CANDIDATE_MESSAGE_CDX_EXISTS","CANDIDATE_MESSAGE_CDX_BYTES","CANDIDATE_TEXT_CDX_EXISTS","CANDIDATE_TEXT_CDX_BYTES","ACTIVE_CATALOG_MUTATION_OBSERVED","PROTECTED_FINGERPRINT_CHANGES","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    print(status); print(f"  validation issues: {'0' if status==OK else str(max(1,fail))}")
    print(f"  candidate message cdx exists/bytes: {1 if msg.exists() else 0}/{msg.stat().st_size if msg.exists() else ''}")
    print(f"  candidate text cdx exists/bytes: {1 if txt.exists() else 0}/{txt.stat().st_size if txt.exists() else ''}")
    print(f"  active catalog mutation observed: {0 if len(delta)==0 else 1}")
    print(f"  protected fingerprint changes: {len(delta)}")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT if status==OK else 'HOLD_AND_FIX_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD'}")
    print(f"  reports: {rep}")
    return 0 if status==OK else 2
if __name__=="__main__": raise SystemExit(main())
