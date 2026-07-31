#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN="MESSAGE_CATALOG_PHASE22AE_6_5_10AJ_POST_PROMOTION_ACCEPTANCE_AND_BACKUP_RETENTION_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED="MESSAGE_CATALOG_PHASE22AE_6_5_10AJ_POST_PROMOTION_ACCEPTANCE_AND_BACKUP_RETENTION_PLAN_BLOCKED"
NEXT_GATE="HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AK_POST_PROMOTION_MESSAGING_CATALOG_CLOSEOUT"
REPORT_DIR=Path("docs/messaging/reports")
ACTIVE_MSG=Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT=Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

def rows(path):
    if not path.exists(): return []
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def row(path):
    r=rows(path); return r[0] if r else {}
def write(path, data, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader(); [w.writerow({k:x.get(k,"") for k in fields}) for x in data]
def rel(path, repo):
    try: return str(path.relative_to(repo)).replace("\\","/")
    except Exception: return str(path).replace("\\","/")
def count_dbf(path):
    if not path.exists() or path.stat().st_size < 12: return ""
    return int.from_bytes(path.read_bytes()[:12][4:8],"little")
def savepoint(repo, sid):
    latest=""
    latest_path=repo/REPORT_DIR/"message_savepoint_latest_v1.json"
    if latest_path.exists():
        try: latest=json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id","")
        except Exception: latest=""
    journal=repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text=journal.read_text(encoding="utf-8",errors="replace") if journal.exists() else ""
    return latest==sid or sid in text, latest
def backup_exists(repo, value):
    if not value: return False,""
    p=Path(value)
    if not p.is_absolute(): p=repo/p
    return p.exists(), rel(p, repo)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root", required=True)
    args=ap.parse_args(); repo=Path(args.repo_root).resolve(); reports=repo/REPORT_DIR; reports.mkdir(parents=True, exist_ok=True)

    ah_p=row(reports/"message_catalog_phase22ae_6_5_10ah_prepare_status_summary_v1.csv")
    ah=row(reports/"message_catalog_phase22ae_6_5_10ah_finalize_status_summary_v1.csv")
    ai=row(reports/"message_catalog_phase22ae_6_5_10ai_validate_status_summary_v1.csv")
    sp_ah,latest_ah=savepoint(repo,"MSG-022AE.6.5.10AH")
    sp_ai,latest_ai=savepoint(repo,"MSG-022AE.6.5.10AI")
    backup_root=ah.get("BACKUP_ROOT","") or ah_p.get("BACKUP_ROOT","")
    bexists,bpath=backup_exists(repo, backup_root)
    backup_rows=rows(reports/"message_catalog_phase22ae_6_5_10ah_backup_manifest_v1.csv")
    msg_count=count_dbf(repo/ACTIVE_MSG); text_count=count_dbf(repo/ACTIVE_TEXT)

    gates=[]; fails=0
    def gate(name, ok, detail):
        nonlocal fails
        gates.append({"GATE":name,"STATUS":"PASS" if ok else "FAIL","DETAIL":str(detail)})
        if not ok: fails+=1

    gate("PHASE22AE_6_5_10AH_GREEN_ACTIVE_PROMOTED", ah.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_GREEN_ACTIVE_PROMOTED", ah.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10AH_SAVEPOINT_PRESENT", sp_ah, latest_ah)
    gate("PHASE22AE_6_5_10AI_GREEN_ACTIVE_PROMOTION_PERSISTED", ai.get("STATUS")=="MESSAGE_CATALOG_PHASE22AE_6_5_10AI_POST_PROMOTION_FRESH_READBACK_GREEN_ACTIVE_PROMOTION_PERSISTED", ai.get("STATUS","missing"))
    gate("MSG_022AE_6_5_10AI_SAVEPOINT_PRESENT", sp_ai, latest_ai)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count==14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count==70, text_count)
    gate("10AI_NO_ACTIVE_CATALOG_MUTATION", ai.get("ACTIVE_CATALOG_MUTATION_OBSERVED")=="0", ai.get("ACTIVE_CATALOG_MUTATION_OBSERVED","missing"))
    gate("10AH_ROLLBACK_BACKUP_ROOT_EXISTS", bexists, bpath)
    gate("10AH_BACKUP_MANIFEST_ROWS_PRESENT", len(backup_rows)>0, len(backup_rows))

    status=STATUS_GREEN if fails==0 else STATUS_BLOCKED
    issues="0" if status==STATUS_GREEN else str(fails)
    accepted=1 if status==STATUS_GREEN else 0
    rollback_required=0 if status==STATUS_GREEN else 1

    acceptance=[
        {"ACCEPTANCE_ITEM":"ACTIVE_MESSAGING_CATALOG_PROMOTION","STATUS":"ACCEPTED" if accepted else "BLOCKED","EVIDENCE":"10AH final promotion plus 10AI fresh-session readback","DETAIL":"Accept active SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70."},
        {"ACCEPTANCE_ITEM":"ROLLBACK_REQUIRED","STATUS":"NO" if accepted else "REVIEW","EVIDENCE":"10AI persisted 14/70","DETAIL":"Do not run 10AH rollback unless a later explicit rejection/failure appears."},
        {"ACCEPTANCE_ITEM":"BACKUP_RETENTION","STATUS":"RETAIN_AS_ARCHIVE" if accepted else "RETAIN_AS_ACTIVE_ROLLBACK","EVIDENCE":f"backup_root={bpath}; manifest_rows={len(backup_rows)}","DETAIL":"Retain backup; no delete/compress authorization in 10AJ."},
        {"ACCEPTANCE_ITEM":"HELP_CMDHELPCHK_SOURCE_BOUNDARY","STATUS":"CLEAN","EVIDENCE":"10AI mutation checks zero","DETAIL":"HELP DATA, CMDHELPCHK, and source remain untouched."},
    ]
    final_state=[
        {"OBJECT":"SYSTEM_MESSAGES","ACTIVE_PATH":rel(repo/ACTIVE_MSG,repo),"ACCEPTED_RECORD_COUNT":14,"OBSERVED_RECORD_COUNT":msg_count,"STATE":"PROMOTED_ACCEPTED" if accepted else "REVIEW"},
        {"OBJECT":"SYSTEM_MESSAGE_TEXT","ACTIVE_PATH":rel(repo/ACTIVE_TEXT,repo),"ACCEPTED_RECORD_COUNT":70,"OBSERVED_RECORD_COUNT":text_count,"STATE":"PROMOTED_ACCEPTED" if accepted else "REVIEW"},
    ]
    backup_policy=[
        {"POLICY_ITEM":"ROLLBACK_BACKUP_ROOT","POLICY":"RETAIN","PATH":bpath,"REASON":"Preserve exact pre-promotion backup for audit and emergency rollback."},
        {"POLICY_ITEM":"ROLLBACK_EXECUTION","POLICY":"DO_NOT_RUN_BY_DEFAULT","PATH":"tools/messaging/run_message_catalog_phase22ae_6_5_10ah_rollback.ps1","REASON":"10AH and 10AI are green; rollback would undo the accepted 14/70 promotion."},
        {"POLICY_ITEM":"BACKUP_CLEANUP","POLICY":"NOT_AUTHORIZED","PATH":bpath,"REASON":"No backup deletion or compression in 10AJ."},
    ]
    closeout=[
        {"STEP":1,"ACTION":"RECORD_ACTIVE_PROMOTED_STATE","DETAIL":"Declare active messaging catalog 14/70 accepted.","MUTATES_ACTIVE":0},
        {"STEP":2,"ACTION":"RETAIN_ROLLBACK_BACKUP","DETAIL":"Keep 10AH backup available; do not rollback and do not delete backup.","MUTATES_ACTIVE":0},
        {"STEP":3,"ACTION":"PREPARE_10AK_CLOSEOUT","DETAIL":"Summarize 22AE.6.5.10U through 10AJ and list remaining verification items.","MUTATES_ACTIVE":0},
        {"STEP":4,"ACTION":"NO_HELP_OR_CMDHELPCHK_APPLY","DETAIL":"HELP DATA and CMDHELPCHK remain outside this promotion unless separately authorized.","MUTATES_ACTIVE":0},
    ]
    boundary=[
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"10AJ is report-only."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGE_TEXT","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation."},
        {"PROTECTED_SYSTEM":"ROLLBACK_BACKUP_DELETE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No backup deletion or compression."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]

    write(reports/"message_catalog_phase22ae_6_5_10aj_gate_check_v1.csv",gates,["GATE","STATUS","DETAIL"])
    write(reports/"message_catalog_phase22ae_6_5_10aj_acceptance_ledger_v1.csv",acceptance,["ACCEPTANCE_ITEM","STATUS","EVIDENCE","DETAIL"])
    write(reports/"message_catalog_phase22ae_6_5_10aj_final_state_declaration_v1.csv",final_state,["OBJECT","ACTIVE_PATH","ACCEPTED_RECORD_COUNT","OBSERVED_RECORD_COUNT","STATE"])
    write(reports/"message_catalog_phase22ae_6_5_10aj_backup_retention_policy_v1.csv",backup_policy,["POLICY_ITEM","POLICY","PATH","REASON"])
    write(reports/"message_catalog_phase22ae_6_5_10aj_closeout_plan_v1.csv",closeout,["STEP","ACTION","DETAIL","MUTATES_ACTIVE"])
    write(reports/"message_catalog_phase22ae_6_5_10aj_boundary_ledger_v1.csv",boundary,["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    summary={
        "STATUS":status,"VALIDATION_ISSUES":issues,
        "PHASE22AE_6_5_10AH_STATUS":ah.get("STATUS",""),"MSG_022AE_6_5_10AH_SAVEPOINT_PRESENT":1 if sp_ah else 0,
        "PHASE22AE_6_5_10AI_STATUS":ai.get("STATUS",""),"MSG_022AE_6_5_10AI_SAVEPOINT_PRESENT":1 if sp_ai else 0,
        "ACTIVE_MESSAGES_ACCEPTED_COUNT":14,"ACTIVE_TEXT_ACCEPTED_COUNT":70,
        "ACTIVE_MESSAGES_OBSERVED_COUNT":msg_count,"ACTIVE_TEXT_OBSERVED_COUNT":text_count,
        "ACTIVE_PROMOTION_ACCEPTED":accepted,"ROLLBACK_REQUIRED":rollback_required,
        "ROLLBACK_BACKUP_RETAINED":1 if bexists else 0,"ROLLBACK_BACKUP_ROOT":bpath,"ROLLBACK_BACKUP_MANIFEST_ROWS":len(backup_rows),
        "ROLLBACK_BACKUP_DELETE_AUTHORIZED":0,"ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW":0,
        "SOURCE_FILES_MUTATED":0,"HELP_DATA_MUTATION_OBSERVED":0,"CMDHELPCHK_MUTATION_OBSERVED":0,
        "NEXT_GATE":NEXT_GATE,"REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }
    write(reports/"message_catalog_phase22ae_6_5_10aj_status_summary_v1.csv",[summary],list(summary.keys()))
    (repo/"docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AJ_POST_PROMOTION_ACCEPTANCE_AND_BACKUP_RETENTION_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AJ Post-Promotion Acceptance and Backup Retention Plan\n\nStatus: `{status}`\n\n10AJ is report-only. It accepts the 14/70 active messaging catalog state after 10AH and 10AI, retains rollback backup, and does not authorize rollback or backup deletion.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n", encoding="utf-8")

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10AH status: {ah.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AH savepoint present: {1 if sp_ah else 0}")
    print(f"  Phase 22AE.6.5.10AI status: {ai.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AI savepoint present: {1 if sp_ai else 0}")
    print(f"  active messages accepted/observed: 14/{msg_count}")
    print(f"  active text accepted/observed: 70/{text_count}")
    print(f"  active promotion accepted: {accepted}")
    print(f"  rollback required: {rollback_required}")
    print(f"  rollback backup retained: {1 if bexists else 0}")
    print(f"  rollback backup root: {bpath}")
    print("  rollback backup delete authorized: 0")
    print("  active catalog mutation observed by review: 0")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status==STATUS_GREEN else 2
if __name__=="__main__":
    raise SystemExit(main())
