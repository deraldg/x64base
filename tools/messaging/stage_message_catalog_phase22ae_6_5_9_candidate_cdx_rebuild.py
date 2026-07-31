
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

OK="MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_PACKAGE_STAGED_SOURCE_HELD"
BAD="MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_PACKAGE_BLOCKED"
NEXT="RUN_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_RUNTIME_THEN_VALIDATE"

def rows(p):
    if not p.exists(): return []
    with p.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def first(p): 
    r=rows(p); return r[0] if r else {}
def wcsv(p, rs, fs):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fs, lineterminator="\n", extrasaction="ignore"); w.writeheader(); [w.writerow({k:r.get(k,"") for k in fs}) for r in rs]
def rel(p, repo):
    try: return str(p.relative_to(repo)).replace("\\","/")
    except Exception: return str(p).replace("\\","/")
def sha(p):
    if not p.exists() or not p.is_file(): return ""
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()
def sp(repo, sid):
    latest=repo/"docs/messaging/reports/message_savepoint_latest_v1.json"
    latest_id=""
    if latest.exists():
        try: latest_id=json.loads(latest.read_text(encoding="utf-8")).get("savepoint_id","")
        except Exception: latest_id=""
    j=repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    t=j.read_text(encoding="utf-8", errors="replace") if j.exists() else ""
    return latest_id==sid or sid in t, latest_id
