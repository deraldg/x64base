#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, shutil
from pathlib import Path
from datetime import datetime, timezone

OK="LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS_SOURCE_PATCH_APPLIED_BUILD_HELD"
BAD="LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS_SOURCE_PATCH_BLOCKED"
NEXT="BUILD_AND_RUN_MSGMGR_PROVIDER_STATUS_SMOKE_THEN_VALIDATE"
CMD=Path("src/cli/cmd_msgmgr.cpp")
SMOKE=Path("docs/locale/scripts/LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS_SMOKE.dts")
ANCHOR='        << "  active message get   : SET MESSAGE CATALOG GET\\n"'
INSERT='        << "  provider mode        : active_dbf\\n"\n        << "  message DBF root     : dottalkpp/data/messaging\\n"\n        << "  message index root   : dottalkpp/data/indexes/messaging\\n"\n        << "  message LMDB root    : dottalkpp/data/lmdb/messaging\\n"'
SMOKE_TEXT='* LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS_SMOKE.dts\n* MSGMGR provider/status surface smoke.\n* Boundary: read-only command status; no DBF/CDX/LMDB mutation.\n\nMSGMGR STATUS\nMSGMGR CHECK\n\n'

def csv_rows(p):
    if not p.exists(): return []
    with p.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def first(p):
    r=csv_rows(p); return r[0] if r else {}
def write_csv(p, rows, fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in fields})
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576), b""): h.update(b)
    return h.hexdigest()
def rel(p,repo):
    try: return p.relative_to(repo).as_posix()
    except Exception: return str(p)
