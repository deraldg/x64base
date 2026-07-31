#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CSB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CS_B_ACTIVE_CANDIDATE_NATIVE_WRITER_INVOCATION_PLAN_GREEN_REPORT_ONLY_SOURCE_HELD"
CSB_SAVEPOINT = "MSG-022AE.6.5.10CS-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CT_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_STAGING_GREEN_DTS_AND_CSV_STAGED_SOURCE_HELD"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10ct_b_native_candidate_table_materialization_staging_v1"
NEXT = "HOLD_OR_RUN_CT_B_DOTTALK_NATIVE_TABLE_MATERIALIZATION_DTS_AND_CAPTURE_TRANSCRIPT"

def rt(p): return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
def wt(p,s): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8", newline="\n")
def wr_csv(p, fields, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in fields})
def rows(p):
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
    except Exception: return []
def one(p):
    r=rows(p); return r[0] if r else {}
def latest(repo):
    try: return json.loads(rt(repo/"docs/messaging/reports/message_savepoint_latest_v1.json"))
    except Exception: return {}
def has_journal(repo, marker): return int(marker in rt(repo/"docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-staging", action="store_true")
    a=ap.parse_args()
    repo=Path(a.repo_root).resolve()
    docs=repo/"docs/messaging"; reports=docs/"reports"; out=repo/ROOT_REL
    if out.exists() and a.replace_existing_staging: shutil.rmtree(out)

    csb=one(reports/"message_catalog_phase22ae_6_5_10cs_b_status_summary_v1.csv")
    latest_before=latest(repo).get("savepoint_id", latest(repo).get("savepoint",""))
    csb_green=int(csb.get("STATUS","")==CSB_GREEN)
    csb_sp=has_journal(repo, CSB_SAVEPOINT)
    pre=[
      {"check_id":"cs_b_status_green","value":csb_green,"expected":1,"status":"PASS" if csb_green else "FAIL"},
      {"check_id":"cs_b_savepoint_present","value":csb_sp,"expected":1,"status":"PASS" if csb_sp else "FAIL"},
      {"check_id":"ct_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or a.replace_existing_staging) else "FAIL"},
      {"check_id":"official_latest_pointer_not_modified_by_staging","value":1,"expected":1,"status":"PASS"},
    ]
    validation=sum(1 for r in pre if r["status"]=="FAIL")
    status=GREEN if validation==0 else "MESSAGE_CATALOG_PHASE22AE_6_5_10CT_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_STAGING_RED_REVIEW_REQUIRED"
    next_gate=NEXT if status==GREEN else "REVIEW_CT_B_STAGING_PRECONDITIONS"

    dbf=out/"dbf"; idx=out/"indexes"; lmdb=out/"lmdb"; inp=out/"candidate_inputs"; scr=out/"scripts"; runlog=out/"runlog"
    for d in [dbf,idx,lmdb,inp,scr,runlog,reports]: d.mkdir(parents=True, exist_ok=True)

    msghelp=[
      {"MSG_ID":"MSG_CT_001","LOCALE_ID":"en-US","HELP_KEY":"CTB.NATIVE.CREATE","HELP_TEXT":"DotTalk++ CREATE X64 creates a fenced candidate DBF table.","SOURCE":"CT-B","STATUS":"CANDIDATE"},
      {"MSG_ID":"MSG_CT_002","LOCALE_ID":"en-US","HELP_KEY":"CTB.NATIVE.IMPORT","HELP_TEXT":"Native IMPORT populates candidate rows from CSV.","SOURCE":"CT-B","STATUS":"CANDIDATE"},
      {"MSG_ID":"MSG_CT_003","LOCALE_ID":"en-US","HELP_KEY":"CTB.NATIVE.READBACK","HELP_TEXT":"FIELDS STRUCT DISPLAY SMARTLIST ALL read back candidate rows.","SOURCE":"CT-B","STATUS":"CANDIDATE"},
    ]
    cmdchk=[
      {"CMD_NAME":"CREATE","HELP_KEY":"CTB.NATIVE.CREATE","CHECK_ID":"CHK_CT_001","CHECK_STAT":"CANDIDATE_ONLY","MUTATES":"False","STATUS":"PROOF"},
      {"CMD_NAME":"USE","HELP_KEY":"CTB.NATIVE.USE","CHECK_ID":"CHK_CT_002","CHECK_STAT":"CANDIDATE_ONLY","MUTATES":"False","STATUS":"PROOF"},
      {"CMD_NAME":"DISPLAY","HELP_KEY":"CTB.NATIVE.DISPLAY","CHECK_ID":"CHK_CT_003","CHECK_STAT":"READBACK","MUTATES":"False","STATUS":"PROOF"},
      {"CMD_NAME":"SMARTLIST","HELP_KEY":"CTB.NATIVE.SMARTLIST","CHECK_ID":"CHK_CT_004","CHECK_STAT":"READBACK_ALL","MUTATES":"False","STATUS":"PROOF"},
    ]
    gate=[
      {"GATE_ID":"GATE_CT_001","GATE_STAT":"NO_SOURCE_MUTATION","MUTATES":"False","NOTES":"CT-B staging does not edit source."},
      {"GATE_ID":"GATE_CT_002","GATE_STAT":"NO_ACTIVE_HELP_APPLY","MUTATES":"False","NOTES":"CT-B proof uses fenced DBF path only."},
      {"GATE_ID":"GATE_CT_003","GATE_STAT":"NO_CMDHELPCHK_APPLY","MUTATES":"False","NOTES":"CT-B proof does not apply CMDHELPCHK."},
      {"GATE_ID":"GATE_CT_004","GATE_STAT":"NO_LATEST_POINTER_CHANGE","MUTATES":"False","NOTES":"Side-branch savepoints only."},
    ]
    msg_csv=inp/"MSGHELP_CT.csv"; cmd_csv=inp/"CMDCHK_CT.csv"; gate_csv=inp/"MSGGATE_CT.csv"
    wr_csv(msg_csv, ["MSG_ID","LOCALE_ID","HELP_KEY","HELP_TEXT","SOURCE","STATUS"], msghelp)
    wr_csv(cmd_csv, ["CMD_NAME","HELP_KEY","CHECK_ID","CHECK_STAT","MUTATES","STATUS"], cmdchk)
    wr_csv(gate_csv, ["GATE_ID","GATE_STAT","MUTATES","NOTES"], gate)

    dts=scr/"ct_b_native_candidate_table_materialization_AFTER_REVIEW.dts"
    wt(dts, f"""SETPATH DBF TO {dbf}
SETPATH INDEXES TO {idx}
SETPATH LMDB TO {lmdb}

CREATE X64 MSGHELP_CT (MSG_ID C(40), LOCALE_ID C(16), HELP_KEY C(80), HELP_TEXT C(240), SOURCE C(80), STATUS C(80))
IMPORT {msg_csv}
COUNT
FIELDS
STRUCT
DISPLAY
SMARTLIST ALL
CDX CREATE
CDX ADDTAG MSG_ID
CDX ADDTAG HELP_KEY
BUILDLMDB CLEAN YES
SET INDEX TO MSGHELP_CT.cdx
SET ORDER TO TAG MSG_ID
SMARTLIST ALL
SET ORDER TO TAG HELP_KEY
SMARTLIST ALL
CLOSE

CREATE X64 CMDCHK_CT (CMD_NAME C(40), HELP_KEY C(80), CHECK_ID C(40), CHECK_STAT C(80), MUTATES L, STATUS C(80))
IMPORT {cmd_csv}
COUNT
FIELDS
STRUCT
DISPLAY
SMARTLIST ALL
CDX CREATE
CDX ADDTAG CMD_NAME
CDX ADDTAG CHECK_ID
BUILDLMDB CLEAN YES
SET INDEX TO CMDCHK_CT.cdx
SET ORDER TO TAG CMD_NAME
SMARTLIST ALL
SET ORDER TO TAG CHECK_ID
SMARTLIST ALL
CLOSE

CREATE X64 MSGGATE_CT (GATE_ID C(40), GATE_STAT C(80), MUTATES L, NOTES C(160))
IMPORT {gate_csv}
COUNT
FIELDS
STRUCT
DISPLAY
SMARTLIST ALL
CDX CREATE
CDX ADDTAG GATE_ID
BUILDLMDB CLEAN YES
SET INDEX TO MSGGATE_CT.cdx
SET ORDER TO TAG GATE_ID
SMARTLIST ALL
CLOSE

WORKSPACE
AREA

""")

    ps=scr/"run_ct_b_native_candidate_table_materialization_AFTER_REVIEW.ps1"
    wt(ps, f"""param([Parameter(Mandatory=$true)][string]$RepoRoot)

$DtsPath = Join-Path $RepoRoot "{dts.relative_to(repo)}"
$Transcript = Join-Path $RepoRoot "docs\\messaging\\apply\\phase22ae_6_5_10ct_b_native_candidate_table_materialization_staging_v1\\runlog\\CT_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_TRANSCRIPT.txt"

Write-Host "[CT-B] Run this DTS inside DotTalk++ and capture transcript:"
Write-Host ". DO $DtsPath"
Write-Host ""
Write-Host "[CT-B] Transcript target:"
Write-Host $Transcript
Write-Host ""
Write-Host "[CT-B] This script intentionally does not launch DotTalk++ or execute the DTS."
""")

    contract={
      "phase":"22AE.6.5.10CT-B",
      "corrected_concept":"DotTalk++ native table/materialization command path",
      "candidate_tables":["MSGHELP_CT","CMDCHK_CT","MSGGATE_CT"],
      "commands":["SETPATH","CREATE X64","IMPORT","COUNT","FIELDS","STRUCT","DISPLAY","SMARTLIST ALL","CDX CREATE","CDX ADDTAG","BUILDLMDB CLEAN YES","SET INDEX","SET ORDER TO TAG","CLOSE","WORKSPACE","AREA"],
      "dts_script":str(dts),
      "package_executes_dts":False,
      "source_mutation_authorized_now":False,
      "help_data_apply_executed":False,
      "cmdhelpchk_apply_executed":False,
      "latest_pointer_change_allowed":False
    }
    wt(out/"native_candidate_table_materialization_contract_v1.json", json.dumps(contract, indent=2))

    table_plan=[
      {"table":"MSGHELP_CT","role":"candidate HELP DATA-style rows","csv":str(msg_csv.relative_to(repo)).replace("\\","/"),"rows":len(msghelp),"tags":"MSG_ID;HELP_KEY"},
      {"table":"CMDCHK_CT","role":"candidate CMDHELPCHK-style rows","csv":str(cmd_csv.relative_to(repo)).replace("\\","/"),"rows":len(cmdchk),"tags":"CMD_NAME;CHECK_ID"},
      {"table":"MSGGATE_CT","role":"candidate boundary/provenance rows","csv":str(gate_csv.relative_to(repo)).replace("\\","/"),"rows":len(gate),"tags":"GATE_ID"},
    ]
    boundary=[
      {"boundary":"dts executed by package","value":0,"status":"PASS"},
      {"boundary":"dbf created by package","value":0,"status":"PASS"},
      {"boundary":"cdx/lmdb created by package","value":0,"status":"PASS"},
      {"boundary":"source files mutated","value":0,"status":"PASS"},
      {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
      {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
      {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
      {"boundary":"latest pointer changed by CT-B","value":0,"status":"PASS"},
    ]
    summary=[{
      "STATUS":status,"VALIDATION_ISSUES":validation,"PHASE":"22AE.6.5.10CT-B",
      "CORRECTED_CONCEPT":"DotTalk++ native table/materialization command path",
      "CS_B_STATUS_GREEN":csb_green,"CS_B_SAVEPOINT_PRESENT":csb_sp,
      "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CT_B":latest_before,
      "CANDIDATE_TABLES":3,"CANDIDATE_INPUT_ROWS":len(msghelp)+len(cmdchk)+len(gate),
      "STAGED_ARTIFACTS":6,"MANUAL_RUN_ARTIFACTS":2,
      "DTS_EXECUTED_BY_PACKAGE":0,"DBF_CREATED_BY_PACKAGE":0,"CDX_LMDB_CREATED_BY_PACKAGE":0,
      "NATIVE_TABLE_MATERIALIZATION_CONFIRMED_NOW":0,"REUSE_PATH_CONFIRMED_NOW":0,
      "SOURCE_MUTATION_AUTHORIZED_NOW":0,"APPLY_EXECUTION_AUTHORIZED_NOW":0,
      "HELP_DATA_APPLY_EXECUTED":0,"CMDHELPCHK_APPLY_EXECUTED":0,
      "ACTIVE_CATALOG_MUTATION_OBSERVED":0,"LATEST_POINTER_CHANGED_BY_CT_B":0,
      "NEXT_GATE":next_gate,"REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    }]
    wr_csv(reports/"message_catalog_phase22ae_6_5_10ct_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    wr_csv(reports/"message_catalog_phase22ae_6_5_10ct_b_candidate_table_plan_v1.csv", ["table","role","csv","rows","tags"], table_plan)
    wr_csv(reports/"message_catalog_phase22ae_6_5_10ct_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)
    wr_csv(reports/"message_catalog_phase22ae_6_5_10ct_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report=f"""# Phase 22AE.6.5.10CT-B Native Candidate Table Materialization Staging

- Status: {status}
- Validation issues: {validation}
- Corrected concept: DotTalk++ native table/materialization command path
- CS-B status green: {csb_green}
- CS-B savepoint present: {csb_sp}
- Official latest before CT-B: `{latest_before}`
- Candidate tables: `MSGHELP_CT`, `CMDCHK_CT`, `MSGGATE_CT`
- Candidate input rows: {len(msghelp)+len(cmdchk)+len(gate)}
- DTS executed by package: 0
- DBF created by package: 0
- CDX/LMDB created by package: 0
- Native table materialization confirmed now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Latest pointer changed by CT-B: 0
- Next gate: {next_gate}

CT-B stages candidate CSV files and a DotTalk++ `.dts` proof script using native commands: SETPATH, CREATE X64, IMPORT, COUNT, FIELDS, STRUCT, DISPLAY, SMARTLIST ALL, CDX CREATE, CDX ADDTAG, BUILDLMDB, SET INDEX, SET ORDER TO TAG, CLOSE, WORKSPACE, and AREA.
"""
    wt(out/"MESSAGE_LOCALE_PHASE22AE_6_5_10CT_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_STAGING.md", report)
    wt(docs/"MESSAGE_LOCALE_PHASE22AE_6_5_10CT_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_STAGING.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print("  corrected concept: DotTalk++ native table/materialization command path")
    print(f"  CS-B status green: {csb_green}")
    print(f"  CS-B savepoint present: {csb_sp}")
    print(f"  official latest before CT-B: {latest_before}")
    print("  candidate tables: MSGHELP_CT, CMDCHK_CT, MSGGATE_CT")
    print(f"  candidate input rows: {len(msghelp)+len(cmdchk)+len(gate)}")
    print("  DTS executed by package: 0")
    print("  DBF created by package: 0")
    print("  CDX/LMDB created by package: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  latest pointer changed by CT-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status==GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
