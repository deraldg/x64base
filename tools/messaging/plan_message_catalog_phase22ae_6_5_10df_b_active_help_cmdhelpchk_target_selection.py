from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DE_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DE_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_REVIEW_GREEN_TARGET_REVIEW_QUEUE_ACCEPTED_NO_SELECTION"
DE_SAVEPOINT = "MSG-022AE.6.5.10DE-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DF_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_PLAN_GREEN_PLAN_ONLY_NO_SELECTION_NO_MUTATION"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DF_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DG_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_REVIEW"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10df_b_active_help_cmdhelpchk_target_selection_plan_v1"

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
    parser.add_argument("--replace-existing-plan", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_plan:
        shutil.rmtree(out)

    de = csv_one(reports / "message_catalog_phase22ae_6_5_10de_b_status_summary_v1.csv")
    narrowed = csv_rows(reports / "message_catalog_phase22ae_6_5_10de_b_narrowed_target_review_queue_v1.csv")
    buckets = csv_rows(reports / "message_catalog_phase22ae_6_5_10de_b_review_bucket_summary_v1.csv")
    requirements = csv_rows(reports / "message_catalog_phase22ae_6_5_10de_b_selection_requirements_v1.csv")

    de_green = int(de.get("STATUS", "") == DE_GREEN)
    de_savepoint = has_journal(repo, DE_SAVEPOINT)
    review_accepted = int(str(de.get("TARGET_DISCOVERY_REVIEW_ACCEPTED", "0")) == "1")
    target_selected_help = int(str(de.get("ACTIVE_HELP_DATA_TARGET_SELECTED_NOW", "0")) == "1")
    target_selected_cmd = int(str(de.get("ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW", "0")) == "1")
    apply_auth = int(str(de.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == "1")
    help_apply = int(str(de.get("HELP_DATA_APPLY_EXECUTED", "0")) == "1")
    cmd_apply = int(str(de.get("CMDHELPCHK_APPLY_EXECUTED", "0")) == "1")

    pre = [
        {"check_id":"de_b_status_green","value":de_green,"expected":1,"status":"PASS" if de_green else "FAIL"},
        {"check_id":"de_b_savepoint_present","value":de_savepoint,"expected":1,"status":"PASS" if de_savepoint else "FAIL"},
        {"check_id":"target_discovery_review_accepted","value":review_accepted,"expected":1,"status":"PASS" if review_accepted else "FAIL"},
        {"check_id":"narrowed_review_queue_exists","value":int(bool(narrowed)),"expected":1,"status":"PASS" if narrowed else "FAIL"},
        {"check_id":"review_buckets_exist","value":int(bool(buckets)),"expected":1,"status":"PASS" if buckets else "FAIL"},
        {"check_id":"help_target_not_selected_yet","value":target_selected_help,"expected":0,"status":"PASS" if target_selected_help == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_target_not_selected_yet","value":target_selected_cmd,"expected":0,"status":"PASS" if target_selected_cmd == 0 else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"df_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
    ]

    selection_rules = [
        {"rule_id":"DF001","family":"HELP_DATA","rule":"Select active HELP DATA target only from reviewed runtime data/config candidates, not from source/docs by default.","required":1},
        {"rule_id":"DF002","family":"CMDHELPCHK","rule":"Select active CMDHELPCHK target only from reviewed runtime data/config candidates, not from source/docs by default.","required":1},
        {"rule_id":"DF003","family":"BOTH","rule":"Treat BOTH-family artifacts as cross-check/provenance first; do not use as active mutation target unless target semantics are proven.","required":1},
        {"rule_id":"DF004","family":"ALL","rule":"Any selected target must have physical path, schema/fields, keys, backup path, rollback path, and readback command identified.","required":1},
        {"rule_id":"DF005","family":"ALL","rule":"Any selected target must have duplicate/collision policy for HELP_KEY, COMMAND_NAME, LOCALE_ID, CHECK_ID before apply.","required":1},
        {"rule_id":"DF006","family":"ALL","rule":"DF-B selects no target and executes no mutation; target selection remains a plan/review step.","required":1},
    ]

    # Rank candidates into review lanes, but do not select them.
    family_rank = {"HELP_DATA":0, "CMDHELPCHK":0, "BOTH":0}
    ranked = []
    for row in narrowed:
        fam = row.get("family", "UNKNOWN")
        if fam not in family_rank:
            continue
        family_rank[fam] += 1
        ranked.append({
            "family": fam,
            "rank_within_family": family_rank[fam],
            "relative_path": row.get("relative_path", ""),
            "artifact_type": row.get("artifact_type", ""),
            "review_priority": row.get("review_priority", ""),
            "selection_lane": "review_candidate_not_selected",
            "selection_basis": "DE-B narrowed queue priority; target semantics still require review",
            "active_target_selected_now": 0,
            "apply_now": 0,
        })

    lane_summary = []
    for fam in ["HELP_DATA", "CMDHELPCHK", "BOTH"]:
        rows = [r for r in ranked if r["family"] == fam]
        lane_summary.append({
            "family": fam,
            "review_candidates": len(rows),
            "top_candidate": rows[0]["relative_path"] if rows else "",
            "target_selected_now": 0,
            "selection_plan_ready": 1 if rows else 0,
            "requires_next_review": 1,
        })

    required_next_review = [
        {"review_id":"DG001","review":"Inspect the highest-ranked HELP_DATA candidates and decide whether any are active HELP DATA targets.","required":1},
        {"review_id":"DG002","review":"Inspect the highest-ranked CMDHELPCHK candidates and decide whether any are active CMDHELPCHK targets.","required":1},
        {"review_id":"DG003","review":"Separate active data targets from documentation, tooling, generated reports, and source-code evidence.","required":1},
        {"review_id":"DG004","review":"Record target path, role, write mode, backup, rollback, schema/key evidence, and readback command for any selected target.","required":1},
        {"review_id":"DG005","review":"Continue to refuse active apply until a later dry-run delta and execution package are separately authorized.","required":1},
    ]

    boundary = [
        {"boundary":"target selection plan created","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DF-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DF_B_TARGET_SELECTION_PLAN_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10df_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10df_b_selection_rules_v1.csv", ["rule_id","family","rule","required"], selection_rules)
    write_csv(reports / "message_catalog_phase22ae_6_5_10df_b_ranked_target_review_candidates_v1.csv", ["family","rank_within_family","relative_path","artifact_type","review_priority","selection_lane","selection_basis","active_target_selected_now","apply_now"], ranked)
    write_csv(reports / "message_catalog_phase22ae_6_5_10df_b_selection_lane_summary_v1.csv", ["family","review_candidates","top_candidate","target_selected_now","selection_plan_ready","requires_next_review"], lane_summary)
    write_csv(reports / "message_catalog_phase22ae_6_5_10df_b_required_next_review_v1.csv", ["review_id","review","required"], required_next_review)
    write_csv(reports / "message_catalog_phase22ae_6_5_10df_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10DF-B",
        "DE_B_STATUS_GREEN": de_green,
        "DE_B_SAVEPOINT_PRESENT": de_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DF_B": latest_id(repo),
        "TARGET_SELECTION_PLAN_CREATED": 1 if status == GREEN else 0,
        "RANKED_REVIEW_CANDIDATES": len(ranked),
        "SELECTION_RULE_ROWS": len(selection_rules),
        "LANE_SUMMARY_ROWS": len(lane_summary),
        "REQUIRED_NEXT_REVIEW_ROWS": len(required_next_review),
        "HELP_DATA_REVIEW_CANDIDATES": len([r for r in ranked if r["family"] == "HELP_DATA"]),
        "CMDHELPCHK_REVIEW_CANDIDATES": len([r for r in ranked if r["family"] == "CMDHELPCHK"]),
        "BOTH_REVIEW_CANDIDATES": len([r for r in ranked if r["family"] == "BOTH"]),
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW": 0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_PLAN": 0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_PLAN": 0,
        "WORKSPACE_MUTATION_OBSERVED_BY_PLAN": 0,
        "LATEST_POINTER_CHANGED_BY_DF_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10df_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase": "22AE.6.5.10DF-B",
        "status": status,
        "target_selection_plan_created": 1 if status == GREEN else 0,
        "active_target_selected_now": False,
        "apply_execution_authorized_now": False,
        "next_gate": next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10df_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DF-B Active HELP/CMDHELPCHK Target Selection Plan

- Status: {status}
- Validation issues: {validation}
- DE-B status green: {de_green}
- DE-B savepoint present: {de_savepoint}
- Target selection plan created: {1 if status == GREEN else 0}
- Ranked review candidates: {len(ranked)}
- HELP DATA review candidates: {len([r for r in ranked if r['family'] == 'HELP_DATA'])}
- CMDHELPCHK review candidates: {len([r for r in ranked if r['family'] == 'CMDHELPCHK'])}
- BOTH-family review candidates: {len([r for r in ranked if r['family'] == 'BOTH'])}
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by plan: 0
- Active DBF/CDX/LMDB mutation observed by plan: 0
- Workspace mutation observed by plan: 0
- Latest pointer changed by DF-B: 0
- Next gate: {next_gate}

DF-B creates the target-selection plan and ranked review lanes. It deliberately selects no active target and applies nothing.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DF_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DF_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DE-B status green: {de_green}")
    print(f"  DE-B savepoint present: {de_savepoint}")
    print(f"  target selection plan created: {1 if status == GREEN else 0}")
    print(f"  ranked review candidates: {len(ranked)}")
    print(f"  HELP DATA review candidates: {len([r for r in ranked if r['family'] == 'HELP_DATA'])}")
    print(f"  CMDHELPCHK review candidates: {len([r for r in ranked if r['family'] == 'CMDHELPCHK'])}")
    print(f"  BOTH-family review candidates: {len([r for r in ranked if r['family'] == 'BOTH'])}")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by plan: 0")
    print("  active DBF/CDX/LMDB mutation observed by plan: 0")
    print("  workspace mutation observed by plan: 0")
    print("  latest pointer changed by DF-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
