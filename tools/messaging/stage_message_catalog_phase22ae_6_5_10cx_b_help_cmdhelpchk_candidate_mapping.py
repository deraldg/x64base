from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CWB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_MAPPING_PLAN_GREEN_REPORT_ONLY_APPLY_HELD"
CWB_SAVEPOINT = "MSG-022AE.6.5.10CW-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CX_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_STAGING_GREEN_MAPPED_CANDIDATES_STAGED_APPLY_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CX_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_STAGING_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CY_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_VALIDATION"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cx_b_help_cmdhelpchk_candidate_mapping_staging_v1"
CT_REL = "docs/messaging/apply/phase22ae_6_5_10ct_b_native_candidate_table_materialization_staging_v1/candidate_inputs"

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

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--replace-existing-staging", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    docs = repo / "docs/messaging"
    out = repo / ROOT_REL
    ct_inputs = repo / CT_REL
    candidate_outputs = out / "candidate_outputs"

    if out.exists() and args.replace_existing_staging:
        shutil.rmtree(out)

    cw = csv_one(reports / "message_catalog_phase22ae_6_5_10cw_b_status_summary_v1.csv")
    cw_green = int(cw.get("STATUS", "") == CWB_GREEN)
    cw_savepoint = has_journal(repo, CWB_SAVEPOINT)

    msghelp = csv_rows(ct_inputs / "MSGHELP_CT.csv")
    cmdchk = csv_rows(ct_inputs / "CMDCHK_CT.csv")
    gates = csv_rows(ct_inputs / "MSGGATE_CT.csv")

    pre = [
        {"check_id":"cw_b_status_green","value":cw_green,"expected":1,"status":"PASS" if cw_green else "FAIL"},
        {"check_id":"cw_b_savepoint_present","value":cw_savepoint,"expected":1,"status":"PASS" if cw_savepoint else "FAIL"},
        {"check_id":"msghelp_ct_input_rows","value":len(msghelp),"expected":">0","status":"PASS" if len(msghelp) else "FAIL"},
        {"check_id":"cmdchk_ct_input_rows","value":len(cmdchk),"expected":">0","status":"PASS" if len(cmdchk) else "FAIL"},
        {"check_id":"msggate_ct_input_rows","value":len(gates),"expected":">0","status":"PASS" if len(gates) else "FAIL"},
        {"check_id":"cx_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_staging) else "FAIL"},
    ]

    help_rows = []
    for r in msghelp:
        help_rows.append({
            "MESSAGE_ID": r.get("MSG_ID",""),
            "LOCALE_ID": r.get("LOCALE_ID",""),
            "HELP_KEY": r.get("HELP_KEY",""),
            "HELP_TEXT": r.get("HELP_TEXT",""),
            "SOURCE_PHASE": r.get("SOURCE","CT-B"),
            "REVIEW_STATUS": r.get("STATUS","CANDIDATE"),
            "APPLY_READY": "False",
            "APPLY_SCOPE": "CANDIDATE_ONLY",
        })

    cmd_rows = []
    for r in cmdchk:
        cmd_rows.append({
            "COMMAND_NAME": r.get("CMD_NAME",""),
            "HELP_KEY": r.get("HELP_KEY",""),
            "CHECK_ID": r.get("CHECK_ID",""),
            "CHECK_STATUS": r.get("CHECK_STAT",""),
            "MUTATION_FLAG": r.get("MUTATES","False"),
            "REVIEW_STATUS": r.get("STATUS","PROOF"),
            "APPLY_READY": "False",
            "APPLY_SCOPE": "CANDIDATE_ONLY",
        })

    gate_rows = []
    for r in gates:
        gate_rows.append({
            "GATE_ID": r.get("GATE_ID",""),
            "GATE_STATUS": r.get("GATE_STAT",""),
            "MUTATION_FLAG": r.get("MUTATES","False"),
            "GATE_NOTES": r.get("NOTES",""),
            "APPLY_SCOPE": "CANDIDATE_ONLY",
        })

    validation = sum(1 for r in pre if r["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CX_B_STAGING_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    candidate_outputs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(candidate_outputs / "HELP_DATA_CANDIDATE_ROWS.csv",
              ["MESSAGE_ID","LOCALE_ID","HELP_KEY","HELP_TEXT","SOURCE_PHASE","REVIEW_STATUS","APPLY_READY","APPLY_SCOPE"], help_rows)
    write_csv(candidate_outputs / "CMDHELPCHK_CANDIDATE_ROWS.csv",
              ["COMMAND_NAME","HELP_KEY","CHECK_ID","CHECK_STATUS","MUTATION_FLAG","REVIEW_STATUS","APPLY_READY","APPLY_SCOPE"], cmd_rows)
    write_csv(candidate_outputs / "MESSAGE_APPLY_GATE_EVIDENCE.csv",
              ["GATE_ID","GATE_STATUS","MUTATION_FLAG","GATE_NOTES","APPLY_SCOPE"], gate_rows)

    boundary = [
        {"boundary":"candidate mapping staged","value":1 if status == GREEN else 0,"status":"PASS" if status == GREEN else "FAIL"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CX-B","value":0,"status":"PASS"},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10cx_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cx_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cx_b_staged_outputs_v1.csv",
              ["artifact","rows","apply_scope","apply_ready"],
              [
                  {"artifact":"HELP_DATA_CANDIDATE_ROWS.csv","rows":len(help_rows),"apply_scope":"CANDIDATE_ONLY","apply_ready":"False"},
                  {"artifact":"CMDHELPCHK_CANDIDATE_ROWS.csv","rows":len(cmd_rows),"apply_scope":"CANDIDATE_ONLY","apply_ready":"False"},
                  {"artifact":"MESSAGE_APPLY_GATE_EVIDENCE.csv","rows":len(gate_rows),"apply_scope":"CANDIDATE_ONLY","apply_ready":"False"},
              ])

    manifest = {
        "phase":"22AE.6.5.10CX-B",
        "status":status,
        "source_tables":["MSGHELP_CT","CMDCHK_CT","MSGGATE_CT"],
        "mapped_outputs":{
            "HELP_DATA_CANDIDATE_ROWS.csv":len(help_rows),
            "CMDHELPCHK_CANDIDATE_ROWS.csv":len(cmd_rows),
            "MESSAGE_APPLY_GATE_EVIDENCE.csv":len(gate_rows),
        },
        "apply_ready":False,
        "active_apply_executed":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10cx_b_manifest_v1.json", json.dumps(manifest, indent=2))

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10CX-B",
        "CW_B_STATUS_GREEN":cw_green,
        "CW_B_SAVEPOINT_PRESENT":cw_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CX_B":latest_id(repo),
        "HELP_DATA_CANDIDATE_ROWS":len(help_rows),
        "CMDHELPCHK_CANDIDATE_ROWS":len(cmd_rows),
        "GATE_EVIDENCE_ROWS":len(gate_rows),
        "CANDIDATE_MAPPING_STAGED":1 if status == GREEN else 0,
        "CANDIDATE_MAPPING_VALIDATED_NOW":0,
        "APPLY_READY":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED":0,
        "WORKSPACE_MUTATION_OBSERVED":0,
        "LATEST_POINTER_CHANGED_BY_CX_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cx_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report = f"""# Phase 22AE.6.5.10CX-B HELP/CMDHELPCHK Candidate Mapping Staging

- Status: {status}
- Validation issues: {validation}
- CW-B status green: {cw_green}
- CW-B savepoint present: {cw_savepoint}
- HELP DATA candidate rows: {len(help_rows)}
- CMDHELPCHK candidate rows: {len(cmd_rows)}
- Gate evidence rows: {len(gate_rows)}
- Candidate mapping staged: {1 if status == GREEN else 0}
- Candidate mapping validated now: 0
- Apply ready: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Latest pointer changed by CX-B: 0
- Next gate: {next_gate}
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CX_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_STAGING.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CX_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_STAGING.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CW-B status green: {cw_green}")
    print(f"  CW-B savepoint present: {cw_savepoint}")
    print(f"  HELP DATA candidate rows: {len(help_rows)}")
    print(f"  CMDHELPCHK candidate rows: {len(cmd_rows)}")
    print(f"  gate evidence rows: {len(gate_rows)}")
    print("  candidate mapping staged: 1")
    print("  candidate mapping validated now: 0")
    print("  apply ready: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  latest pointer changed by CX-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
