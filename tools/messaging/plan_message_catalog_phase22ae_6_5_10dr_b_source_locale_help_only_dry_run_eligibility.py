from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DQ_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DQ_B_LOCALE_CMDHELPCHK_GAP_RESOLUTION_POLICY_PLAN_GREEN_POLICY_STAGED_DRY_RUN_STILL_HELD"
DQ_SAVEPOINT = "MSG-022AE.6.5.10DQ-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DR_B_SOURCE_LOCALE_HELP_ONLY_DRY_RUN_ELIGIBILITY_PLAN_GREEN_SCOPE_NARROWED_DRY_RUN_STILL_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DR_B_SOURCE_LOCALE_HELP_ONLY_DRY_RUN_ELIGIBILITY_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DS_B_SOURCE_LOCALE_HELP_ROW_SHAPE_KEY_POLICY_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dr_b_source_locale_help_only_dry_run_eligibility_plan_v1"

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

def is_source_locale(row: dict) -> int:
    loc = (row.get("LOCALE_ID") or row.get("locale_id") or "").strip().lower()
    if not loc:
        return 1
    return int(loc in {"source", "source_locale", "base", "base_locale", "en", "en-us", "en_us", "default"})

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

    dq = csv_one(reports / "message_catalog_phase22ae_6_5_10dq_b_status_summary_v1.csv")
    scope_rows = csv_rows(reports / "message_catalog_phase22ae_6_5_10dq_b_narrowed_next_scope_v1.csv")
    unresolved = csv_rows(reports / "message_catalog_phase22ae_6_5_10dq_b_unresolved_apply_gaps_v1.csv")
    help_rows = csv_rows(repo / "docs/messaging/apply/phase22ae_6_5_10cx_b_help_cmdhelpchk_candidate_mapping_staging_v1/candidate_outputs/HELP_DATA_CANDIDATE_ROWS.csv")
    mappings = csv_rows(reports / "message_catalog_phase22ae_6_5_10do_b_candidate_to_active_mapping_hypotheses_v1.csv")

    dq_green = int(dq.get("STATUS", "") == DQ_GREEN)
    dq_savepoint = has_journal(repo, DQ_SAVEPOINT)
    source_locale_allowed = as_int(dq.get("LOCALE_GAP_POLICY_RESOLVED_FOR_SOURCE_LOCALE_SCOPE", "0"))
    localized_held = as_int(dq.get("LOCALIZED_VARIANTS_HELD_FOR_FUTURE_OVERLAY", "0"))
    cmd_report_only = as_int(dq.get("CMDHELPCHK_POLICY_RESOLVED_AS_REPORT_ONLY_FOR_THIS_LANE", "0"))
    dryrun_auth = as_int(dq.get("DRY_RUN_AUTHORIZED_NOW", "0"))
    apply_auth = as_int(dq.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0"))

    source_help_rows = [r for r in help_rows if is_source_locale(r)]
    localized_help_rows = [r for r in help_rows if not is_source_locale(r)]

    pre = [
        {"check_id":"dq_b_status_green","value":dq_green,"expected":1,"status":"PASS" if dq_green else "FAIL"},
        {"check_id":"dq_b_savepoint_present","value":dq_savepoint,"expected":1,"status":"PASS" if dq_savepoint else "FAIL"},
        {"check_id":"source_locale_scope_allowed_by_dq_b","value":source_locale_allowed,"expected":1,"status":"PASS" if source_locale_allowed else "FAIL"},
        {"check_id":"localized_variants_held_by_dq_b","value":localized_held,"expected":1,"status":"PASS" if localized_held else "FAIL"},
        {"check_id":"cmdhelpchk_report_only_by_dq_b","value":cmd_report_only,"expected":1,"status":"PASS" if cmd_report_only else "FAIL"},
        {"check_id":"help_candidate_rows_available","value":len(help_rows),"expected":">0","status":"PASS" if help_rows else "WARN"},
        {"check_id":"source_locale_help_rows_available","value":len(source_help_rows),"expected":">0","status":"PASS" if source_help_rows else "WARN"},
        {"check_id":"dry_run_not_authorized_by_dq_b","value":dryrun_auth,"expected":0,"status":"PASS" if dryrun_auth == 0 else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"dr_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
    ]

    eligibility_rows = [
        {
            "scope_id":"DR001",
            "candidate_scope":"source-locale HELP_DATA rows",
            "candidate_rows":len(source_help_rows),
            "eligible_for_row_shape_policy_plan":1 if source_help_rows else 0,
            "eligible_for_dry_run_now":0,
            "eligibility_reason":"DQ-B allows source-locale HELP-only scope, but row-shape/key policy is still required before dry-run.",
            "apply_now":0,
        },
        {
            "scope_id":"DR002",
            "candidate_scope":"localized HELP_DATA variants",
            "candidate_rows":len(localized_help_rows),
            "eligible_for_row_shape_policy_plan":0,
            "eligible_for_dry_run_now":0,
            "eligibility_reason":"Localized variants remain held for future overlay/schema work because active HELP catalog has no LOCALE_ID field.",
            "apply_now":0,
        },
        {
            "scope_id":"DR003",
            "candidate_scope":"CMDHELPCHK rows as active catalog writes",
            "candidate_rows":0,
            "eligible_for_row_shape_policy_plan":0,
            "eligible_for_dry_run_now":0,
            "eligibility_reason":"DQ-B resolves CMDHELPCHK as validation/report evidence only in this lane.",
            "apply_now":0,
        },
        {
            "scope_id":"DR004",
            "candidate_scope":"CMDHELPCHK rows as validation gates",
            "candidate_rows":0,
            "eligible_for_row_shape_policy_plan":1,
            "eligible_for_dry_run_now":0,
            "eligibility_reason":"May be used as readback/coverage validation, not active catalog mutation.",
            "apply_now":0,
        },
    ]

    source_help_preview = []
    for idx, row in enumerate(source_help_rows, start=1):
        source_help_preview.append({
            "row_id":f"DR_HELP_{idx:03d}",
            "HELP_KEY":row.get("HELP_KEY", ""),
            "LOCALE_ID":row.get("LOCALE_ID", ""),
            "HELP_TEXT_LENGTH":len(row.get("HELP_TEXT", "")),
            "SOURCE_PHASE":row.get("SOURCE_PHASE", ""),
            "REVIEW_STATUS":row.get("REVIEW_STATUS", ""),
            "eligible_for_next_policy_plan":1,
            "eligible_for_dry_run_now":0,
            "apply_now":0,
        })

    row_shape_requirements = [
        {"req_id":"DS001","requirement":"Define TOPICKEY/TOPIC/CATALOG policy for each source-locale HELP_KEY.","required":1},
        {"req_id":"DS002","requirement":"Define HELP_TOPIC row creation/update rules, including TOPICTYPE, STATUS, IMPLEMENT, SUPPORTED, PRIMARY, CONFID, TITLE, SUMMARY.","required":1},
        {"req_id":"DS003","requirement":"Define HELP_ARTIFACTS row creation/update rules for SOURCE, CONFID, SEVERITY, NAME, ORD, TEXT, DETAIL, EVIDENCE.","required":1},
        {"req_id":"DS004","requirement":"Define HELP_SECTION and HELP_LINE expansion policy for HELP_TEXT, including C(240) line splitting and ordering.","required":1},
        {"req_id":"DS005","requirement":"Define ID/key generation or lookup policy for TOPICID, ARTID, SECTID, LINEID without corrupting existing catalog rows.","required":1},
        {"req_id":"DS006","requirement":"Define collision policy when candidate HELP_KEY/TOPICKEY already exists.","required":1},
        {"req_id":"DS007","requirement":"Define validation/readback checks using CMDHELPCHK rows as report-only evidence.","required":1},
        {"req_id":"DS008","requirement":"Keep DS-B policy-only; no dry-run/apply until later package.","required":1},
    ]

    next_decisions = [
        {"decision_id":"DR001_ACCEPT_NARROWED_SCOPE","decision":"ACCEPT","meaning":"Proceed with source-locale HELP-only eligibility planning.","selected":1,"dry_run_now":0,"apply_now":0},
        {"decision_id":"DR002_HOLD_LOCALIZED_VARIANTS","decision":"ACCEPT","meaning":"Localized HELP variants remain held for future overlay/schema work.","selected":1,"dry_run_now":0,"apply_now":0},
        {"decision_id":"DR003_HOLD_CMDHELPCHK_CATALOG_WRITES","decision":"ACCEPT","meaning":"CMDHELPCHK rows remain validation/report evidence only.","selected":1,"dry_run_now":0,"apply_now":0},
        {"decision_id":"DR004_SELECT_DS_ROW_SHAPE_KEY_POLICY_NEXT","decision":"SELECT_NEXT","meaning":"Next package must define row-shape, key, collision, and line-splitting policy before dry-run.","selected":1,"dry_run_now":0,"apply_now":0},
    ]

    boundary = [
        {"boundary":"source-locale HELP-only dry-run eligibility plan created","value":1,"status":"PASS"},
        {"boundary":"dry-run authorized now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DR-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DR_B_ELIGIBILITY_PLAN_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dr_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dr_b_eligibility_scope_v1.csv", ["scope_id","candidate_scope","candidate_rows","eligible_for_row_shape_policy_plan","eligible_for_dry_run_now","eligibility_reason","apply_now"], eligibility_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dr_b_source_locale_help_preview_v1.csv", ["row_id","HELP_KEY","LOCALE_ID","HELP_TEXT_LENGTH","SOURCE_PHASE","REVIEW_STATUS","eligible_for_next_policy_plan","eligible_for_dry_run_now","apply_now"], source_help_preview)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dr_b_row_shape_key_requirements_v1.csv", ["req_id","requirement","required"], row_shape_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dr_b_next_decisions_v1.csv", ["decision_id","decision","meaning","selected","dry_run_now","apply_now"], next_decisions)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dr_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DR-B",
        "DQ_B_STATUS_GREEN":dq_green,
        "DQ_B_SAVEPOINT_PRESENT":dq_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DR_B":latest_id(repo),
        "SOURCE_LOCALE_HELP_ONLY_ELIGIBILITY_PLAN_CREATED":1 if status == GREEN else 0,
        "HELP_CANDIDATE_ROWS":len(help_rows),
        "SOURCE_LOCALE_HELP_ROWS":len(source_help_rows),
        "LOCALIZED_HELP_ROWS_HELD":len(localized_help_rows),
        "ELIGIBILITY_SCOPE_ROWS":len(eligibility_rows),
        "ROW_SHAPE_KEY_REQUIREMENT_ROWS":len(row_shape_requirements),
        "SOURCE_LOCALE_HELP_SCOPE_ELIGIBLE_FOR_NEXT_POLICY_PLAN":1 if source_help_rows and status == GREEN else 0,
        "SOURCE_LOCALE_HELP_DRY_RUN_AUTHORIZED_NOW":0,
        "DRY_RUN_AUTHORIZED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_PLAN":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_PLAN":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_PLAN":0,
        "LATEST_POINTER_CHANGED_BY_DR_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dr_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DR-B",
        "status":status,
        "source_locale_help_scope_eligible_for_next_policy_plan": bool(source_help_rows and status == GREEN),
        "dry_run_authorized_now": False,
        "apply_execution_authorized_now": False,
        "next_gate": next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dr_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DR-B Source-Locale HELP-only Dry-run Eligibility Plan

- Status: {status}
- Validation issues: {validation}
- DQ-B status green: {dq_green}
- DQ-B savepoint present: {dq_savepoint}
- Source-locale HELP-only eligibility plan created: {1 if status == GREEN else 0}
- HELP candidate rows: {len(help_rows)}
- Source-locale HELP rows: {len(source_help_rows)}
- Localized HELP rows held: {len(localized_help_rows)}
- Row-shape/key requirement rows: {len(row_shape_requirements)}
- Source-locale HELP scope eligible for next policy plan: {1 if source_help_rows and status == GREEN else 0}
- Source-locale HELP dry-run authorized now: 0
- Dry-run authorized now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by plan: 0
- Active DBF/CDX/LMDB mutation observed by plan: 0
- Workspace mutation observed by plan: 0
- Latest pointer changed by DR-B: 0
- Next gate: {next_gate}

DR-B narrows the lane to source-locale HELP-only eligibility. It does not authorize dry-run or apply; DS-B must define row-shape, key, collision, and line-splitting policy first.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DR_B_SOURCE_LOCALE_HELP_ONLY_DRY_RUN_ELIGIBILITY_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DR_B_SOURCE_LOCALE_HELP_ONLY_DRY_RUN_ELIGIBILITY_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DQ-B status green: {dq_green}")
    print(f"  DQ-B savepoint present: {dq_savepoint}")
    print(f"  source-locale HELP-only eligibility plan created: {1 if status == GREEN else 0}")
    print(f"  HELP candidate rows: {len(help_rows)}")
    print(f"  source-locale HELP rows: {len(source_help_rows)}")
    print(f"  localized HELP rows held: {len(localized_help_rows)}")
    print(f"  eligibility scope rows: {len(eligibility_rows)}")
    print(f"  row-shape/key requirement rows: {len(row_shape_requirements)}")
    print(f"  source-locale HELP scope eligible for next policy plan: {1 if source_help_rows and status == GREEN else 0}")
    print("  source-locale HELP dry-run authorized now: 0")
    print("  dry-run authorized now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by plan: 0")
    print("  active DBF/CDX/LMDB mutation observed by plan: 0")
    print("  workspace mutation observed by plan: 0")
    print("  latest pointer changed by DR-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
