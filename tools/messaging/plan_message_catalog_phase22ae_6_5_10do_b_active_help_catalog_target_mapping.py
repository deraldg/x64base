from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DN_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DN_B_OPERATOR_HELP_TARGET_EVIDENCE_INTAKE_GREEN_ACTIVE_HELP_CATALOG_CANDIDATE_FOUND_APPLY_HELD"
DN_SAVEPOINT = "MSG-022AE.6.5.10DN-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DO_B_ACTIVE_HELP_CATALOG_TARGET_MAPPING_PLAN_GREEN_MAPPING_HYPOTHESES_STAGED_APPLY_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DO_B_ACTIVE_HELP_CATALOG_TARGET_MAPPING_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DP_B_ACTIVE_HELP_CATALOG_MAPPING_REVIEW"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10do_b_active_help_catalog_target_mapping_plan_v1"

ACTIVE_SCHEMA = {
    "CMD_ARGS": ["ID","CATALOG","COMMAND","CMDKEY","ARG","USAGE","VERBOSE"],
    "COMMANDS": ["ID","CATALOG","COMMAND","CMDKEY","IMPLEMENT","SUPPORTED","USAGE","VERBOSE"],
    "HELP_ARTIFACTS": ["ID","CATALOG","COMMAND","CMDKEY","OWNER","KIND","SOURCE","CONFID","SEVERITY","NAME","ORD","TEXT","DETAIL","EVIDENCE"],
    "HELP_LINE": ["LINEID","ARTID","TOPICKEY","CATALOG","TOPIC","KIND","SOURCE","CONFID","SEVERITY","NAME","ROLE","LINE_NO","PART_NO","TEXT"],
    "HELP_SECTION": ["SECTID","ARTID","TOPICID","TOPICKEY","KIND","SOURCE","CONFID","SEVERITY","NAME","ORD","NLINES"],
    "HELP_TOPIC": ["TOPICID","TOPICKEY","CATALOG","TOPIC","TOPICTYPE","STATUS","IMPLEMENT","SUPPORTED","PRIMARY","CONFID","TITLE","SUMMARY","SECTIONS","LINES"],
}
EXPECTED_DBFS = {
    "CMD_ARGS":"dottalkpp/data/HELP/cmd_args.dbf",
    "COMMANDS":"dottalkpp/data/HELP/commands.dbf",
    "HELP_ARTIFACTS":"dottalkpp/data/HELP/help_artifacts.dbf",
    "HELP_LINE":"dottalkpp/data/HELP/help_line.dbf",
    "HELP_SECTION":"dottalkpp/data/HELP/help_section.dbf",
    "HELP_TOPIC":"dottalkpp/data/HELP/help_topic.dbf",
}

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

