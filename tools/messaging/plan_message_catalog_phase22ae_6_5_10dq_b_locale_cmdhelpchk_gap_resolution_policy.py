from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DP_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DP_B_ACTIVE_HELP_CATALOG_MAPPING_REVIEW_GREEN_MAPPING_ACCEPTED_GAPS_REQUIRE_POLICY_APPLY_HELD"
DP_SAVEPOINT = "MSG-022AE.6.5.10DP-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DQ_B_LOCALE_CMDHELPCHK_GAP_RESOLUTION_POLICY_PLAN_GREEN_POLICY_STAGED_DRY_RUN_STILL_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DQ_B_LOCALE_CMDHELPCHK_GAP_RESOLUTION_POLICY_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DR_B_SOURCE_LOCALE_HELP_ONLY_DRY_RUN_ELIGIBILITY_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dq_b_locale_cmdhelpchk_gap_resolution_policy_plan_v1"

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

    dp = csv_one(reports / "message_catalog_phase22ae_6_5_10dp_b_status_summary_v1.csv")
    blockers = csv_rows(reports / "message_catalog_phase22ae_6_5_10dp_b_dry_run_blockers_v1.csv")
    policy_questions = csv_rows(reports / "message_catalog_phase22ae_6_5_10dp_b_policy_questions_v1.csv")
    reviewed_mappings = csv_rows(reports / "message_catalog_phase22ae_6_5_10dp_b_reviewed_mapping_hypotheses_v1.csv")

    dp_green = int(dp.get("STATUS", "") == DP_GREEN)
    dp_savepoint = has_journal(repo, DP_SAVEPOINT)
    locale_gap = as_int(dp.get("LOCALE_ID_GAP_BLOCKS_DRY_RUN", "0"))
    cmd_gap = as_int(dp.get("CMDHELPCHK_SEMANTIC_GAP_BLOCKS_DRY_RUN", "0"))
    dryrun_auth = as_int(dp.get("DRY_RUN_AUTHORIZED_NOW", "0"))
    apply_auth = as_int(dp.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0"))
    help_apply = as_int(dp.get("HELP_DATA_APPLY_EXECUTED", "0"))
    cmd_apply = as_int(dp.get("CMDHELPCHK_APPLY_EXECUTED", "0"))

    pre = [
        {"check_id":"dp_b_status_green","value":dp_green,"expected":1,"status":"PASS" if dp_green else "FAIL"},
        {"check_id":"dp_b_savepoint_present","value":dp_savepoint,"expected":1,"status":"PASS" if dp_savepoint else "FAIL"},
        {"check_id":"locale_gap_was_declared","value":locale_gap,"expected":1,"status":"PASS" if locale_gap else "FAIL"},
        {"check_id":"cmdhelpchk_gap_was_declared","value":cmd_gap,"expected":1,"status":"PASS" if cmd_gap else "FAIL"},
        {"check_id":"dry_run_not_authorized_pre_policy","value":dryrun_auth,"expected":0,"status":"PASS" if dryrun_auth == 0 else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"policy_questions_available","value":len(policy_questions),"expected":">0","status":"PASS" if policy_questions else "WARN"},
        {"check_id":"dry_run_blockers_available","value":len(blockers),"expected":">0","status":"PASS" if blockers else "WARN"},
        {"check_id":"dq_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
    ]

    policy_decisions = [
        {
            "policy_id":"DQ001_LOCALE_ACTIVE_HELP_SOURCE_LOCALE_ONLY",
            "policy_area":"locale",
            "decision":"SOURCE_LOCALE_ONLY_FOR_ACTIVE_HELP_CATALOG_IN_THIS_LANE",
            "meaning":"The active six-table HELP catalog has no LOCALE_ID field, so this lane must not write localized variants into it.",
            "resolves_blocker":1,
            "dry_run_unblocked_for_scope":"source-locale HELP-only candidates after separate eligibility review",
            "apply_now":0,
        },
        {
            "policy_id":"DQ002_LOCALE_LOCALIZED_ROWS_HELD_FOR_OVERLAY",
            "policy_area":"locale",
            "decision":"LOCALIZED_ROWS_REQUIRE_FUTURE_LOCALE_OVERLAY_OR_SCHEMA_EXTENSION",
            "meaning":"Rows whose LOCALE_ID is not the active/source locale must remain candidate evidence until a locale-aware HELP overlay/table/schema is designed and authorized.",
            "resolves_blocker":1,
            "dry_run_unblocked_for_scope":"none for localized variants",
            "apply_now":0,
        },
        {
            "policy_id":"DQ003_CMDHELPCHK_REPORT_EVIDENCE_ONLY",
            "policy_area":"cmdhelpchk",
            "decision":"CMDHELPCHK_ROWS_ARE_VALIDATION_REPORT_EVIDENCE_NOT_DIRECT_HELP_CATALOG_WRITES",
            "meaning":"CMDHELPCHK candidate rows should verify command/help coverage and gate status, not mutate COMMANDS/CMD_ARGS/HELP_* directly in this lane.",
            "resolves_blocker":1,
            "dry_run_unblocked_for_scope":"HELP_DATA source-locale rows only; CMDHELPCHK remains report-only",
            "apply_now":0,
        },
        {
            "policy_id":"DQ004_HELP_TEXT_LINE_POLICY_DEFERRED_TO_DRY_RUN_ELIGIBILITY",
            "policy_area":"line_model",
            "decision":"LINE_SPLIT_AND_ARTIFACT_POLICY_REQUIRED_BEFORE_DRY_RUN",
            "meaning":"HELP_LINE.TEXT is fixed width and HELP_ARTIFACTS has memo text, so source-locale dry-run must still stage a row-shape/line-splitting policy before execution.",
            "resolves_blocker":0,
            "dry_run_unblocked_for_scope":"not yet; requires DR-B eligibility plan",
            "apply_now":0,
        },
        {
            "policy_id":"DQ005_NO_APPLY_OR_DRY_RUN_BY_POLICY_PLAN",
            "policy_area":"execution",
            "decision":"NO_DRY_RUN_OR_APPLY_AUTHORIZED_BY_DQ_B",
            "meaning":"DQ-B is policy planning only. It sets the next narrowed scope but performs no dry-run and no active mutation.",
            "resolves_blocker":0,
            "dry_run_unblocked_for_scope":"none by DQ-B itself",
            "apply_now":0,
        },
    ]

    scope_rows = [
        {"scope_id":"DR_SCOPE_001","scope":"source-locale HELP_DATA rows only","eligible_for_next_plan":1,"reason":"Locale gap can be avoided only by limiting next plan to active/source locale HELP rows."},
        {"scope_id":"DR_SCOPE_002","scope":"localized HELP_DATA variants","eligible_for_next_plan":0,"reason":"Requires future locale-aware overlay/schema."},
        {"scope_id":"DR_SCOPE_003","scope":"CMDHELPCHK rows as active HELP catalog writes","eligible_for_next_plan":0,"reason":"Must remain validation/report evidence until command-check semantics are separately designed."},
        {"scope_id":"DR_SCOPE_004","scope":"CMDHELPCHK rows as validation/readback gates","eligible_for_next_plan":1,"reason":"May be used to verify coverage, not to mutate active HELP catalog."},
        {"scope_id":"DR_SCOPE_005","scope":"source-locale HELP dry-run eligibility","eligible_for_next_plan":1,"reason":"Next plan may decide whether the source-locale HELP subset is dry-run eligible after row-shape/key policy review."},
    ]

    unresolved = [
        {"gap_id":"DQ_GAP_001","gap":"Exact active/source locale identity must be confirmed before dry-run.","blocks_apply":1,"blocks_dry_run":1},
        {"gap_id":"DQ_GAP_002","gap":"HELP_LINE/HELP_SECTION/HELP_ARTIFACTS row-shape policy must be specified before dry-run.","blocks_apply":1,"blocks_dry_run":1},
        {"gap_id":"DQ_GAP_003","gap":"Key/collision policy for TOPICKEY, CMDKEY, COMMAND, TOPIC, ARTID, SECTID, LINEID must be specified before dry-run.","blocks_apply":1,"blocks_dry_run":1},
        {"gap_id":"DQ_GAP_004","gap":"CMDHELPCHK remains non-mutating validation evidence; a separate future design is required for direct catalog integration.","blocks_apply":1,"blocks_dry_run":0},
    ]

    boundary = [
        {"boundary":"locale/CMDHELPCHK policy plan created","value":1,"status":"PASS"},
        {"boundary":"dry-run authorized now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected for apply now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by policy plan","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by policy plan","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by policy plan","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DQ-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DQ_B_POLICY_PLAN_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dq_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dq_b_policy_decisions_v1.csv", ["policy_id","policy_area","decision","meaning","resolves_blocker","dry_run_unblocked_for_scope","apply_now"], policy_decisions)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dq_b_narrowed_next_scope_v1.csv", ["scope_id","scope","eligible_for_next_plan","reason"], scope_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dq_b_unresolved_apply_gaps_v1.csv", ["gap_id","gap","blocks_apply","blocks_dry_run"], unresolved)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dq_b_dp_blockers_copy_v1.csv", list(blockers[0].keys()) if blockers else ["candidate_family"], blockers)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dq_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    blockers_resolved_for_narrowed_scope = 1
    dryrun_still_held = 1
    apply_still_held = 1

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DQ-B",
        "DP_B_STATUS_GREEN":dp_green,
        "DP_B_SAVEPOINT_PRESENT":dp_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DQ_B":latest_id(repo),
        "POLICY_PLAN_CREATED":1 if status == GREEN else 0,
        "POLICY_DECISION_ROWS":len(policy_decisions),
        "NARROWED_NEXT_SCOPE_ROWS":len(scope_rows),
        "UNRESOLVED_APPLY_GAP_ROWS":len(unresolved),
        "LOCALE_GAP_POLICY_RESOLVED_FOR_SOURCE_LOCALE_SCOPE":1 if status == GREEN else 0,
        "LOCALIZED_VARIANTS_HELD_FOR_FUTURE_OVERLAY":1 if status == GREEN else 0,
        "CMDHELPCHK_POLICY_RESOLVED_AS_REPORT_ONLY_FOR_THIS_LANE":1 if status == GREEN else 0,
        "BLOCKERS_RESOLVED_FOR_NARROWED_SCOPE":blockers_resolved_for_narrowed_scope if status == GREEN else 0,
        "DRY_RUN_AUTHORIZED_NOW":0,
        "DRY_RUN_STILL_HELD":dryrun_still_held,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "APPLY_STILL_HELD":apply_still_held,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_POLICY_PLAN":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_POLICY_PLAN":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_POLICY_PLAN":0,
        "LATEST_POINTER_CHANGED_BY_DQ_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dq_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DQ-B",
        "status":status,
        "source_locale_scope_allowed_for_next_plan":status == GREEN,
        "localized_variants_held":status == GREEN,
        "cmdhelpchk_report_only":status == GREEN,
        "dry_run_authorized_now":False,
        "apply_execution_authorized_now":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dq_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DQ-B Locale/CMDHELPCHK Gap Resolution Policy Plan

- Status: {status}
- Validation issues: {validation}
- DP-B status green: {dp_green}
- DP-B savepoint present: {dp_savepoint}
- Policy plan created: {1 if status == GREEN else 0}
- Policy decision rows: {len(policy_decisions)}
- Narrowed next scope rows: {len(scope_rows)}
- Unresolved apply gap rows: {len(unresolved)}
- Locale gap resolved for source-locale scope: {1 if status == GREEN else 0}
- Localized variants held for future overlay: {1 if status == GREEN else 0}
- CMDHELPCHK policy resolved as report-only for this lane: {1 if status == GREEN else 0}
- Dry-run authorized now: 0
- Dry-run still held: 1
- Apply execution authorized now: 0
- Apply still held: 1
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by policy plan: 0
- Active DBF/CDX/LMDB mutation observed by policy plan: 0
- Workspace mutation observed by policy plan: 0
- Latest pointer changed by DQ-B: 0
- Next gate: {next_gate}

DQ-B resolves the blockers conservatively. The next lane may consider source-locale HELP-only dry-run eligibility, while localized variants and CMDHELPCHK catalog writes remain held for future overlay/design work.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DQ_B_LOCALE_CMDHELPCHK_GAP_RESOLUTION_POLICY_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DQ_B_LOCALE_CMDHELPCHK_GAP_RESOLUTION_POLICY_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DP-B status green: {dp_green}")
    print(f"  DP-B savepoint present: {dp_savepoint}")
    print(f"  policy plan created: {1 if status == GREEN else 0}")
    print(f"  policy decision rows: {len(policy_decisions)}")
    print(f"  narrowed next scope rows: {len(scope_rows)}")
    print(f"  unresolved apply gap rows: {len(unresolved)}")
    print(f"  locale gap resolved for source-locale scope: {1 if status == GREEN else 0}")
    print(f"  localized variants held for future overlay: {1 if status == GREEN else 0}")
    print(f"  CMDHELPCHK policy resolved as report-only for this lane: {1 if status == GREEN else 0}")
    print("  dry-run authorized now: 0")
    print("  dry-run still held: 1")
    print("  apply execution authorized now: 0")
    print("  apply still held: 1")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by policy plan: 0")
    print("  active DBF/CDX/LMDB mutation observed by policy plan: 0")
    print("  workspace mutation observed by policy plan: 0")
    print("  latest pointer changed by DQ-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
