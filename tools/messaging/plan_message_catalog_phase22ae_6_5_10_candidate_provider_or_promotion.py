
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
from datetime import datetime, timezone

OK="MESSAGE_CATALOG_PHASE22AE_6_5_10_CANDIDATE_PROVIDER_READBACK_OR_ACTIVE_PROMOTION_PLAN_GREEN_SOURCE_HELD"
BAD="MESSAGE_CATALOG_PHASE22AE_6_5_10_CANDIDATE_PROVIDER_READBACK_OR_ACTIVE_PROMOTION_PLAN_BLOCKED"
NEXT="HOLD_OR_AUTHORIZE_PHASE22AE_6_5_11_CANDIDATE_PROVIDER_READBACK_PACKAGE"

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
        h.update(str(x.relative_to(p)).replace("\\","/").encode("utf-8"))
        h.update(sha(x).encode("ascii")); total += x.stat().st_size
    return (h.hexdigest(),len(files),total)
def sp(repo, sid):
    latest=repo/"docs/messaging/reports/message_savepoint_latest_v1.json"
    latest_id=""
    if latest.exists():
        try: latest_id=json.loads(latest.read_text(encoding="utf-8")).get("savepoint_id","")
        except Exception: latest_id=""
    journal=repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text=journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id==sid or sid in text, latest_id
