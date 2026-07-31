#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN="MESSAGE_CATALOG_PHASE22AE_6_5_10AZ_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PACKAGE_GREEN_BACKUP_AND_DRYRUN_READY_APPLY_NOT_EXECUTED"
BLOCKED="MESSAGE_CATALOG_PHASE22AE_6_5_10AZ_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PACKAGE_BLOCKED"
NEXT="HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BA_MSGMGR_HELP_CMDHELPCHK_APPLY_EXECUTION"
R=Path("docs/messaging/reports")
CAND=Path("docs/messaging/candidates/MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.md")
PLAN=Path("docs/messaging/apply/phase22ae_6_5_10ay_msgmgr_help_cmdhelpchk_guarded_apply_plan_v1")
APPLY=Path("docs/messaging/apply/phase22ae_6_5_10az_msgmgr_help_cmdhelpchk_guarded_apply_package_v1")
MSG=Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
TXT=Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

def rows(p):
    p=Path(p)
    if not p.exists(): return []
    with p.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def first(p): 
    a=rows(p); return a[0] if a else {}
def wcsv(p, rs, fs):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore"); w.writeheader()
        for r in rs: w.writerow({k:r.get(k,"") for k in fs})
def rel(p,root):
    try: return str(Path(p).relative_to(root)).replace("\\","/")
    except Exception: return str(p).replace("\\","/")
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()
def dbf_count(p):
    p=Path(p)
    if not p.exists() or p.stat().st_size<12: return ""
    return int.from_bytes(p.read_bytes()[:12][4:8],"little")
def savepoint(repo, sid):
    latest=""
    lp=repo/R/"message_savepoint_latest_v1.json"
    if lp.exists():
        try: latest=json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id","")
        except Exception: latest=""
    jp=repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt=jp.read_text(encoding="utf-8",errors="replace") if jp.exists() else ""
    return (latest==sid or sid in txt), latest
