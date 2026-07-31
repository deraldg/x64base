from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CVB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CV_B_NATIVE_MATERIALIZATION_REUSE_DECISION_PACKAGE_GREEN_NATIVE_TABLE_PATH_CONFIRMED_APPLY_HELD"
CVB_SAVEPOINT = "MSG-022AE.6.5.10CV-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_MAPPING_PLAN_GREEN_REPORT_ONLY_APPLY_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CW_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_MAPPING_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CX_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_STAGING"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cw_b_help_cmdhelpchk_candidate_table_mapping_plan_v1"

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
    parser.add_argument("--replace-existing-plan", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL
    if out.exists() and args.replace_existing_plan:
        shutil.rmtree(out)

    cv = csv_one(reports / "message_catalog_phase22ae_6_5_10cv_b_status_summary_v1.csv")
    cv_green = int(cv.get("STATUS", "") == CVB_GREEN)
    cv_savepoint = has_journal(repo, CVB_SAVEPOINT)
    native_accepted = int(str(cv.get("NATIVE_TABLE_MATERIALIZATION_ACCEPTED", "0")) == "1")

    pre = [
        {"check_id":"cv_b_status_green","value":cv_green,"expected":1,"status":"PASS" if cv_green else "FAIL"},
        {"check_id":"cv_b_savepoint_present","value":cv_savepoint,"expected":1,"status":"PASS" if cv_savepoint else "FAIL"},
        {"check_id":"native_table_materialization_accepted","value":native_accepted,"expected":1,"status":"PASS" if native_accepted else "FAIL"},
        {"check_id":"cw_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
    ]

    table_map = [
        {"candidate_table":"MSGHELP_CT","candidate_role":"candidate HELP DATA-style rows","target_lane":"HELP DATA candidate mapping","target_object":"HELP_DATA_CANDIDATE_ROWS","mapping_status":"PLANNED_NOT_APPLIED","apply_now":0},
        {"candidate_table":"CMDCHK_CT","candidate_role":"candidate CMDHELPCHK-style rows","target_lane":"CMDHELPCHK candidate mapping","target_object":"CMDHELPCHK_CANDIDATE_ROWS","mapping_status":"PLANNED_NOT_APPLIED","apply_now":0},
        {"candidate_table":"MSGGATE_CT","candidate_role":"candidate boundary/provenance rows","target_lane":"Messaging apply gate evidence","target_object":"MESSAGE_APPLY_GATE_EVIDENCE","mapping_status":"PLANNED_NOT_APPLIED","apply_now":0},
    ]
    field_pairs = [
        ("MSGHELP_CT","MSG_ID","MESSAGE_ID","stable message/candidate row identifier"),
        ("MSGHELP_CT","LOCALE_ID","LOCALE_ID","shared locale spine identifier"),
        ("MSGHELP_CT","HELP_KEY","HELP_KEY","help/catalog lookup key"),
        ("MSGHELP_CT","HELP_TEXT","HELP_TEXT","candidate help text body"),
        ("MSGHELP_CT","SOURCE","SOURCE_PHASE","provenance/source phase"),
        ("MSGHELP_CT","STATUS","REVIEW_STATUS","candidate/review state"),
        ("CMDCHK_CT","CMD_NAME","COMMAND_NAME","command surface name"),
        ("CMDCHK_CT","HELP_KEY","HELP_KEY","associated help/catalog key"),
        ("CMDCHK_CT","CHECK_ID","CHECK_ID","candidate validation/check identifier"),
        ("CMDCHK_CT","CHECK_STAT","CHECK_STATUS","candidate check result/status"),
        ("CMDCHK_CT","MUTATES","MUTATION_FLAG","whether command/check mutates"),
        ("CMDCHK_CT","STATUS","REVIEW_STATUS","candidate/review state"),
        ("MSGGATE_CT","GATE_ID","GATE_ID","boundary gate identifier"),
        ("MSGGATE_CT","GATE_STAT","GATE_STATUS","boundary gate state"),
        ("MSGGATE_CT","MUTATES","MUTATION_FLAG","must remain false"),
        ("MSGGATE_CT","NOTES","GATE_NOTES","provenance/boundary note"),
    ]
    field_rows = [{"candidate_table": a, "candidate_field": b, "target_field": c, "meaning": d, "required": 1} for a,b,c,d in field_pairs]
    boundary = [
        {"boundary":"candidate table mapping planned","value":1,"status":"PASS"},
        {"boundary":"candidate mapping executed now","value":0,"status":"PASS"},
        {"boundary":"HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CW-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CW_B_MAPPING_PLAN_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cw_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cw_b_candidate_table_mapping_v1.csv", ["candidate_table","candidate_role","target_lane","target_object","mapping_status","apply_now"], table_map)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cw_b_field_mapping_v1.csv", ["candidate_table","candidate_field","target_field","meaning","required"], field_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cw_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10CW-B",
        "CORRECTED_CONCEPT": "DotTalk++ native table/materialization command path mapped to HELP/CMDHELPCHK candidate semantics",
        "CV_B_STATUS_GREEN": cv_green,
        "CV_B_SAVEPOINT_PRESENT": cv_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CW_B": latest_id(repo),
        "CANDIDATE_TABLE_MAPPINGS": len(table_map),
        "FIELD_MAPPING_ROWS": len(field_rows),
        "CANDIDATE_MAPPING_PLANNED": 1,
        "CANDIDATE_MAPPING_EXECUTED_NOW": 0,
        "PRODUCTION_HELP_CMDHELPCHK_REUSE_CONFIRMED_NOW": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "LATEST_POINTER_CHANGED_BY_CW_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cw_b_status_summary_v1.csv", list(summary[0].keys()), summary)
    write_text(out / "message_catalog_phase22ae_6_5_10cw_b_manifest_v1.json", json.dumps(summary[0], indent=2))
    report = "\n".join([
        "# Phase 22AE.6.5.10CW-B HELP/CMDHELPCHK Candidate Table Mapping Plan",
        "",
        f"- Status: {status}",
        f"- Validation issues: {validation}",
        f"- CV-B status green: {cv_green}",
        f"- CV-B savepoint present: {cv_savepoint}",
        f"- Candidate table mappings: {len(table_map)}",
        f"- Field mapping rows: {len(field_rows)}",
        "- Candidate mapping planned: 1",
        "- Candidate mapping executed now: 0",
        "- Production HELP/CMDHELPCHK reuse confirmed now: 0",
        "- Apply execution authorized now: 0",
        "- HELP DATA apply executed: 0",
        "- CMDHELPCHK apply executed: 0",
        "- Source mutation authorized now: 0",
        "- Latest pointer changed by CW-B: 0",
        f"- Next gate: {next_gate}",
        "",
    ])
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CW_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_MAPPING_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CW_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_MAPPING_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CV-B status green: {cv_green}")
    print(f"  CV-B savepoint present: {cv_savepoint}")
    print(f"  candidate table mappings: {len(table_map)}")
    print(f"  field mapping rows: {len(field_rows)}")
    print("  candidate mapping planned: 1")
    print("  candidate mapping executed now: 0")
    print("  production HELP/CMDHELPCHK reuse confirmed now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  latest pointer changed by CW-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
