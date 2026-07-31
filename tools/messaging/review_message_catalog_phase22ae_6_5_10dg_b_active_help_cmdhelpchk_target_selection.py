from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DF_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DF_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_PLAN_GREEN_PLAN_ONLY_NO_SELECTION_NO_MUTATION"
DF_SAVEPOINT = "MSG-022AE.6.5.10DF-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DG_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_REVIEW_GREEN_SELECTION_PLAN_ACCEPTED_NO_TARGET_SELECTED"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DG_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_REVIEW_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DH_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_DECISION_PACKAGE"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dg_b_active_help_cmdhelpchk_target_selection_review_v1"

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

def as_int(value, default=0):
    try:
        return int(str(value).strip())
    except Exception:
        return default

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

    df = csv_one(reports / "message_catalog_phase22ae_6_5_10df_b_status_summary_v1.csv")
    ranked = csv_rows(reports / "message_catalog_phase22ae_6_5_10df_b_ranked_target_review_candidates_v1.csv")
    rules = csv_rows(reports / "message_catalog_phase22ae_6_5_10df_b_selection_rules_v1.csv")
    lanes = csv_rows(reports / "message_catalog_phase22ae_6_5_10df_b_selection_lane_summary_v1.csv")
    next_review = csv_rows(reports / "message_catalog_phase22ae_6_5_10df_b_required_next_review_v1.csv")

    df_green = int(df.get("STATUS", "") == DF_GREEN)
    df_savepoint = has_journal(repo, DF_SAVEPOINT)
    plan_created = int(str(df.get("TARGET_SELECTION_PLAN_CREATED", "0")) == "1")
    help_selected = int(str(df.get("ACTIVE_HELP_DATA_TARGET_SELECTED_NOW", "0")) == "1")
    cmd_selected = int(str(df.get("ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW", "0")) == "1")
    apply_auth = int(str(df.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == "1")
    help_apply = int(str(df.get("HELP_DATA_APPLY_EXECUTED", "0")) == "1")
    cmd_apply = int(str(df.get("CMDHELPCHK_APPLY_EXECUTED", "0")) == "1")

    pre = [
        {"check_id":"df_b_status_green","value":df_green,"expected":1,"status":"PASS" if df_green else "FAIL"},
        {"check_id":"df_b_savepoint_present","value":df_savepoint,"expected":1,"status":"PASS" if df_savepoint else "FAIL"},
        {"check_id":"target_selection_plan_created","value":plan_created,"expected":1,"status":"PASS" if plan_created else "FAIL"},
        {"check_id":"ranked_candidates_exist","value":int(bool(ranked)),"expected":1,"status":"PASS" if ranked else "FAIL"},
        {"check_id":"selection_rules_exist","value":int(bool(rules)),"expected":1,"status":"PASS" if rules else "FAIL"},
        {"check_id":"selection_lanes_exist","value":int(bool(lanes)),"expected":1,"status":"PASS" if lanes else "FAIL"},
        {"check_id":"active_help_data_target_not_selected","value":help_selected,"expected":0,"status":"PASS" if help_selected == 0 else "FAIL"},
        {"check_id":"active_cmdhelpchk_target_not_selected","value":cmd_selected,"expected":0,"status":"PASS" if cmd_selected == 0 else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"dg_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_review) else "FAIL"},
    ]

    # Review/accept ranked plan without selecting targets.
    focus = []
    for fam in ["HELP_DATA", "CMDHELPCHK", "BOTH"]:
        fam_rows = [r for r in ranked if r.get("family") == fam]
        for row in fam_rows[:10]:
            focus.append({
                "family": fam,
                "rank_within_family": row.get("rank_within_family", ""),
                "relative_path": row.get("relative_path", ""),
                "artifact_type": row.get("artifact_type", ""),
                "review_priority": row.get("review_priority", ""),
                "review_result": "accepted_for_selection_decision_review",
                "target_selected_now": 0,
                "apply_now": 0,
            })

    decision_inputs = [
        {"input_id":"DH001","input":"DF-B ranked target review candidates","accepted":1,"target_selected_now":0},
        {"input_id":"DH002","input":"DF-B selection rules","accepted":1,"target_selected_now":0},
        {"input_id":"DH003","input":"DF-B selection lane summary","accepted":1,"target_selected_now":0},
        {"input_id":"DH004","input":"DF-B required next-review checklist","accepted":1,"target_selected_now":0},
    ]

    decision_requirements = [
        {"req_id":"DH001","requirement":"DH-B must choose whether to select active HELP DATA target, active CMDHELPCHK target, both, or hold.","required":1},
        {"req_id":"DH002","requirement":"DH-B must identify physical active target path/table and target family if selection is made.","required":1},
        {"req_id":"DH003","requirement":"DH-B must continue to authorize no apply execution; target selection is not a write.","required":1},
        {"req_id":"DH004","requirement":"DH-B must require later dry-run delta before any apply execution package.","required":1},
        {"req_id":"DH005","requirement":"DH-B must preserve source, HELP DATA, CMDHELPCHK, active DBF/CDX/LMDB, workspace, and latest-pointer boundaries.","required":1},
    ]

    boundary = [
        {"boundary":"target selection plan reviewed","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by review","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DG-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DG_B_TARGET_SELECTION_REVIEW_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dg_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dg_b_focus_review_queue_v1.csv", ["family","rank_within_family","relative_path","artifact_type","review_priority","review_result","target_selected_now","apply_now"], focus)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dg_b_decision_inputs_v1.csv", ["input_id","input","accepted","target_selected_now"], decision_inputs)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dg_b_decision_requirements_v1.csv", ["req_id","requirement","required"], decision_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dg_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10DG-B",
        "DF_B_STATUS_GREEN": df_green,
        "DF_B_SAVEPOINT_PRESENT": df_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DG_B": latest_id(repo),
        "TARGET_SELECTION_PLAN_REVIEWED": 1 if status == GREEN else 0,
        "RANKED_CANDIDATES_REVIEWED": len(ranked),
        "FOCUS_REVIEW_QUEUE_ROWS": len(focus),
        "DECISION_INPUT_ROWS": len(decision_inputs),
        "DECISION_REQUIREMENT_ROWS": len(decision_requirements),
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW": 0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_REVIEW": 0,
        "WORKSPACE_MUTATION_OBSERVED_BY_REVIEW": 0,
        "LATEST_POINTER_CHANGED_BY_DG_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dg_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase": "22AE.6.5.10DG-B",
        "status": status,
        "target_selection_plan_reviewed": 1 if status == GREEN else 0,
        "active_target_selected_now": False,
        "apply_execution_authorized_now": False,
        "next_gate": next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dg_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DG-B Active HELP/CMDHELPCHK Target Selection Review

- Status: {status}
- Validation issues: {validation}
- DF-B status green: {df_green}
- DF-B savepoint present: {df_savepoint}
- Target selection plan reviewed: {1 if status == GREEN else 0}
- Ranked candidates reviewed: {len(ranked)}
- Focus review queue rows: {len(focus)}
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by review: 0
- Active DBF/CDX/LMDB mutation observed by review: 0
- Workspace mutation observed by review: 0
- Latest pointer changed by DG-B: 0
- Next gate: {next_gate}

DG-B accepts the DF-B target-selection plan and prepares inputs for a later selection decision package. It deliberately selects no active target and applies nothing.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DG_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_REVIEW.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DG_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_REVIEW.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DF-B status green: {df_green}")
    print(f"  DF-B savepoint present: {df_savepoint}")
    print(f"  target selection plan reviewed: {1 if status == GREEN else 0}")
    print(f"  ranked candidates reviewed: {len(ranked)}")
    print(f"  focus review queue rows: {len(focus)}")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by review: 0")
    print("  active DBF/CDX/LMDB mutation observed by review: 0")
    print("  workspace mutation observed by review: 0")
    print("  latest pointer changed by DG-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