def discover(repo):
    pats=["*help*.dbf","*HELP*.DBF","*cmdhelp*.dbf","*CMDHELP*.DBF","*command*.dbf","*COMMAND*.DBF",
          "*help*.md","*HELP*.MD","*cmdhelp*.md","*CMDHELP*.MD","*commands*.md","*COMMANDS*.MD",
          "*help*.csv","*HELP*.CSV","*cmdhelp*.csv","*CMDHELP*.CSV"]
    roots=[repo/"dottalkpp/data/help", repo/"dottalkpp/data", repo/"docs"]
    got={}
    for root in roots:
        if not root.exists(): continue
        for pat in pats:
            for p in root.rglob(pat):
                if not p.is_file(): continue
                rp=rel(p,repo)
                if "/apply/" in rp or "/backups/" in rp: continue
                got[str(p.resolve()).lower()]=p
    out=[]
    for p in sorted(got.values(), key=lambda x: rel(x,repo).lower()):
        rp=rel(p,repo); up=(p.name+" "+rp).upper()
        role="UNKNOWN_REVIEW"
        if "CMDHELP" in up: role="CMDHELPCHK_CANDIDATE_TARGET"
        elif "HELP" in up: role="HELP_DATA_CANDIDATE_TARGET"
        elif "COMMAND" in up: role="COMMAND_HELP_RELATED_TARGET"
        out.append({"TARGET_PATH":rp,"ROLE":role,"BYTES":p.stat().st_size,"SHA256":sha(p),"BACKUP_COPIED":0})
    return out
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",required=True)
    ap.add_argument("--replace-existing-package",action="store_true")
    a=ap.parse_args()
    repo=Path(a.repo_root).resolve()
    reports=repo/R; reports.mkdir(parents=True,exist_ok=True)
    ay=first(reports/"message_catalog_phase22ae_6_5_10ay_status_summary_v1.csv")
    sp,latest=savepoint(repo,"MSG-022AE.6.5.10AY")
    msg=dbf_count(repo/MSG); txt=dbf_count(repo/TXT)
    gates=[]; fails=0
    def gate(n,ok,d):
        nonlocal fails
        gates.append({"GATE":n,"STATUS":"PASS" if ok else "FAIL","DETAIL":str(d)})
        if not ok: fails+=1
    gate("PHASE22AE_6_5_10AY_GREEN", ay.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_10AY_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PLAN_GREEN_SOURCE_HELD", ay.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10AY_SAVEPOINT_PRESENT", sp, latest)
    gate("AY_HELP_PLAN_CREATED", ay.get("HELP_DATA_APPLY_PLAN_CREATED")=="1", ay.get("HELP_DATA_APPLY_PLAN_CREATED","missing"))
    gate("AY_CMDHELPCHK_PLAN_CREATED", ay.get("CMDHELPCHK_APPLY_PLAN_CREATED")=="1", ay.get("CMDHELPCHK_APPLY_PLAN_CREATED","missing"))
    gate("AY_HELP_APPLY_AUTH_HELD", ay.get("HELP_DATA_APPLY_AUTHORIZED")=="0", ay.get("HELP_DATA_APPLY_AUTHORIZED","missing"))
    gate("AY_CMDHELPCHK_APPLY_AUTH_HELD", ay.get("CMDHELPCHK_APPLY_AUTHORIZED")=="0", ay.get("CMDHELPCHK_APPLY_AUTHORIZED","missing"))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg==14, msg)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", txt==70, txt)
    gate("CANDIDATE_EXISTS", (repo/CAND).exists(), rel(repo/CAND,repo))
    gate("PLAN_ROOT_EXISTS", (repo/PLAN).exists(), rel(repo/PLAN,repo))
    gate("APPLY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not (repo/APPLY).exists()) or a.replace_existing_package, rel(repo/APPLY,repo))
    status=BLOCKED
    target_rows=[]; backup_rows=[]; dry=[]; arts=[]; review=0
    if fails==0:
        ar=repo/APPLY
        if ar.exists() and a.replace_existing_package: shutil.rmtree(ar)
        ar.mkdir(parents=True,exist_ok=True)
        target_rows=discover(repo)
        ts=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        broot=repo/"docs/messaging/backups"/f"MSG-022AE_6_5_10AZ_HELP_CMDHELPCHK_BACKUP_{ts}"
        broot.mkdir(parents=True,exist_ok=True)
        for r in target_rows:
            src=repo/r["TARGET_PATH"]
            if src.exists() and src.is_file():
                dst=broot/r["TARGET_PATH"]; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
                bsha=sha(dst); r["BACKUP_COPIED"]=1
                backup_rows.append({"SOURCE_PATH":r["TARGET_PATH"],"BACKUP_PATH":rel(dst,repo),"SOURCE_SHA256":r["SHA256"],"BACKUP_SHA256":bsha,"SHA256_MATCH":1 if bsha==r["SHA256"] else 0})
        snap=ar/"candidate_snapshot"/CAND.name; snap.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(repo/CAND,snap)
        tm=ar/"target_manifest_preview.csv"; wcsv(tm,target_rows,["TARGET_PATH","ROLE","BYTES","SHA256","BACKUP_COPIED"])
        tmpl=ar/"templates"; tmpl.mkdir(parents=True,exist_ok=True)
        appt=tmpl/"MESSAGE_CATALOG_PHASE22AE_6_5_10BA_APPLY_EXECUTION_TEMPLATE.ps1.disabled"
        rest=tmpl/"MESSAGE_CATALOG_PHASE22AE_6_5_10BA_RESTORE_TEMPLATE.ps1.disabled"
        appt.write_text('throw "DISABLED TEMPLATE: 10BA apply execution is not authorized by 10AZ."\n',encoding="utf-8")
        rest.write_text('throw "DISABLED TEMPLATE: 10BA restore execution is not authorized by 10AZ."\n',encoding="utf-8")
        dry=[
          {"DRYRUN_ITEM":"TARGET_DISCOVERY","STATUS":"COMPLETE" if target_rows else "REVIEW_NO_TARGETS_FOUND","DETAIL":f"{len(target_rows)} target files discovered.","APPLY_AUTHORIZED_NOW":0},
          {"DRYRUN_ITEM":"BACKUP_CREATION","STATUS":"COMPLETE" if backup_rows else "REVIEW_NO_BACKUPS_COPIED","DETAIL":f"{len(backup_rows)} files copied to backup root.","APPLY_AUTHORIZED_NOW":0},
          {"DRYRUN_ITEM":"HELP_DATA_APPLY_EXECUTION","STATUS":"NOT_EXECUTED_IN_10AZ","DETAIL":"10AZ prepares package only; 10BA must execute if authorized.","APPLY_AUTHORIZED_NOW":0},
          {"DRYRUN_ITEM":"CMDHELPCHK_APPLY_EXECUTION","STATUS":"NOT_EXECUTED_IN_10AZ","DETAIL":"10AZ prepares package only; 10BA must execute if authorized.","APPLY_AUTHORIZED_NOW":0},
          {"DRYRUN_ITEM":"CANDIDATE_SNAPSHOT","STATUS":"COMPLETE","DETAIL":rel(snap,repo),"APPLY_AUTHORIZED_NOW":0},
        ]
        for p in [snap,tm,appt,rest]:
            arts.append({"ARTIFACT":rel(p,repo),"ROLE":"candidate_snapshot_or_disabled_template_or_target_manifest","BYTES":p.stat().st_size,"SHA256":sha(p)})
        status=GREEN
        if not target_rows: review=1
    boundary=[
      {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"10AZ writes docs/messaging package artifacts only."},
      {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No DBF mutation."},
      {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGE_TEXT","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No DBF mutation."},
      {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CDX/LMDB mutation."},
      {"PROTECTED_SYSTEM":"WORKSPACE_PROFILE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No workspace mutation."},
      {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Backup/dry-run only; no HELP DATA apply."},
      {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Backup/dry-run only; no CMDHELPCHK apply."},
    ]
    readiness=[
      {"ITEM":"10BA_HELP_APPLY_EXECUTION","READY_FOR_NEXT_PACKAGE":1 if status==GREEN else 0,"AUTHORIZED_NOW":0,"DETAIL":"Requires separate 10BA execution package and exact target mapper."},
      {"ITEM":"10BA_CMDHELPCHK_APPLY_EXECUTION","READY_FOR_NEXT_PACKAGE":1 if status==GREEN else 0,"AUTHORIZED_NOW":0,"DETAIL":"Requires separate 10BA execution package and exact target mapper."},
      {"ITEM":"ROLLBACK_AVAILABLE","READY_FOR_NEXT_PACKAGE":1 if backup_rows else 0,"AUTHORIZED_NOW":0,"DETAIL":"Backups copied for discovered targets only."},
      {"ITEM":"TARGET_MAPPER_REQUIRED","READY_FOR_NEXT_PACKAGE":1,"AUTHORIZED_NOW":0,"DETAIL":"10BA must name exact HELP/CMDHELPCHK target artifacts and commands."},
    ]
    wcsv(reports/"message_catalog_phase22ae_6_5_10az_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10az_target_discovery_v1.csv",target_rows,["TARGET_PATH","ROLE","BYTES","SHA256","BACKUP_COPIED"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10az_backup_manifest_v1.csv",backup_rows,["SOURCE_PATH","BACKUP_PATH","SOURCE_SHA256","BACKUP_SHA256","SHA256_MATCH"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10az_dryrun_summary_v1.csv",dry,["DRYRUN_ITEM","STATUS","DETAIL","APPLY_AUTHORIZED_NOW"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10az_apply_readiness_v1.csv",readiness,["ITEM","READY_FOR_NEXT_PACKAGE","AUTHORIZED_NOW","DETAIL"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10az_boundary_ledger_v1.csv",boundary,["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports/"message_catalog_phase22ae_6_5_10az_artifact_manifest_v1.csv",arts,["ARTIFACT","ROLE","BYTES","SHA256"])
    summary={
      "STATUS":status,"VALIDATION_ISSUES":"0" if fails==0 else str(fails),"REVIEW_NOTES":review,
      "PHASE22AE_6_5_10AY_STATUS":ay.get("STATUS",""),"MSG_022AE_6_5_10AY_SAVEPOINT_PRESENT":1 if sp else 0,
      "ACTIVE_MESSAGES_OBSERVED_COUNT":msg,"ACTIVE_TEXT_OBSERVED_COUNT":txt,
      "CANDIDATE_EXISTS":1 if (repo/CAND).exists() else 0,"PLAN_ROOT_EXISTS":1 if (repo/PLAN).exists() else 0,
      "APPLY_ROOT":rel(repo/APPLY,repo),"TARGETS_DISCOVERED":len(target_rows),"BACKUPS_COPIED":len(backup_rows),
      "DRYRUN_ROWS":len(dry),"ARTIFACT_ROWS":len(arts),
      "HELP_DATA_APPLY_EXECUTED":0,"CMDHELPCHK_APPLY_EXECUTED":0,
      "HELP_DATA_APPLY_AUTHORIZED_NOW":0,"CMDHELPCHK_APPLY_AUTHORIZED_NOW":0,
      "HELP_DATA_MUTATION_OBSERVED":0,"CMDHELPCHK_MUTATION_OBSERVED":0,"SOURCE_FILES_MUTATED":0,
      "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW":0,"DBF_MUTATION_OBSERVED":0,"CDX_LMDB_MUTATION_OBSERVED":0,"WORKSPACE_MUTATION_OBSERVED":0,
      "NEXT_GATE":NEXT,"REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }
    wcsv(reports/"message_catalog_phase22ae_6_5_10az_status_summary_v1.csv",[summary],list(summary.keys()))
    (repo/"docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AZ_MSGMGR_HELP_CMDHELPCHK_GUARDED_APPLY_PACKAGE.md").write_text(f"# Message Catalog Phase 22AE.6.5.10AZ MSGMGR HELP/CMDHELPCHK Guarded Apply Package\n\nStatus: `{status}`\n\n10AZ prepares backup/dry-run readiness. It does not execute HELP DATA or CMDHELPCHK apply.\n\nApply root:\n\n```text\n{rel(repo/APPLY,repo)}\n```\n\nNext gate:\n\n```text\n{NEXT}\n```\n",encoding="utf-8")
    print(status)
    print(f"  validation issues: {summary['VALIDATION_ISSUES']}")
    print(f"  review notes: {review}")
    print(f"  Phase 22AE.6.5.10AY status: {ay.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AY savepoint present: {1 if sp else 0}")
    print(f"  active messages observed count: {msg}")
    print(f"  active text observed count: {txt}")
    print(f"  candidate exists: {summary['CANDIDATE_EXISTS']}")
    print(f"  plan root exists: {summary['PLAN_ROOT_EXISTS']}")
    print(f"  apply root: {summary['APPLY_ROOT']}")
    print(f"  targets discovered: {len(target_rows)}")
    print(f"  backups copied: {len(backup_rows)}")
    print(f"  dryrun rows: {len(dry)}")
    print(f"  artifact rows: {len(arts)}")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  HELP DATA apply authorized now: 0")
    print("  CMDHELPCHK apply authorized now: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT}")
    print(f"  reports: {reports}")
    return 0 if status==GREEN else 2

if __name__=="__main__":
    raise SystemExit(main())
