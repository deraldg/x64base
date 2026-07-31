from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CY_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CY_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_VALIDATION_GREEN_MAPPED_CANDIDATES_VALIDATED_APPLY_HELD"
CY_SAVEPOINT = "MSG-022AE.6.5.10CY-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CZ_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_STAGING_GREEN_DTS_AND_MAPPED_INPUTS_STAGED_APPLY_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CZ_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_STAGING_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_RUN_CZ_B_DOTTALK_HELP_CMDHELPCHK_CANDIDATE_TABLE_MATERIALIZATION_DTS_AND_CAPTURE_TRANSCRIPT"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cz_b_help_cmdhelpchk_candidate_table_native_materialization_staging_v1"
CX_OUT_REL = "docs/messaging/apply/phase22ae_6_5_10cx_b_help_cmdhelpchk_candidate_mapping_staging_v1/candidate_outputs"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def csv_rows(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def csv_one(path: Path) -> dict:
    rows = csv_rows(path)
    return rows[0] if rows else {}

def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})

def has_journal(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest_id(repo: Path) -> str:
    try:
        data = json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
        return data.get("savepoint_id", data.get("savepoint", ""))
    except Exception:
        return ""

def copy_csv(src: Path, dst: Path) -> int:
    if not src.exists():
        return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return 1

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--replace-existing-staging", action="store_true")
    parser.add_argument("--allow-missing-cy-b-savepoint", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL
    cx_outputs = repo / CX_OUT_REL

    if out.exists() and args.replace_existing_staging:
        shutil.rmtree(out)

    cy = csv_one(reports / "message_catalog_phase22ae_6_5_10cy_b_status_summary_v1.csv")
    cy_green = int(cy.get("STATUS", "") == CY_GREEN)
    cy_savepoint = has_journal(repo, CY_SAVEPOINT)

    dbf_dir = out / "dbf"
    idx_dir = out / "indexes"
    lmdb_dir = out / "lmdb"
    inputs_dir = out / "candidate_inputs"
    scripts_dir = out / "scripts"
    runlog_dir = out / "runlog"

    source_help = cx_outputs / "HELP_DATA_CANDIDATE_ROWS.csv"
    source_cmd = cx_outputs / "CMDHELPCHK_CANDIDATE_ROWS.csv"
    source_gate = cx_outputs / "MESSAGE_APPLY_GATE_EVIDENCE.csv"

    target_help = inputs_dir / "HELPDATA_CZ.csv"
    target_cmd = inputs_dir / "CMDHELP_CZ.csv"
    target_gate = inputs_dir / "GATEEV_CZ.csv"

    pre = [
        {"check_id":"cy_b_status_green","value":cy_green,"expected":1,"status":"PASS" if cy_green else "FAIL"},
        {"check_id":"cy_b_savepoint_present","value":cy_savepoint,"expected":1,"status":"PASS" if cy_savepoint else ("REVIEW" if args.allow_missing_cy_b_savepoint else "FAIL")},
        {"check_id":"cx_help_candidate_output_exists","value":int(source_help.exists()),"expected":1,"status":"PASS" if source_help.exists() else "FAIL"},
        {"check_id":"cx_cmdhelpchk_candidate_output_exists","value":int(source_cmd.exists()),"expected":1,"status":"PASS" if source_cmd.exists() else "FAIL"},
        {"check_id":"cx_gate_evidence_output_exists","value":int(source_gate.exists()),"expected":1,"status":"PASS" if source_gate.exists() else "FAIL"},
        {"check_id":"cz_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_staging) else "FAIL"},
    ]

    validation = sum(1 for row in pre if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CZ_B_STAGING_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    for d in [dbf_dir, idx_dir, lmdb_dir, inputs_dir, scripts_dir, runlog_dir, reports]:
        d.mkdir(parents=True, exist_ok=True)

    copied_help = copy_csv(source_help, target_help)
    copied_cmd = copy_csv(source_cmd, target_cmd)
    copied_gate = copy_csv(source_gate, target_gate)

    help_rows = len(csv_rows(target_help))
    cmd_rows = len(csv_rows(target_cmd))
    gate_rows = len(csv_rows(target_gate))

    dts = scripts_dir / "cz_b_help_cmdhelpchk_candidate_table_materialization_AFTER_REVIEW.dts"
    write_text(dts, f"""SETPATH DBF TO {dbf_dir}
SETPATH INDEXES TO {idx_dir}
SETPATH LMDB TO {lmdb_dir}

CREATE X64 HELPDATA_CZ (MESSAGE_ID C(40), LOCALE_ID C(16), HELP_KEY C(80), HELP_TEXT C(240), SOURCE_PHASE C(40), REVIEW_STATUS C(40), APPLY_READY L, APPLY_SCOPE C(40))
IMPORT {target_help}
COUNT
FIELDS
STRUCT
DISPLAY
SMARTLIST ALL
CDX CREATE
CDX ADDTAG MESSAGE_ID
CDX ADDTAG HELP_KEY
BUILDLMDB CLEAN YES
SET INDEX TO HELPDATA_CZ.cdx
SET ORDER TO TAG MESSAGE_ID
SMARTLIST ALL
SET ORDER TO TAG HELP_KEY
SMARTLIST ALL
CLOSE

CREATE X64 CMDHELP_CZ (COMMAND_NAME C(40), HELP_KEY C(80), CHECK_ID C(40), CHECK_STATUS C(80), MUTATION_FLAG L, REVIEW_STATUS C(40), APPLY_READY L, APPLY_SCOPE C(40))
IMPORT {target_cmd}
COUNT
FIELDS
STRUCT
DISPLAY
SMARTLIST ALL
CDX CREATE
CDX ADDTAG COMMAND_NAME
CDX ADDTAG CHECK_ID
BUILDLMDB CLEAN YES
SET INDEX TO CMDHELP_CZ.cdx
SET ORDER TO TAG COMMAND_NAME
SMARTLIST ALL
SET ORDER TO TAG CHECK_ID
SMARTLIST ALL
CLOSE

CREATE X64 GATEEV_CZ (GATE_ID C(40), GATE_STATUS C(80), MUTATION_FLAG L, GATE_NOTES C(180), APPLY_SCOPE C(40))
IMPORT {target_gate}
COUNT
FIELDS
STRUCT
DISPLAY
SMARTLIST ALL
CDX CREATE
CDX ADDTAG GATE_ID
BUILDLMDB CLEAN YES
SET INDEX TO GATEEV_CZ.cdx
SET ORDER TO TAG GATE_ID
SMARTLIST ALL
CLOSE

WORKSPACE
AREA

""")

    manual_ps1 = scripts_dir / "run_cz_b_help_cmdhelpchk_candidate_table_materialization_AFTER_REVIEW.ps1"
    write_text(manual_ps1, f"""param([Parameter(Mandatory=$true)][string]$RepoRoot)

$DtsPath = Join-Path $RepoRoot "{dts.relative_to(repo)}"
$Transcript = Join-Path $RepoRoot "docs\\messaging\\apply\\phase22ae_6_5_10cz_b_help_cmdhelpchk_candidate_table_native_materialization_staging_v1\\runlog\\CZ_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_MATERIALIZATION_TRANSCRIPT.txt"

Write-Host "[CZ-B] Run this DTS inside DotTalk++ and capture transcript:"
Write-Host "DOTSCRIPT $DtsPath OUT $Transcript"
Write-Host ""
Write-Host "[CZ-B] This script intentionally does not launch DotTalk++ or execute the DTS."
""")

    staged_outputs = [
        {"artifact":"HELPDATA_CZ.csv","source":str(source_help),"target":str(target_help),"copied":copied_help,"rows":help_rows,"role":"mapped HELP DATA candidate input"},
        {"artifact":"CMDHELP_CZ.csv","source":str(source_cmd),"target":str(target_cmd),"copied":copied_cmd,"rows":cmd_rows,"role":"mapped CMDHELPCHK candidate input"},
        {"artifact":"GATEEV_CZ.csv","source":str(source_gate),"target":str(target_gate),"copied":copied_gate,"rows":gate_rows,"role":"mapped gate evidence candidate input"},
        {"artifact":"cz_b_help_cmdhelpchk_candidate_table_materialization_AFTER_REVIEW.dts","source":"","target":str(dts),"copied":1,"rows":"","role":"manual DotTalk++ proof script"},
        {"artifact":"run_cz_b_help_cmdhelpchk_candidate_table_materialization_AFTER_REVIEW.ps1","source":"","target":str(manual_ps1),"copied":1,"rows":"","role":"manual run instruction script"},
    ]

    boundary = [
        {"boundary":"DTS executed by package","value":0,"status":"PASS"},
        {"boundary":"DBF created by package","value":0,"status":"PASS"},
        {"boundary":"CDX/LMDB created by package","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CZ-B","value":0,"status":"PASS"},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10cz_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cz_b_staged_artifacts_v1.csv", ["artifact","source","target","copied","rows","role"], staged_outputs)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cz_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    manifest = {
        "phase":"22AE.6.5.10CZ-B",
        "status":status,
        "candidate_tables":["HELPDATA_CZ","CMDHELP_CZ","GATEEV_CZ"],
        "candidate_input_rows":{"HELPDATA_CZ":help_rows,"CMDHELP_CZ":cmd_rows,"GATEEV_CZ":gate_rows},
        "dts_script":str(dts),
        "package_executes_dts":False,
        "active_apply_executed":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10cz_b_manifest_v1.json", json.dumps(manifest, indent=2))

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10CZ-B",
        "CY_B_STATUS_GREEN":cy_green,
        "CY_B_SAVEPOINT_PRESENT":cy_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CZ_B":latest_id(repo),
        "HELPDATA_CZ_INPUT_ROWS":help_rows,
        "CMDHELP_CZ_INPUT_ROWS":cmd_rows,
        "GATEEV_CZ_INPUT_ROWS":gate_rows,
        "STAGED_ARTIFACTS":len(staged_outputs),
        "MANUAL_RUN_ARTIFACTS":2,
        "DTS_EXECUTED_BY_PACKAGE":0,
        "DBF_CREATED_BY_PACKAGE":0,
        "CDX_LMDB_CREATED_BY_PACKAGE":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "LATEST_POINTER_CHANGED_BY_CZ_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cz_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report = f"""# Phase 22AE.6.5.10CZ-B HELP/CMDHELPCHK Candidate Table Native Materialization Staging

- Status: {status}
- Validation issues: {validation}
- CY-B status green: {cy_green}
- CY-B savepoint present: {cy_savepoint}
- HELPDATA_CZ input rows: {help_rows}
- CMDHELP_CZ input rows: {cmd_rows}
- GATEEV_CZ input rows: {gate_rows}
- DTS executed by package: 0
- DBF created by package: 0
- CDX/LMDB created by package: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Latest pointer changed by CZ-B: 0
- Next gate: {next_gate}
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CZ_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_STAGING.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CZ_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_STAGING.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CY-B status green: {cy_green}")
    print(f"  CY-B savepoint present: {cy_savepoint}")
    print(f"  HELPDATA_CZ input rows: {help_rows}")
    print(f"  CMDHELP_CZ input rows: {cmd_rows}")
    print(f"  GATEEV_CZ input rows: {gate_rows}")
    print("  staged artifacts:", len(staged_outputs))
    print("  manual-run artifacts: 2")
    print("  DTS executed by package: 0")
    print("  DBF created by package: 0")
    print("  CDX/LMDB created by package: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  latest pointer changed by CZ-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