def fp(repo):
    out=[]
    active=repo/"dottalkpp/data/messaging"
    ai=repo/"dottalkpp/data/indexes/messaging"
    al=repo/"dottalkpp/data/lmdb/messaging"
    di=repo/"dottalkpp/data/indexes"
    dl=repo/"dottalkpp/data/lmdb"
    for tab in ["SYSTEM_MESSAGES","SYSTEM_MESSAGE_TEXT"]:
        for role,path in [
            (f"active_dbf_{tab}",active/f"{tab}.dbf"),
            (f"active_dtx_{tab}",active/f"{tab}.dtx"),
            (f"active_index_{tab}",ai/f"{tab}.cdx"),
            (f"active_index_meta_{tab}",ai/f"{tab}.cdx.meta"),
            (f"active_lmdb_{tab}",al/f"{tab}.cdx.d"),
            (f"default_index_{tab}",di/f"{tab}.cdx"),
            (f"default_index_meta_{tab}",di/f"{tab}.cdx.meta"),
            (f"default_lmdb_{tab}",dl/f"{tab}.cdx.d"),
        ]:
            if path.is_dir():
                files=sorted(x for x in path.rglob("*") if x.is_file())
                h=hashlib.sha256(); total=0
                for x in files:
                    h.update(str(x.relative_to(path)).replace("\\","/").encode()); h.update(sha(x).encode()); total+=x.stat().st_size
                out.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":1,"KIND":"dir","BYTES":total,"SHA256":h.hexdigest(),"FILES":len(files)})
            elif path.is_file():
                out.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":1,"KIND":"file","BYTES":path.stat().st_size,"SHA256":sha(path),"FILES":1})
            else:
                out.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":0,"KIND":"missing","BYTES":0,"SHA256":"","FILES":0})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-candidate-cdx-rebuild", action="store_true")
    ap.add_argument("--replace-existing-candidate-indexes", action="store_true")
    a=ap.parse_args()
    repo=Path(a.repo_root).resolve()
    rep=repo/"docs/messaging/reports"; rep.mkdir(parents=True, exist_ok=True)
    cand=repo/"docs/messaging/candidates/phase22ae_6_5_8_active_basename_candidate_v1"
    dbf=cand/"dbf"; idx=cand/"indexes"; lmdb=cand/"lmdb"
    msg=dbf/"SYSTEM_MESSAGES.dbf"; txt=dbf/"SYSTEM_MESSAGE_TEXT.dbf"; dtx=dbf/"SYSTEM_MESSAGE_TEXT.dtx"
    s658=first(rep/"message_catalog_phase22ae_6_5_8_validate_status_summary_v1.csv")
    sp_ok,latest=sp(repo,"MSG-022AE.6.5.8")
    gates=[]; fail=0
    def gate(n, ok, detail):
        nonlocal fail
        gates.append({"GATE":n,"STATUS":"PASS" if ok else "FAIL","DETAIL":str(detail)})
        if not ok: fail+=1
    gate("PHASE22AE_6_5_8_GREEN",s658.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_AND_READBACK_GREEN_SOURCE_HELD",s658.get("STATUS","missing"))
    gate("MSG_022AE_6_5_8_SAVEPOINT_PRESENT",sp_ok,latest)
    gate("CANDIDATE_CDX_REBUILD_EXPLICITLY_AUTHORIZED",a.allow_candidate_cdx_rebuild,a.allow_candidate_cdx_rebuild)
    gate("CANDIDATE_DBF_ARTIFACTS_PRESENT",msg.exists() and txt.exists() and dtx.exists(),rel(dbf,repo))
    gate("CANDIDATE_INDEX_ROOT_ABSENT_OR_REPLACE_AUTHORIZED",(not idx.exists()) or a.replace_existing_candidate_indexes,rel(idx,repo))
    before=fp(repo)
    wcsv(rep/"message_catalog_phase22ae_6_5_9_active_fingerprint_before_v1.csv", before, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    script_rel=""; err=""
    if fail==0:
        try:
            if idx.exists() and a.replace_existing_candidate_indexes: shutil.rmtree(idx)
            idx.mkdir(parents=True, exist_ok=True); lmdb.mkdir(parents=True, exist_ok=True)
            script=repo/"docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD.dts"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD.dts",
                "* Candidate-only CDX rebuild. If SET INDEXES syntax is not accepted, stop and report output.",
                "* No active DBF/CDX/LMDB mutation is authorized.",
                f"SET INDEXES TO {idx.resolve().as_posix()}",
                "SELECT 1",
                f"USE {msg.resolve().as_posix()}",
                "CDX CREATE",
                "CDX ADDTAG SYMBOL",
                "CDX ADDTAG STATUS",
                "CDX ADDTAG SRC",
                "COUNT",
                "SELECT 2",
                f"USE {txt.resolve().as_posix()}",
                "CDX CREATE",
                "CDX ADDTAG SYMBOL",
                "CDX ADDTAG LOCALE",
                "CDX ADDTAG STATUS",
                "COUNT",
                ""
            ]), encoding="utf-8")
            script_rel=rel(script,repo)
        except Exception as e:
            err=str(e); fail+=1
    status=OK if fail==0 else BAD
    inv=[
        {"ROLE":"candidate_message_dbf","PATH":rel(msg,repo),"EXISTS":1 if msg.exists() else 0,"BYTES":msg.stat().st_size if msg.exists() else "","SHA256":sha(msg)},
        {"ROLE":"candidate_text_dbf","PATH":rel(txt,repo),"EXISTS":1 if txt.exists() else 0,"BYTES":txt.stat().st_size if txt.exists() else "","SHA256":sha(txt)},
        {"ROLE":"candidate_text_dtx","PATH":rel(dtx,repo),"EXISTS":1 if dtx.exists() else 0,"BYTES":dtx.stat().st_size if dtx.exists() else "","SHA256":sha(dtx)},
        {"ROLE":"candidate_message_cdx_target","PATH":rel(idx/"SYSTEM_MESSAGES.cdx",repo),"EXISTS":1 if (idx/"SYSTEM_MESSAGES.cdx").exists() else 0,"BYTES":(idx/"SYSTEM_MESSAGES.cdx").stat().st_size if (idx/"SYSTEM_MESSAGES.cdx").exists() else "","SHA256":sha(idx/"SYSTEM_MESSAGES.cdx")},
        {"ROLE":"candidate_text_cdx_target","PATH":rel(idx/"SYSTEM_MESSAGE_TEXT.cdx",repo),"EXISTS":1 if (idx/"SYSTEM_MESSAGE_TEXT.cdx").exists() else 0,"BYTES":(idx/"SYSTEM_MESSAGE_TEXT.cdx").stat().st_size if (idx/"SYSTEM_MESSAGE_TEXT.cdx").exists() else "","SHA256":sha(idx/"SYSTEM_MESSAGE_TEXT.cdx")},
    ]
    tags=[
        {"TABLE":"SYSTEM_MESSAGES","TAG":"SYMBOL","RATIONALE":"message lookup"},
        {"TABLE":"SYSTEM_MESSAGES","TAG":"STATUS","RATIONALE":"candidate/status review"},
        {"TABLE":"SYSTEM_MESSAGES","TAG":"SRC","RATIONALE":"source/provenance review"},
        {"TABLE":"SYSTEM_MESSAGE_TEXT","TAG":"SYMBOL","RATIONALE":"text lookup"},
        {"TABLE":"SYSTEM_MESSAGE_TEXT","TAG":"LOCALE","RATIONALE":"locale filtering"},
        {"TABLE":"SYSTEM_MESSAGE_TEXT","TAG":"STATUS","RATIONALE":"candidate/status review"},
    ]
    boundary=[
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"candidate CDX rebuild package only"},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"candidate index root only"},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no LMDB rebuild in 6.5.9"},
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no source mutation"},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no HELP mutation"},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"no CMDHELPCHK mutation"},
    ]
    wcsv(rep/"message_catalog_phase22ae_6_5_9_stage_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_candidate_inventory_before_v1.csv",inv,["ROLE","PATH","EXISTS","BYTES","SHA256"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_tag_plan_v1.csv",tags,["TABLE","TAG","RATIONALE"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_boundary_ledger_v1.csv",boundary,["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(rep/"message_catalog_phase22ae_6_5_9_stage_status_summary_v1.csv",[{
        "STATUS":status,"VALIDATION_ISSUES":"0" if status==OK else str(max(1,fail)),
        "PHASE22AE_6_5_8_GREEN":1 if s658.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_AND_READBACK_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_5_8_SAVEPOINT_PRESENT":1 if sp_ok else 0,
        "CANDIDATE_INDEX_ROOT":rel(idx,repo),"SCRIPT_PATH":script_rel,
        "CANDIDATE_CDX_REBUILD_AUTHORIZED":1 if a.allow_candidate_cdx_rebuild else 0,
        "CANDIDATE_LMDB_REBUILD_AUTHORIZED":0,"ACTIVE_PROMOTION_AUTHORIZED":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0,"SOURCE_FILES_MUTATED":0,
        "HELP_DATA_MUTATION_OBSERVED":0,"CMDHELPCHK_MUTATION_OBSERVED":0,
        "ERRORS":err,"NEXT_GATE":NEXT if status==OK else "HOLD_AND_FIX_PHASE22AE_6_5_9_STAGE",
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }],["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_8_GREEN","MSG_022AE_6_5_8_SAVEPOINT_PRESENT","CANDIDATE_INDEX_ROOT","SCRIPT_PATH","CANDIDATE_CDX_REBUILD_AUTHORIZED","CANDIDATE_LMDB_REBUILD_AUTHORIZED","ACTIVE_PROMOTION_AUTHORIZED","ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","ERRORS","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    print(status)
    print(f"  validation issues: {'0' if status==OK else str(max(1,fail))}")
    print(f"  Phase 22AE.6.5.8 green: {1 if s658.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_AND_READBACK_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.8 savepoint present: {1 if sp_ok else 0}")
    print(f"  candidate index root: {rel(idx,repo)}")
    print(f"  script path: {script_rel}")
    print(f"  candidate CDX rebuild authorized: {1 if a.allow_candidate_cdx_rebuild else 0}")
    print("  candidate LMDB rebuild authorized: 0")
    print("  active promotion authorized: 0")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT if status==OK else 'HOLD_AND_FIX_PHASE22AE_6_5_9_STAGE'}")
    print(f"  reports: {rep}")
    return 0 if status==OK else 2
if __name__=="__main__":
    raise SystemExit(main())
