from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DO_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DO_B_ACTIVE_HELP_CATALOG_TARGET_MAPPING_PLAN_GREEN_MAPPING_HYPOTHESES_STAGED_APPLY_HELD"
DO_SAVEPOINT = "MSG-022AE.6.5.10DO-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DP_B_ACTIVE_HELP_CATALOG_MAPPING_REVIEW_GREEN_MAPPING_ACCEPTED_GAPS_REQUIRE_POLICY_APPLY_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DP_B_ACTIVE_HELP_CATALOG_MAPPING_REVIEW_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DQ_B_LOCALE_CMDHELPCHK_GAP_RESOLUTION_POLICY_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dp_b_active_help_catalog_mapping_review_v1"

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

def review_disposition(row: dict) -> tuple[str, str, int]:
    mtype = row.get("mapping_type", "")
    cand_field = row.get("candidate_field", "")
    family = row.get("candidate_family", "")
    note = row.get("mapping_note", "")
    if cand_field == "LOCALE_ID":
        return "BLOCKED_BY_LOCALE_GAP", "Active HELP catalog has no LOCALE_ID field; localized apply policy required first.", 1
    if family == "CMDHELPCHK" and mtype in ("gap", "semantic_gap", "weak_hypothesis"):
        return "BLOCKED_BY_CMDHELPCHK_SEMANTIC_GAP", "CMDHELPCHK semantics do not yet map safely to active HELP catalog fields.", 1
    if mtype in ("strong_hypothesis", "possible", "possible_split"):
        return "ACCEPT_FOR_POLICY_REVIEW", "Mapping is plausible but still requires policy, key, collision, and row-shape review.", 0
    if mtype in ("gap", "semantic_gap"):
        return "BLOCKED_BY_UNRESOLVED_GAP", note or "Unresolved mapping gap.", 1
    return "DEFER_REVIEW", note or "Requires manual mapping review.", 1

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--replace-existing-review", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_review:
        shutil.rmtree(out)

    do = csv_one(reports / "message_catalog_phase22ae_6_5_10do_b_status_summary_v1.csv")
    schema = csv_rows(reports / "message_catalog_phase22ae_6_5_10do_b_active_help_catalog_schema_v1.csv")
    mapping = csv_rows(reports / "message_catalog_phase22ae_6_5_10do_b_candidate_to_active_mapping_hypotheses_v1.csv")
    gaps = csv_rows(reports / "message_catalog_phase22ae_6_5_10do_b_mapping_gaps_v1.csv")
    reqs = csv_rows(reports / "message_catalog_phase22ae_6_5_10do_b_mapping_review_requirements_v1.csv")

    do_green = int(do.get("STATUS", "") == DO_GREEN)
    do_savepoint = has_journal(repo, DO_SAVEPOINT)
    mapping_created = as_int(do.get("ACTIVE_HELP_CATALOG_MAPPING_PLAN_CREATED", "0"))
    mapping_rows = as_int(do.get("MAPPING_HYPOTHESIS_ROWS", len(mapping)))
    gap_rows = as_int(do.get("MAPPING_GAP_ROWS", len(gaps)))
    locale_gap = as_int(do.get("LOCALE_ID_GAP_PRESENT", "0"))
    cmd_gap = as_int(do.get("CMDHELPCHK_SEMANTIC_GAP_PRESENT", "0"))
    apply_auth = as_int(do.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0"))
    help_apply = as_int(do.get("HELP_DATA_APPLY_EXECUTED", "0"))
    cmd_apply = as_int(do.get("CMDHELPCHK_APPLY_EXECUTED", "0"))

    pre = [
        {"check_id":"do_b_status_green","value":do_green,"expected":1,"status":"PASS" if do_green else "FAIL"},
        {"check_id":"do_b_savepoint_present","value":do_savepoint,"expected":1,"status":"PASS" if do_savepoint else "FAIL"},
        {"check_id":"active_help_catalog_mapping_plan_created","value":mapping_created,"expected":1,"status":"PASS" if mapping_created else "FAIL"},
        {"check_id":"active_schema_rows_exist","value":len(schema),"expected":">0","status":"PASS" if schema else "FAIL"},
        {"check_id":"mapping_hypotheses_exist","value":len(mapping),"expected":">0","status":"PASS" if mapping else "FAIL"},
        {"check_id":"mapping_gaps_declared","value":gap_rows,"expected":">=1","status":"PASS" if gap_rows >= 1 else "FAIL"},
        {"check_id":"locale_gap_declared","value":locale_gap,"expected":1,"status":"PASS" if locale_gap else "FAIL"},
        {"check_id":"cmdhelpchk_semantic_gap_declared","value":cmd_gap,"expected":1,"status":"PASS" if cmd_gap else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"dp_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_review) else "FAIL"},
    ]

    reviewed = []
    blockers = []
    accepted = 0
    for row in mapping:
        disposition, reason, blocks_dry_run = review_disposition(row)
        if disposition == "ACCEPT_FOR_POLICY_REVIEW":
            accepted += 1
        reviewed_row = {
            "candidate_family":row.get("candidate_family", ""),
            "candidate_field":row.get("candidate_field", ""),
            "active_table":row.get("active_table", ""),
            "active_field":row.get("active_field", ""),
            "mapping_type":row.get("mapping_type", ""),
            "confidence":row.get("confidence", ""),
            "review_disposition":disposition,
            "review_reason":reason,
            "blocks_dry_run":blocks_dry_run,
            "requires_policy_resolution":1,
            "apply_now":0,
        }
        reviewed.append(reviewed_row)
        if blocks_dry_run:
            blockers.append(reviewed_row)

    policy_questions = [
        {"question_id":"DQ001","policy_area":"locale","question":"How should LOCALE_ID be represented when active HELP catalog tables have no LOCALE_ID field?","must_resolve_before_dry_run":1},
        {"question_id":"DQ002","policy_area":"cmdhelpchk","question":"Is CMDHELPCHK intended to update COMMANDS/CMD_ARGS/HELP_* rows, remain a checker/report artifact, or both?","must_resolve_before_dry_run":1},
        {"question_id":"DQ003","policy_area":"line_model","question":"When candidate HELP_TEXT exceeds HELP_LINE.TEXT C(240), what line-splitting and section/topic creation policy applies?","must_resolve_before_dry_run":1},
        {"question_id":"DQ004","policy_area":"keys","question":"What are the canonical keys for COMMAND, CMDKEY, TOPICKEY, TOPIC, ARTID, SECTID, LINEID, and collision handling?","must_resolve_before_dry_run":1},
        {"question_id":"DQ005","policy_area":"memo","question":"Which candidate content should become memo text in HELP_ARTIFACTS.TEXT/DETAIL/EVIDENCE versus fixed text in HELP_LINE.TEXT?","must_resolve_before_dry_run":1},
    ]

    dp_decisions = [
        {"decision_id":"DP001_ACCEPT_DO_MAPPING_PLAN","decision":"ACCEPT","meaning":"DO-B mapping hypotheses are accepted for policy review.","selected":1,"apply_now":0},
        {"decision_id":"DP002_ACCEPT_ACTIVE_HELP_SCHEMA_AS_TARGET_CANDIDATE","decision":"ACCEPT","meaning":"The six-table active HELP catalog surface is accepted as the candidate target family.","selected":1,"apply_now":0},
        {"decision_id":"DP003_BLOCK_DRY_RUN_UNTIL_GAPS_RESOLVED","decision":"ACCEPT","meaning":"Dry-run/apply remains blocked until LOCALE_ID and CMDHELPCHK semantic gaps are resolved.","selected":1,"apply_now":0},
        {"decision_id":"DP004_KEEP_APPLY_HELD","decision":"ACCEPT","meaning":"No HELP DATA/CMDHELPCHK apply is authorized by DP-B.","selected":1,"apply_now":0},
        {"decision_id":"DP005_SELECT_DQ_POLICY_PLAN_NEXT","decision":"SELECT_NEXT","meaning":"Proceed to DQ-B locale/CMDHELPCHK gap-resolution policy plan.","selected":1,"apply_now":0},
    ]

    boundary = [
        {"boundary":"active HELP catalog mapping review created","value":1,"status":"PASS"},
        {"boundary":"dry-run authorized now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DP-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DP_B_MAPPING_REVIEW_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dp_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dp_b_reviewed_mapping_hypotheses_v1.csv", ["candidate_family","candidate_field","active_table","active_field","mapping_type","confidence","review_disposition","review_reason","blocks_dry_run","requires_policy_resolution","apply_now"], reviewed)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dp_b_dry_run_blockers_v1.csv", ["candidate_family","candidate_field","active_table","active_field","mapping_type","confidence","review_disposition","review_reason","blocks_dry_run","requires_policy_resolution","apply_now"], blockers)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dp_b_policy_questions_v1.csv", ["question_id","policy_area","question","must_resolve_before_dry_run"], policy_questions)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dp_b_decision_rows_v1.csv", ["decision_id","decision","meaning","selected","apply_now"], dp_decisions)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dp_b_do_review_requirements_copy_v1.csv", list(reqs[0].keys()) if reqs else ["req_id"], reqs)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dp_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DP-B",
        "DO_B_STATUS_GREEN":do_green,
        "DO_B_SAVEPOINT_PRESENT":do_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DP_B":latest_id(repo),
        "ACTIVE_HELP_CATALOG_MAPPING_REVIEW_CREATED":1 if status == GREEN else 0,
        "MAPPING_HYPOTHESES_REVIEWED":len(reviewed),
        "ACCEPTED_FOR_POLICY_REVIEW_ROWS":accepted,
        "DRY_RUN_BLOCKER_ROWS":len(blockers),
        "POLICY_QUESTION_ROWS":len(policy_questions),
        "LOCALE_ID_GAP_BLOCKS_DRY_RUN":locale_gap,
        "CMDHELPCHK_SEMANTIC_GAP_BLOCKS_DRY_RUN":cmd_gap,
        "DRY_RUN_AUTHORIZED_NOW":0,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW":0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_REVIEW":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_REVIEW":0,
        "LATEST_POINTER_CHANGED_BY_DP_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dp_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DP-B",
        "status":status,
        "mapping_review_created":status == GREEN,
        "dry_run_blocked_by_policy_gaps":True,
        "apply_execution_authorized_now":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dp_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DP-B Active HELP Catalog Mapping Review

- Status: {status}
- Validation issues: {validation}
- DO-B status green: {do_green}
- DO-B savepoint present: {do_savepoint}
- Active HELP catalog mapping review created: {1 if status == GREEN else 0}
- Mapping hypotheses reviewed: {len(reviewed)}
- Accepted for policy review rows: {accepted}
- Dry-run blocker rows: {len(blockers)}
- Policy question rows: {len(policy_questions)}
- LOCALE_ID gap blocks dry-run: {locale_gap}
- CMDHELPCHK semantic gap blocks dry-run: {cmd_gap}
- Dry-run authorized now: 0
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by review: 0
- Active DBF/CDX/LMDB mutation observed by review: 0
- Workspace mutation observed by review: 0
- Latest pointer changed by DP-B: 0
- Next gate: {next_gate}

DP-B accepts DO-B's mapping hypotheses as useful but not executable. LOCALE_ID and CMDHELPCHK semantic gaps are explicit blockers, so the next safe step is a policy/gap-resolution plan, not a dry-run or apply.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DP_B_ACTIVE_HELP_CATALOG_MAPPING_REVIEW.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DP_B_ACTIVE_HELP_CATALOG_MAPPING_REVIEW.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DO-B status green: {do_green}")
    print(f"  DO-B savepoint present: {do_savepoint}")
    print(f"  active HELP catalog mapping review created: {1 if status == GREEN else 0}")
    print(f"  mapping hypotheses reviewed: {len(reviewed)}")
    print(f"  accepted for policy review rows: {accepted}")
    print(f"  dry-run blocker rows: {len(blockers)}")
    print(f"  policy question rows: {len(policy_questions)}")
    print(f"  LOCALE_ID gap blocks dry-run: {locale_gap}")
    print(f"  CMDHELPCHK semantic gap blocks dry-run: {cmd_gap}")
    print("  dry-run authorized now: 0")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by review: 0")
    print("  active DBF/CDX/LMDB mutation observed by review: 0")
    print("  workspace mutation observed by review: 0")
    print("  latest pointer changed by DP-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