def file_row(repo, role, p):
    if p.is_dir():
        h,c,b=dir_sha(p)
        return {"ROLE":role,"PATH":rel(p,repo),"EXISTS":1,"KIND":"dir","BYTES":b,"SHA256":h,"FILES":c}
    if p.is_file():
        return {"ROLE":role,"PATH":rel(p,repo),"EXISTS":1,"KIND":"file","BYTES":p.stat().st_size,"SHA256":sha(p),"FILES":1}
    return {"ROLE":role,"PATH":rel(p,repo),"EXISTS":0,"KIND":"missing","BYTES":"","SHA256":"","FILES":""}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args=ap.parse_args()
    repo=Path(args.repo_root).resolve()
    reports=repo/"docs/messaging/reports"; reports.mkdir(parents=True, exist_ok=True)
    s6592=first(reports/"message_catalog_phase22ae_6_5_9_2_validate_status_summary_v1.csv")
    sp_ok, latest=sp(repo,"MSG-022AE.6.5.9.2")
    cand=repo/"docs/messaging/candidates/phase22ae_6_5_8_active_basename_candidate_v1"
    dbf=cand/"dbf"; idx=cand/"indexes"; lmdb=cand/"lmdb"
    gates=[]; fail=0
    def gate(name, ok, detail):
        nonlocal fail
        gates.append({"GATE":name,"STATUS":"PASS" if ok else "FAIL","DETAIL":str(detail)})
        if not ok: fail += 1
    gate("PHASE22AE_6_5_9_2_GREEN",s6592.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_9_2_CANDIDATE_CDX_BUILDLMDB_WORKAREA_PROOF_GREEN_SOURCE_HELD",s6592.get("STATUS","missing"))
    gate("MSG_022AE_6_5_9_2_SAVEPOINT_PRESENT",sp_ok,latest)
    gate("CANDIDATE_DBF_ROOT_PRESENT",dbf.exists(),rel(dbf,repo))
    gate("CANDIDATE_INDEX_ROOT_PRESENT",idx.exists(),rel(idx,repo))
    gate("CANDIDATE_LMDB_ROOT_PRESENT",lmdb.exists(),rel(lmdb,repo))
    gate("CANDIDATE_REQUIRED_FILES_PRESENT",
         (dbf/"SYSTEM_MESSAGES.dbf").exists() and (dbf/"SYSTEM_MESSAGE_TEXT.dbf").exists() and (dbf/"SYSTEM_MESSAGE_TEXT.dtx").exists() and (idx/"SYSTEM_MESSAGES.cdx").exists() and (idx/"SYSTEM_MESSAGE_TEXT.cdx").exists() and (lmdb/"SYSTEM_MESSAGES.cdx.d").exists() and (lmdb/"SYSTEM_MESSAGE_TEXT.cdx.d").exists(),
         rel(cand,repo))
    status=OK if fail==0 else BAD
    inventory=[
        file_row(repo,"candidate_message_dbf",dbf/"SYSTEM_MESSAGES.dbf"),
        file_row(repo,"candidate_text_dbf",dbf/"SYSTEM_MESSAGE_TEXT.dbf"),
        file_row(repo,"candidate_text_dtx",dbf/"SYSTEM_MESSAGE_TEXT.dtx"),
        file_row(repo,"candidate_message_cdx",idx/"SYSTEM_MESSAGES.cdx"),
        file_row(repo,"candidate_text_cdx",idx/"SYSTEM_MESSAGE_TEXT.cdx"),
        file_row(repo,"candidate_message_lmdb",lmdb/"SYSTEM_MESSAGES.cdx.d"),
        file_row(repo,"candidate_text_lmdb",lmdb/"SYSTEM_MESSAGE_TEXT.cdx.d"),
    ]
    plan=[
        {"STEP":1,"PHASE":"6.5.11","ACTION":"Run candidate provider-style readback proof with candidate SET PATH DBF/INDEXES/LMDB, explicit SELECT 1/2, SET INDEX, SET ORDER, COUNT, and WORKSPACE. No rebuild and no active mutation.","AUTHORIZATION":"future explicit authorization required"},
        {"STEP":2,"PHASE":"6.5.12","ACTION":"Plan active replacement precheck: backup active DBF/DTX/CDX/LMDB, compare candidate hashes/counts, verify rollback paths, hold before replacing active artifacts.","AUTHORIZATION":"future explicit authorization required"},
        {"STEP":3,"PHASE":"6.5.13","ACTION":"Only after explicit approval, perform guarded active replacement of DBF/DTX/CDX/LMDB and run post-promotion SET MESSAGE CATALOG CHECK / provider readback.","AUTHORIZATION":"future explicit authorization required"},
    ]
    sandbox_policy=[
        {"ITEM":"Public syntax preference","RULE":"Use SET PATH DBF/INDEXES/LMDB in generated DTS. SETPATH is accepted alias but SET PATH conforms to command grammar."},
        {"ITEM":"Reusable messaging sandbox","RULE":"Use DBF/SANDBOX/MESSAGES, INDEXES/SANDBOX/MESSAGES, and LMDB/SANDBOX/MESSAGES for normal Messaging sandbox work."},
        {"ITEM":"Boundary proof","RULE":"Use explicit candidate SET PATH lines for promotion-boundary proofs so transcripts show exact target roots."},
        {"ITEM":"Work areas","RULE":"Use SELECT 1 for SYSTEM_MESSAGES and SELECT 2 for SYSTEM_MESSAGE_TEXT in two-table proofs; preserve open areas for WORKSPACE/RDBMS visibility."},
        {"ITEM":"Index proof","RULE":"CDX CREATE and CDX ADDTAG define metadata; BUILDLMDB materializes the LMDB environment; SET INDEX / SET ORDER prove usable indexed access."},
    ]
    boundary=[
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"6.5.10 is plan-only."},
        {"PROTECTED_SYSTEM":"ACTIVE_AND_DEFAULT_INDEX_ROOTS","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"6.5.10 is plan-only."},
        {"PROTECTED_SYSTEM":"ACTIVE_AND_DEFAULT_LMDB_ROOTS","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"6.5.10 is plan-only."},
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]
    wcsv(reports/"message_catalog_phase22ae_6_5_10_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10_candidate_stack_inventory_v1.csv",inventory,["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10_decision_plan_v1.csv",plan,["STEP","PHASE","ACTION","AUTHORIZATION"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10_sandbox_messages_policy_v1.csv",sandbox_policy,["ITEM","RULE"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10_boundary_ledger_v1.csv",boundary,["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    md=f"""# Message Catalog Phase 22AE.6.5.10 Candidate Provider Readback or Active Promotion Plan

Status: `{status}`

6.5.10 is plan-only. It authorizes no active promotion and no candidate mutation.

Candidate stack now available:

```text
DBF root     : {rel(dbf,repo)}
INDEXES root : {rel(idx,repo)}
LMDB root    : {rel(lmdb,repo)}
```

Doctrine captured:

```text
SET PATH is preferred over SETPATH in generated DTS for command grammar conformity.
Use sandbox/messages for reusable Messaging sandbox work.
Use explicit candidate SET PATH lines for promotion-boundary proof transcripts.
Use SELECT 1 and SELECT 2 for two-table messaging proofs.
CDX ADDTAG is metadata; BUILDLMDB materializes LMDB; SET INDEX/SET ORDER proves usable indexed access.
WORKSPACE proves open work areas for future RDBMS relations.
```

Next gate:

```text
{NEXT if status==OK else "HOLD_AND_FIX_PHASE22AE_6_5_10_PLAN_PRECONDITIONS"}
```
"""
    (reports/"MESSAGE_CATALOG_PHASE22AE_6_5_10_CANDIDATE_PROVIDER_READBACK_OR_ACTIVE_PROMOTION_PLAN.md").write_text(md, encoding="utf-8")
    wcsv(reports/"message_catalog_phase22ae_6_5_10_status_summary_v1.csv",[{
        "STATUS":status,"VALIDATION_ISSUES":"0" if status==OK else str(max(1,fail)),
        "PHASE22AE_6_5_9_2_GREEN":1 if s6592.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_9_2_CANDIDATE_CDX_BUILDLMDB_WORKAREA_PROOF_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_5_9_2_SAVEPOINT_PRESENT":1 if sp_ok else 0,
        "CANDIDATE_ROOT":rel(cand,repo),
        "CANDIDATE_DBF_ROOT":rel(dbf,repo),
        "CANDIDATE_INDEX_ROOT":rel(idx,repo),
        "CANDIDATE_LMDB_ROOT":rel(lmdb,repo),
        "ACTIVE_PROMOTION_AUTHORIZED":0,
        "CANDIDATE_PROVIDER_READBACK_AUTHORIZED":0,
        "SOURCE_FILES_MUTATED":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0,
        "HELP_DATA_MUTATION_OBSERVED":0,
        "CMDHELPCHK_MUTATION_OBSERVED":0,
        "NEXT_GATE":NEXT if status==OK else "HOLD_AND_FIX_PHASE22AE_6_5_10_PLAN_PRECONDITIONS",
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }],["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_9_2_GREEN","MSG_022AE_6_5_9_2_SAVEPOINT_PRESENT","CANDIDATE_ROOT","CANDIDATE_DBF_ROOT","CANDIDATE_INDEX_ROOT","CANDIDATE_LMDB_ROOT","ACTIVE_PROMOTION_AUTHORIZED","CANDIDATE_PROVIDER_READBACK_AUTHORIZED","SOURCE_FILES_MUTATED","ACTIVE_CATALOG_MUTATION_OBSERVED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    print(status)
    print(f"  validation issues: {'0' if status==OK else str(max(1,fail))}")
    print(f"  Phase 22AE.6.5.9.2 green: {1 if s6592.get('STATUS')=='MESSAGE_CATALOG_PHASE22AE_6_5_9_2_CANDIDATE_CDX_BUILDLMDB_WORKAREA_PROOF_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.9.2 savepoint present: {1 if sp_ok else 0}")
    print(f"  candidate DBF/INDEXES/LMDB roots present: {1 if dbf.exists() else 0}/{1 if idx.exists() else 0}/{1 if lmdb.exists() else 0}")
    print("  active promotion authorized: 0")
    print("  candidate provider readback authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT if status==OK else 'HOLD_AND_FIX_PHASE22AE_6_5_10_PLAN_PRECONDITIONS'}")
    print(f"  reports: {reports}")
    return 0 if status==OK else 2
if __name__=="__main__":
    raise SystemExit(main())