def backup(path,broot,repo,out):
    if path.exists():
        dest=broot/rel(path,repo); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,dest)
        out.append({"SOURCE_PATH":rel(path,repo),"BACKUP_PATH":rel(dest,repo),"BYTES":dest.stat().st_size,"SHA256":sha(dest),"ACTION":"BACKUP_EXISTING_FILE"})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",required=True)
    ap.add_argument("--allow-source-mutation",action="store_true")
    a=ap.parse_args()
    repo=Path(a.repo_root).resolve(); reports=repo/"docs/locale/reports"; reports.mkdir(parents=True,exist_ok=True)
    p23t=first(reports/"locale_phase23t_msgmgr_message_schema_status_validation_summary_v1.csv")
    p23s=first(reports/"locale_phase23s_message_schema_validation_status_summary_v1.csv")
    gates=[]; failures=0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE":name,"STATUS":"PASS" if ok else "FAIL","DETAIL":detail})
        if not ok: failures += 1
    gate("OPERATOR_ALLOWED_SOURCE_MUTATION", a.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE23T_GREEN", p23t.get("STATUS")=="LOCALE_PHASE23T_MSGMGR_MESSAGE_SCHEMA_STATUS_BUILD_SMOKE_GREEN", p23t.get("STATUS",""))
    gate("PHASE23S_GREEN", p23s.get("STATUS")=="LOCALE_PHASE23S_MESSAGE_CATALOG_ACTIVE_SCHEMA_VALIDATED_GREEN", p23s.get("STATUS",""))
    gate("ACTIVE_MESSAGE_SCHEMA_PRESENT", (repo/"dottalkpp/data/schemas/messaging/message_catalog.dtschema").exists(), "message_catalog.dtschema")
    gate("ACTIVE_LOCALE_SCHEMA_PRESENT", (repo/"dottalkpp/data/schemas/locale/locale_spine.dtschema").exists(), "locale_spine.dtschema")
    gate("CMD_MSGMGR_PRESENT", (repo/CMD).exists(), str(CMD))
    muts=[]; backups=[]; patch="not_attempted"; status=BAD
    if failures==0:
        broot=repo/"docs/locale/backups"/("LOC-023U_MSGMGR_PROVIDER_STATUS_BACKUP_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        backup(repo/CMD,broot,repo,backups); backup(repo/SMOKE,broot,repo,backups)
        text=(repo/CMD).read_text(encoding="utf-8",errors="replace")
        if "provider mode        : active_dbf" in text:
            new=text; patch="already_present"
        elif ANCHOR in text:
            new=text.replace(ANCHOR, ANCHOR+"\n"+INSERT, 1); patch="inserted_after_active_message_get"
        else:
            new=text; patch="anchor_missing"; failures += 1
        if failures==0:
            if new!=text:
                (repo/CMD).write_text(new,encoding="utf-8",newline="\n")
                muts.append({"TARGET_PATH":rel(repo/CMD,repo),"ACTION":"UPDATE_MSGMGR_STATUS_"+patch,"BYTES":(repo/CMD).stat().st_size,"SHA256":sha(repo/CMD)})
            (repo/SMOKE).parent.mkdir(parents=True,exist_ok=True)
            (repo/SMOKE).write_text(SMOKE_TEXT,encoding="utf-8",newline="\n")
            muts.append({"TARGET_PATH":rel(repo/SMOKE,repo),"ACTION":"CREATE_OR_REPLACE_PROVIDER_STATUS_SMOKE","BYTES":(repo/SMOKE).stat().st_size,"SHA256":sha(repo/SMOKE)})
            status=OK
    write_csv(reports/"locale_phase23u_msgmgr_provider_status_apply_summary_v1.csv",[{"STATUS":status,"VALIDATION_ISSUES":"0" if status==OK else str(failures),"SOURCE_MUTATION_AUTHORIZED":1 if a.allow_source_mutation else 0,"SOURCE_FILES_MUTATED":len([m for m in muts if m["TARGET_PATH"].startswith("src/")]),"DOCS_LOCALE_FILES_MUTATED":len([m for m in muts if m["TARGET_PATH"].startswith("docs/")]),"BACKUP_ROWS":len(backups),"PATCH_STATUS":patch,"BUILD_EXECUTED":0,"RUNTIME_SMOKE_EXECUTED":0,"NEXT_GATE":NEXT,"REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")}],["STATUS","VALIDATION_ISSUES","SOURCE_MUTATION_AUTHORIZED","SOURCE_FILES_MUTATED","DOCS_LOCALE_FILES_MUTATED","BACKUP_ROWS","PATCH_STATUS","BUILD_EXECUTED","RUNTIME_SMOKE_EXECUTED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    write_csv(reports/"locale_phase23u_msgmgr_provider_status_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    write_csv(reports/"locale_phase23u_msgmgr_provider_status_mutation_inventory_v1.csv",muts,["TARGET_PATH","ACTION","BYTES","SHA256"])
    write_csv(reports/"locale_phase23u_msgmgr_provider_status_backup_inventory_v1.csv",backups,["SOURCE_PATH","BACKUP_PATH","BYTES","SHA256","ACTION"])
    write_csv(reports/"locale_phase23u_msgmgr_provider_status_boundary_ledger_v1.csv",[{"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":len([m for m in muts if m["TARGET_PATH"].startswith("src/")]),"DETAIL":"Authorized narrow MSGMGR provider/status text wiring only."},{"PROTECTED_SYSTEM":"ACTIVE_SCHEMA_DBF_CDX_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active schema/DBF/CDX/LMDB mutation."},{"PROTECTED_SYSTEM":"HELP_CMDHELPCHK_MANUALGEN_DATADICT_SELFDOC","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No protected consumer mutation."}],["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    (repo/"docs/locale/LOCALE_PHASE23U_MSGMGR_PROVIDER_STATUS.md").write_text(f"# Locale Phase 23U - MSGMGR Provider Status\n\nStatus: `{status}`\n\nAdds read-only provider root status lines to MSGMGR.\n\nNext gate: `{NEXT}`\n",encoding="utf-8")
    print(status)
    print(f"  validation issues: {'0' if status==OK else failures}")
    print(f"  source mutation authorized: {1 if a.allow_source_mutation else 0}")
    print(f"  source files mutated: {len([m for m in muts if m['TARGET_PATH'].startswith('src/')])}")
    print(f"  docs locale files mutated: {len([m for m in muts if m['TARGET_PATH'].startswith('docs/')])}")
    print(f"  backup rows: {len(backups)}")
    print(f"  patch status: {patch}")
    print("  build executed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT}")
    print(f"  reports: {reports}")
    return 0 if status==OK else 2
if __name__=="__main__": raise SystemExit(main())
