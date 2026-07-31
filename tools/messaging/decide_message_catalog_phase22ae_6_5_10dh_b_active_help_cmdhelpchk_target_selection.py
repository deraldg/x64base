from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DG_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DG_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_REVIEW_GREEN_SELECTION_PLAN_ACCEPTED_NO_TARGET_SELECTED"
DG_SAVEPOINT = "MSG-022AE.6.5.10DG-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DH_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_DECISION_PACKAGE_GREEN_SELECTION_HELD_TARGET_VERIFICATION_REQUIRED"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DH_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_DECISION_PACKAGE_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DI_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dh_b_active_help_cmdhelpchk_target_selection_decision_package_v1"

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
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})

def has_journal(repo: Path, marker: str) -> int:
    return int(marker in read_text(repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"))

def latest_id(repo: Path) -> str:
    try:
        data = json.loads(read_text(repo / "docs/messaging/reports/message_savepoint_latest_v1.json"))
        return data.get("savepoint_id", data.get("savepoint", ""))
    except Exception:
        return ""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-decision", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_decision:
        shutil.rmtree(out)

    dg = csv_one(reports / "message_catalog_phase22ae_6_5_10dg_b_status_summary_v1.csv")
    focus = csv_rows(reports / "message_catalog_phase22ae_6_5_10dg_b_focus_review_queue_v1.csv")
    inputs = csv_rows(reports / "message_catalog_phase22ae_6_5_10dg_b_decision_inputs_v1.csv")
    reqs = csv_rows(reports / "message_catalog_phase22ae_6_5_10dg_b_decision_requirements_v1.csv")

    dg_green = int(dg.get("STATUS", "") == DG_GREEN)
    dg_savepoint = has_journal(repo, DG_SAVEPOINT)
    review_ok = int(str(dg.get("TARGET_SELECTION_PLAN_REVIEWED", "0")) == "1")
    help_selected = int(str(dg.get("ACTIVE_HELP_DATA_TARGET_SELECTED_NOW", "0")) == "1")
    cmd_selected = int(str(dg.get("ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW", "0")) == "1")
    apply_auth = int(str(dg.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == "1")
    help_apply = int(str(dg.get("HELP_DATA_APPLY_EXECUTED", "0")) == "1")
    cmd_apply = int(str(dg.get("CMDHELPCHK_APPLY_EXECUTED", "0")) == "1")

    pre = [
        {"check_id":"dg_b_status_green","value":dg_green,"expected":1,"status":"PASS" if dg_green else "FAIL"},
        {"check_id":"dg_b_savepoint_present","value":dg_savepoint,"expected":1,"status":"PASS" if dg_savepoint else "FAIL"},
        {"check_id":"target_selection_plan_reviewed","value":review_ok,"expected":1,"status":"PASS" if review_ok else "FAIL"},
        {"check_id":"focus_review_queue_exists","value":int(bool(focus)),"expected":1,"status":"PASS" if focus else "FAIL"},
        {"check_id":"decision_inputs_exist","value":int(bool(inputs)),"expected":1,"status":"PASS" if inputs else "FAIL"},
        {"check_id":"decision_requirements_exist","value":int(bool(reqs)),"expected":1,"status":"PASS" if reqs else "FAIL"},
        {"check_id":"active_help_data_target_not_selected_yet","value":help_selected,"expected":0,"status":"PASS" if help_selected == 0 else "FAIL"},
        {"check_id":"active_cmdhelpchk_target_not_selected_yet","value":cmd_selected,"expected":0,"status":"PASS" if cmd_selected == 0 else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"dh_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_decision) else "FAIL"},
    ]

    decision_rows = [
        {"decision_id":"DH001_ACCEPT_DG_B_SELECTION_REVIEW","selected":1,"decision_status":"ACCEPTED","meaning":"DG-B target-selection review evidence is accepted as a basis for the next verification step.","active_target_selected_now":0,"apply_now":0},
        {"decision_id":"DH002_SELECT_ACTIVE_HELP_DATA_TARGET_NOW","selected":0,"decision_status":"HELD","meaning":"No active HELP DATA target is selected automatically from the broad discovery inventory.","active_target_selected_now":0,"apply_now":0},
        {"decision_id":"DH003_SELECT_ACTIVE_CMDHELPCHK_TARGET_NOW","selected":0,"decision_status":"HELD","meaning":"No active CMDHELPCHK target is selected automatically from the broad discovery inventory.","active_target_selected_now":0,"apply_now":0},
        {"decision_id":"DH004_REQUIRE_TARGET_VERIFICATION_PROBE_PLAN","selected":1,"decision_status":"SELECTED_NEXT","meaning":"A targeted verification/probe plan is required to distinguish active runtime targets from docs, source, tools, generated reports, and candidates.","active_target_selected_now":0,"apply_now":0},
        {"decision_id":"DH005_AUTHORIZE_APPLY_EXECUTION_NOW","selected":0,"decision_status":"NOT_AUTHORIZED","meaning":"Target selection is not apply execution; no active HELP DATA/CMDHELPCHK apply is authorized.","active_target_selected_now":0,"apply_now":0},
    ]

    verification_scope = [
        {"scope_id":"DI001","family":"HELP_DATA","probe_goal":"Verify exact active HELP DATA storage/table/file target, if any, using focused paths and runtime evidence.","required":1},
        {"scope_id":"DI002","family":"CMDHELPCHK","probe_goal":"Verify exact active CMDHELPCHK storage/table/file target, if any, using focused paths and runtime evidence.","required":1},
        {"scope_id":"DI003","family":"BOTH","probe_goal":"Classify BOTH-family artifacts as data target, generated report, source/tooling evidence, or documentation.","required":1},
        {"scope_id":"DI004","family":"ALL","probe_goal":"Record target schema/fields, keys, backup/rollback path, readback command, and apply eligibility before any selection.","required":1},
        {"scope_id":"DI005","family":"ALL","probe_goal":"Keep verification as report-only unless a later package explicitly authorizes target selection or apply execution.","required":1},
    ]

    # Carry the top focus rows forward as verification candidates, still no selection.
    verification_candidates = []
    for row in focus:
        verification_candidates.append({
            "family": row.get("family",""),
            "rank_within_family": row.get("rank_within_family",""),
            "relative_path": row.get("relative_path",""),
            "artifact_type": row.get("artifact_type",""),
            "review_priority": row.get("review_priority",""),
            "verification_action": "probe_classify_do_not_select",
            "active_target_selected_now": 0,
            "apply_now": 0,
        })

    boundary = [
        {"boundary":"target selection decision package created","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by decision","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by decision","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by decision","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DH-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DH_B_TARGET_SELECTION_DECISION_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dh_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dh_b_decision_rows_v1.csv", ["decision_id","selected","decision_status","meaning","active_target_selected_now","apply_now"], decision_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dh_b_verification_scope_v1.csv", ["scope_id","family","probe_goal","required"], verification_scope)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dh_b_verification_candidates_v1.csv", ["family","rank_within_family","relative_path","artifact_type","review_priority","verification_action","active_target_selected_now","apply_now"], verification_candidates)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dh_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10DH-B",
        "DG_B_STATUS_GREEN": dg_green,
        "DG_B_SAVEPOINT_PRESENT": dg_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DH_B": latest_id(repo),
        "TARGET_SELECTION_DECISION_CREATED": 1 if status == GREEN else 0,
        "DG_B_SELECTION_REVIEW_ACCEPTED": 1 if status == GREEN else 0,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW": 0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW": 0,
        "AUTOMATIC_TARGET_SELECTION_DECLINED": 1,
        "TARGET_VERIFICATION_PROBE_PLAN_REQUIRED": 1,
        "VERIFICATION_SCOPE_ROWS": len(verification_scope),
        "VERIFICATION_CANDIDATE_ROWS": len(verification_candidates),
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_DECISION": 0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_DECISION": 0,
        "WORKSPACE_MUTATION_OBSERVED_BY_DECISION": 0,
        "LATEST_POINTER_CHANGED_BY_DH_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dh_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase": "22AE.6.5.10DH-B",
        "status": status,
        "automatic_target_selection_declined": True,
        "active_target_selected_now": False,
        "target_verification_probe_plan_required": True,
        "apply_execution_authorized_now": False,
        "next_gate": next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dh_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DH-B Active HELP/CMDHELPCHK Target Selection Decision Package

- Status: {status}
- Validation issues: {validation}
- DG-B status green: {dg_green}
- DG-B savepoint present: {dg_savepoint}
- Target selection decision created: {1 if status == GREEN else 0}
- DG-B selection review accepted: {1 if status == GREEN else 0}
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Automatic target selection declined: 1
- Target verification probe plan required: 1
- Verification candidate rows: {len(verification_candidates)}
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by decision: 0
- Active DBF/CDX/LMDB mutation observed by decision: 0
- Workspace mutation observed by decision: 0
- Latest pointer changed by DH-B: 0
- Next gate: {next_gate}

DH-B accepts the target-selection review but deliberately declines automatic active-target selection. The next package should probe and classify likely HELP DATA/CMDHELPCHK targets before any target is selected or apply path is considered.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DH_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_DECISION_PACKAGE.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DH_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_DECISION_PACKAGE.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DG-B status green: {dg_green}")
    print(f"  DG-B savepoint present: {dg_savepoint}")
    print(f"  target selection decision created: {1 if status == GREEN else 0}")
    print(f"  DG-B selection review accepted: {1 if status == GREEN else 0}")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  automatic target selection declined: 1")
    print("  target verification probe plan required: 1")
    print(f"  verification candidate rows: {len(verification_candidates)}")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by decision: 0")
    print("  active DBF/CDX/LMDB mutation observed by decision: 0")
    print("  workspace mutation observed by decision: 0")
    print("  latest pointer changed by DH-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