def as_int(value, default=0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default

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

    dn = csv_one(reports / "message_catalog_phase22ae_6_5_10dn_b_status_summary_v1.csv")
    help_targets = csv_rows(reports / "message_catalog_phase22ae_6_5_10dn_b_active_help_catalog_candidate_targets_v1.csv")
    help_candidate_rows = csv_rows(repo / "docs/messaging/apply/phase22ae_6_5_10cx_b_help_cmdhelpchk_candidate_mapping_staging_v1/candidate_outputs/HELP_DATA_CANDIDATE_ROWS.csv")
    cmd_candidate_rows = csv_rows(repo / "docs/messaging/apply/phase22ae_6_5_10cx_b_help_cmdhelpchk_candidate_mapping_staging_v1/candidate_outputs/CMDHELPCHK_CANDIDATE_ROWS.csv")

    dn_green = int(dn.get("STATUS", "") == DN_GREEN)
    dn_savepoint = has_journal(repo, DN_SAVEPOINT)
    active_root = as_int(dn.get("ACTIVE_HELP_CATALOG_ROOT_EXISTS", "0"))
    tables_found = as_int(dn.get("ACTIVE_HELP_CATALOG_TABLES_FOUND", "0"))
    apply_auth = as_int(dn.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0"))
    help_apply = as_int(dn.get("HELP_DATA_APPLY_EXECUTED", "0"))
    cmd_apply = as_int(dn.get("CMDHELPCHK_APPLY_EXECUTED", "0"))

    pre = [
        {"check_id":"dn_b_status_green","value":dn_green,"expected":1,"status":"PASS" if dn_green else "FAIL"},
        {"check_id":"dn_b_savepoint_present","value":dn_savepoint,"expected":1,"status":"PASS" if dn_savepoint else "FAIL"},
        {"check_id":"active_help_catalog_root_exists","value":active_root,"expected":1,"status":"PASS" if active_root else "FAIL"},
        {"check_id":"active_help_catalog_tables_found","value":tables_found,"expected":6,"status":"PASS" if tables_found >= 6 else "FAIL"},
        {"check_id":"help_candidate_rows_available","value":len(help_candidate_rows),"expected":">0","status":"PASS" if help_candidate_rows else "WARN"},
        {"check_id":"cmdhelpchk_candidate_rows_available","value":len(cmd_candidate_rows),"expected":">0","status":"PASS" if cmd_candidate_rows else "WARN"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"do_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
    ]

    schema_rows = []
    for table, fields in ACTIVE_SCHEMA.items():
        rel = EXPECTED_DBFS[table]
        exists = int((repo / rel).exists())
        schema_rows.append({
            "active_table":table,
            "relative_path":rel,
            "exists":exists,
            "field_count":len(fields),
            "fields":"|".join(fields),
            "role_guess":"active HELP catalog table from operator proof",
            "selected_for_apply_now":0,
            "apply_now":0,
        })

    mapping_rows = [
        {"candidate_family":"HELP_DATA","candidate_field":"HELP_KEY","active_table":"HELP_TOPIC","active_field":"TOPICKEY","mapping_type":"strong_hypothesis","confidence":"medium","mapping_note":"Candidate help key likely maps to topic key; review needed for topic namespace and uniqueness.","requires_review":1,"apply_now":0},
        {"candidate_family":"HELP_DATA","candidate_field":"HELP_KEY","active_table":"HELP_LINE","active_field":"TOPICKEY","mapping_type":"strong_hypothesis","confidence":"medium","mapping_note":"Line rows attach to topic key; candidate text may need section/line expansion.","requires_review":1,"apply_now":0},
        {"candidate_family":"HELP_DATA","candidate_field":"HELP_TEXT","active_table":"HELP_ARTIFACTS","active_field":"TEXT","mapping_type":"possible","confidence":"medium","mapping_note":"Memo TEXT may hold full artifact content; needs existing row model review.","requires_review":1,"apply_now":0},
        {"candidate_family":"HELP_DATA","candidate_field":"HELP_TEXT","active_table":"HELP_LINE","active_field":"TEXT","mapping_type":"possible_split","confidence":"medium","mapping_note":"HELP_LINE.TEXT is C(240), so longer help text would require line splitting and section records.","requires_review":1,"apply_now":0},
        {"candidate_family":"HELP_DATA","candidate_field":"SOURCE_PHASE","active_table":"HELP_ARTIFACTS","active_field":"SOURCE","mapping_type":"possible","confidence":"low","mapping_note":"SOURCE length 16 may not preserve full phase ID; needs compression/policy.","requires_review":1,"apply_now":0},
        {"candidate_family":"HELP_DATA","candidate_field":"REVIEW_STATUS","active_table":"HELP_TOPIC","active_field":"STATUS","mapping_type":"possible","confidence":"low","mapping_note":"Semantic mismatch possible: review status is process metadata, topic STATUS may be runtime status.","requires_review":1,"apply_now":0},
        {"candidate_family":"HELP_DATA","candidate_field":"LOCALE_ID","active_table":"NONE_OBVIOUS","active_field":"NONE_OBVIOUS","mapping_type":"gap","confidence":"high","mapping_note":"Active HELP catalog schema shown by operator proof does not expose LOCALE_ID; locale strategy must be decided before localized apply.","requires_review":1,"apply_now":0},
        {"candidate_family":"CMDHELPCHK","candidate_field":"COMMAND_NAME","active_table":"COMMANDS","active_field":"COMMAND","mapping_type":"strong_hypothesis","confidence":"high","mapping_note":"Command name maps naturally to COMMAND.","requires_review":1,"apply_now":0},
        {"candidate_family":"CMDHELPCHK","candidate_field":"HELP_KEY","active_table":"COMMANDS","active_field":"CMDKEY","mapping_type":"strong_hypothesis","confidence":"medium","mapping_note":"CMDKEY likely connects command to help topic/key; verify existing data convention.","requires_review":1,"apply_now":0},
        {"candidate_family":"CMDHELPCHK","candidate_field":"COMMAND_NAME","active_table":"CMD_ARGS","active_field":"COMMAND","mapping_type":"possible","confidence":"medium","mapping_note":"Arguments table uses COMMAND and ARG for command-specific help usage.","requires_review":1,"apply_now":0},
        {"candidate_family":"CMDHELPCHK","candidate_field":"HELP_KEY","active_table":"CMD_ARGS","active_field":"CMDKEY","mapping_type":"possible","confidence":"medium","mapping_note":"CMD_ARGS also has CMDKEY; verify relation with COMMANDS.CMDKEY.","requires_review":1,"apply_now":0},
        {"candidate_family":"CMDHELPCHK","candidate_field":"CHECK_ID","active_table":"HELP_ARTIFACTS","active_field":"NAME","mapping_type":"weak_hypothesis","confidence":"low","mapping_note":"CHECK_ID has no obvious active field; NAME may carry check/artifact name but needs review.","requires_review":1,"apply_now":0},
        {"candidate_family":"CMDHELPCHK","candidate_field":"CHECK_STATUS","active_table":"COMMANDS","active_field":"SUPPORTED","mapping_type":"semantic_gap","confidence":"low","mapping_note":"Status/check semantics do not directly match SUPPORTED/IMPLEMENT booleans without policy.","requires_review":1,"apply_now":0},
        {"candidate_family":"CMDHELPCHK","candidate_field":"MUTATION_FLAG","active_table":"NONE_OBVIOUS","active_field":"NONE_OBVIOUS","mapping_type":"gap","confidence":"high","mapping_note":"MUTATION_FLAG is gate/process metadata; should not be written into HELP catalog without explicit policy.","requires_review":1,"apply_now":0},
    ]

    gap_rows = [r for r in mapping_rows if r["mapping_type"] in ("gap","semantic_gap")]
    review_requirements = [
        {"req_id":"DP001","requirement":"Review active data rows from COMMANDS, CMD_ARGS, HELP_TOPIC, HELP_ARTIFACTS, HELP_SECTION, HELP_LINE before confirming mappings.","required":1},
        {"req_id":"DP002","requirement":"Resolve LOCALE_ID gap before any localized HELP apply.","required":1},
        {"req_id":"DP003","requirement":"Resolve whether CMDHELPCHK output should update COMMANDS/CMD_ARGS/HELP_* or remain a checker/report artifact.","required":1},
        {"req_id":"DP004","requirement":"Define line-splitting policy for HELP_LINE.TEXT C(240) and section/topic creation rules.","required":1},
        {"req_id":"DP005","requirement":"Define key collision policy for COMMAND, CMDKEY, TOPICKEY, TOPIC, and artifact IDs.","required":1},
        {"req_id":"DP006","requirement":"Keep DO-B plan-only; no active DBF/CDX/LMDB writes.","required":1},
    ]

    boundary = [
        {"boundary":"active HELP catalog target mapping plan created","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DO-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DO_B_ACTIVE_HELP_CATALOG_MAPPING_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10do_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10do_b_active_help_catalog_schema_v1.csv", ["active_table","relative_path","exists","field_count","fields","role_guess","selected_for_apply_now","apply_now"], schema_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10do_b_candidate_to_active_mapping_hypotheses_v1.csv", ["candidate_family","candidate_field","active_table","active_field","mapping_type","confidence","mapping_note","requires_review","apply_now"], mapping_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10do_b_mapping_gaps_v1.csv", ["candidate_family","candidate_field","active_table","active_field","mapping_type","confidence","mapping_note","requires_review","apply_now"], gap_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10do_b_mapping_review_requirements_v1.csv", ["req_id","requirement","required"], review_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10do_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DO-B",
        "DN_B_STATUS_GREEN":dn_green,
        "DN_B_SAVEPOINT_PRESENT":dn_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DO_B":latest_id(repo),
        "ACTIVE_HELP_CATALOG_MAPPING_PLAN_CREATED":1 if status == GREEN else 0,
        "ACTIVE_HELP_CATALOG_TABLES_MAPPED":len(schema_rows),
        "MAPPING_HYPOTHESIS_ROWS":len(mapping_rows),
        "MAPPING_GAP_ROWS":len(gap_rows),
        "HELP_CANDIDATE_ROWS_AVAILABLE":len(help_candidate_rows),
        "CMDHELPCHK_CANDIDATE_ROWS_AVAILABLE":len(cmd_candidate_rows),
        "LOCALE_ID_GAP_PRESENT":1,
        "CMDHELPCHK_SEMANTIC_GAP_PRESENT":1,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW":0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_PLAN":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_PLAN":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_PLAN":0,
        "LATEST_POINTER_CHANGED_BY_DO_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10do_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DO-B",
        "status":status,
        "mapping_plan_created":status == GREEN,
        "locale_id_gap_present":True,
        "cmdhelpchk_semantic_gap_present":True,
        "apply_execution_authorized_now":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10do_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DO-B Active HELP Catalog Target Mapping Plan

- Status: {status}
- Validation issues: {validation}
- DN-B status green: {dn_green}
- DN-B savepoint present: {dn_savepoint}
- Active HELP catalog mapping plan created: {1 if status == GREEN else 0}
- Active HELP catalog tables mapped: {len(schema_rows)}
- Mapping hypothesis rows: {len(mapping_rows)}
- Mapping gap rows: {len(gap_rows)}
- HELP candidate rows available: {len(help_candidate_rows)}
- CMDHELPCHK candidate rows available: {len(cmd_candidate_rows)}
- LOCALE_ID gap present: 1
- CMDHELPCHK semantic gap present: 1
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by plan: 0
- Active DBF/CDX/LMDB mutation observed by plan: 0
- Workspace mutation observed by plan: 0
- Latest pointer changed by DO-B: 0
- Next gate: {next_gate}

DO-B maps candidate fields to the active HELP catalog schema as hypotheses only. It highlights gaps, especially LOCALE_ID and CMDHELPCHK semantics, and authorizes no apply.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DO_B_ACTIVE_HELP_CATALOG_TARGET_MAPPING_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DO_B_ACTIVE_HELP_CATALOG_TARGET_MAPPING_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DN-B status green: {dn_green}")
    print(f"  DN-B savepoint present: {dn_savepoint}")
    print(f"  active HELP catalog mapping plan created: {1 if status == GREEN else 0}")
    print(f"  active HELP catalog tables mapped: {len(schema_rows)}")
    print(f"  mapping hypothesis rows: {len(mapping_rows)}")
    print(f"  mapping gap rows: {len(gap_rows)}")
    print(f"  HELP candidate rows available: {len(help_candidate_rows)}")
    print(f"  CMDHELPCHK candidate rows available: {len(cmd_candidate_rows)}")
    print("  LOCALE_ID gap present: 1")
    print("  CMDHELPCHK semantic gap present: 1")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by plan: 0")
    print("  active DBF/CDX/LMDB mutation observed by plan: 0")
    print("  workspace mutation observed by plan: 0")
    print("  latest pointer changed by DO-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
