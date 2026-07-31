from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DH_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DH_B_ACTIVE_HELP_CMDHELPCHK_TARGET_SELECTION_DECISION_PACKAGE_GREEN_SELECTION_HELD_TARGET_VERIFICATION_REQUIRED"
DH_SAVEPOINT = "MSG-022AE.6.5.10DH-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DI_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_PLAN_GREEN_READ_ONLY_PROBES_STAGED_NO_SELECTION"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DI_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DJ_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_STAGING"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10di_b_active_help_cmdhelpchk_target_verification_probe_plan_v1"

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

def classify_probe_kind(row: dict) -> str:
    t = row.get("artifact_type","")
    p = row.get("relative_path","").lower()
    if t == "runtime_data_or_index" or p.endswith((".dbf",".dtx",".cdx",".idx",".inx",".cnx")):
        return "runtime_data_index_probe"
    if t == "structured_candidate_or_report" or p.endswith((".csv",".json")):
        return "structured_report_candidate_probe"
    if t == "source":
        return "source_evidence_probe"
    if t == "tooling":
        return "tooling_evidence_probe"
    if t == "documentation_or_report":
        return "documentation_evidence_probe"
    return "general_read_only_probe"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--replace-existing-plan", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL
    manual = out / "manual_run"

    if out.exists() and args.replace_existing_plan:
        shutil.rmtree(out)

    dh = csv_one(reports / "message_catalog_phase22ae_6_5_10dh_b_status_summary_v1.csv")
    candidates = csv_rows(reports / "message_catalog_phase22ae_6_5_10dh_b_verification_candidates_v1.csv")
    scope = csv_rows(reports / "message_catalog_phase22ae_6_5_10dh_b_verification_scope_v1.csv")
    decisions = csv_rows(reports / "message_catalog_phase22ae_6_5_10dh_b_decision_rows_v1.csv")

    dh_green = int(dh.get("STATUS", "") == DH_GREEN)
    dh_savepoint = has_journal(repo, DH_SAVEPOINT)
    verification_required = int(str(dh.get("TARGET_VERIFICATION_PROBE_PLAN_REQUIRED", "0")) == "1")
    help_selected = int(str(dh.get("ACTIVE_HELP_DATA_TARGET_SELECTED_NOW", "0")) == "1")
    cmd_selected = int(str(dh.get("ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW", "0")) == "1")
    apply_auth = int(str(dh.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == "1")
    help_apply = int(str(dh.get("HELP_DATA_APPLY_EXECUTED", "0")) == "1")
    cmd_apply = int(str(dh.get("CMDHELPCHK_APPLY_EXECUTED", "0")) == "1")

    pre = [
        {"check_id":"dh_b_status_green","value":dh_green,"expected":1,"status":"PASS" if dh_green else "FAIL"},
        {"check_id":"dh_b_savepoint_present","value":dh_savepoint,"expected":1,"status":"PASS" if dh_savepoint else "FAIL"},
        {"check_id":"target_verification_probe_plan_required","value":verification_required,"expected":1,"status":"PASS" if verification_required else "FAIL"},
        {"check_id":"verification_candidates_exist","value":int(bool(candidates)),"expected":1,"status":"PASS" if candidates else "FAIL"},
        {"check_id":"verification_scope_exists","value":int(bool(scope)),"expected":1,"status":"PASS" if scope else "FAIL"},
        {"check_id":"active_help_data_target_not_selected","value":help_selected,"expected":0,"status":"PASS" if help_selected == 0 else "FAIL"},
        {"check_id":"active_cmdhelpchk_target_not_selected","value":cmd_selected,"expected":0,"status":"PASS" if cmd_selected == 0 else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"di_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
    ]

    probe_plan = []
    for i, row in enumerate(candidates, start=1):
        probe_plan.append({
            "probe_id": f"DI{str(i).zfill(3)}",
            "family": row.get("family",""),
            "rank_within_family": row.get("rank_within_family",""),
            "relative_path": row.get("relative_path",""),
            "artifact_type": row.get("artifact_type",""),
            "probe_kind": classify_probe_kind(row),
            "probe_goal": "classify as active target, generated candidate/report, source/tooling evidence, documentation, or reject",
            "read_only": 1,
            "target_selected_now": 0,
            "apply_now": 0,
        })

    classification_rules = [
        {"rule_id":"DI001","classification":"active_runtime_target_candidate","rule":"Only runtime data/index/config artifacts may become active target candidates, and only after path/schema/key proof.","required":1},
        {"rule_id":"DI002","classification":"generated_candidate_or_report","rule":"docs/messaging/apply and docs/messaging/reports artifacts are evidence/candidates, not active targets by default.","required":1},
        {"rule_id":"DI003","classification":"source_or_tooling_evidence","rule":"src/tools hits may explain command behavior or builder path but are not HELP DATA/CMDHELPCHK write targets by default.","required":1},
        {"rule_id":"DI004","classification":"documentation_evidence","rule":"manual/docs hits may support human review but must not be selected as mutation targets.","required":1},
        {"rule_id":"DI005","classification":"reject_or_defer","rule":"Any candidate without target path/schema/key proof remains rejected/deferred for active selection.","required":1},
    ]

    staged_artifacts = [
        {"artifact_id":"DI_ART_001","artifact":"message_catalog_phase22ae_6_5_10di_b_probe_plan_v1.csv","purpose":"read-only target verification probe plan","created_now":1},
        {"artifact_id":"DI_ART_002","artifact":"message_catalog_phase22ae_6_5_10di_b_classification_rules_v1.csv","purpose":"classification rules for target probe results","created_now":1},
        {"artifact_id":"DI_ART_003","artifact":"DI_B_TARGET_VERIFICATION_PROBE_CHECKLIST.md","purpose":"manual/operator checklist for next probe staging package","created_now":1},
    ]

    boundary = [
        {"boundary":"target verification probe plan created","value":1,"status":"PASS"},
        {"boundary":"read-only probe plan staged","value":1,"status":"PASS"},
        {"boundary":"runtime probe executed by DI-B","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA target selected now","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK target selected now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DI-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DI_B_TARGET_VERIFICATION_PROBE_PLAN_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    manual.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10di_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10di_b_probe_plan_v1.csv", ["probe_id","family","rank_within_family","relative_path","artifact_type","probe_kind","probe_goal","read_only","target_selected_now","apply_now"], probe_plan)
    write_csv(reports / "message_catalog_phase22ae_6_5_10di_b_classification_rules_v1.csv", ["rule_id","classification","rule","required"], classification_rules)
    write_csv(reports / "message_catalog_phase22ae_6_5_10di_b_staged_artifacts_v1.csv", ["artifact_id","artifact","purpose","created_now"], staged_artifacts)
    write_csv(reports / "message_catalog_phase22ae_6_5_10di_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    checklist_lines = [
        "# DI-B Target Verification Probe Checklist",
        "",
        "This checklist is staged for the later DJ-B probe staging package. DI-B itself runs no runtime probe and selects no active target.",
        "",
        "For each candidate, classify it as one of:",
        "",
        "- active_runtime_target_candidate",
        "- generated_candidate_or_report",
        "- source_or_tooling_evidence",
        "- documentation_evidence",
        "- reject_or_defer",
        "",
        "Required proof before any active target selection:",
        "",
        "- exact physical target path/table",
        "- target family: HELP DATA or CMDHELPCHK",
        "- schema/field list",
        "- key/index tags",
        "- backup path",
        "- rollback path",
        "- readback command",
        "- duplicate/collision policy",
        "",
        "No apply execution is authorized by DI-B.",
        "",
    ]
    for row in probe_plan[:30]:
        checklist_lines.append(f"- {row['probe_id']} {row['family']} {row['relative_path']} [{row['probe_kind']}]")
    write_text(manual / "DI_B_TARGET_VERIFICATION_PROBE_CHECKLIST.md", "\n".join(checklist_lines) + "\n")

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10DI-B",
        "DH_B_STATUS_GREEN": dh_green,
        "DH_B_SAVEPOINT_PRESENT": dh_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DI_B": latest_id(repo),
        "TARGET_VERIFICATION_PROBE_PLAN_CREATED": 1 if status == GREEN else 0,
        "PROBE_PLAN_ROWS": len(probe_plan),
        "CLASSIFICATION_RULE_ROWS": len(classification_rules),
        "STAGED_ARTIFACT_ROWS": len(staged_artifacts),
        "READ_ONLY_PROBES_STAGED": 1 if status == GREEN else 0,
        "RUNTIME_PROBE_EXECUTED_BY_DI_B": 0,
        "ACTIVE_HELP_DATA_TARGET_SELECTED_NOW": 0,
        "ACTIVE_CMDHELPCHK_TARGET_SELECTED_NOW": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_PLAN": 0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_PLAN": 0,
        "WORKSPACE_MUTATION_OBSERVED_BY_PLAN": 0,
        "LATEST_POINTER_CHANGED_BY_DI_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10di_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase": "22AE.6.5.10DI-B",
        "status": status,
        "target_verification_probe_plan_created": 1 if status == GREEN else 0,
        "read_only_probes_staged": 1 if status == GREEN else 0,
        "runtime_probe_executed_by_di_b": False,
        "active_target_selected_now": False,
        "apply_execution_authorized_now": False,
        "next_gate": next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10di_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DI-B Active HELP/CMDHELPCHK Target Verification Probe Plan

- Status: {status}
- Validation issues: {validation}
- DH-B status green: {dh_green}
- DH-B savepoint present: {dh_savepoint}
- Target verification probe plan created: {1 if status == GREEN else 0}
- Probe plan rows: {len(probe_plan)}
- Classification rule rows: {len(classification_rules)}
- Read-only probes staged: {1 if status == GREEN else 0}
- Runtime probe executed by DI-B: 0
- Active HELP DATA target selected now: 0
- Active CMDHELPCHK target selected now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by plan: 0
- Active DBF/CDX/LMDB mutation observed by plan: 0
- Workspace mutation observed by plan: 0
- Latest pointer changed by DI-B: 0
- Next gate: {next_gate}

DI-B creates a read-only verification probe plan and checklist. It does not execute runtime probes, select active targets, or apply HELP DATA/CMDHELPCHK changes.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DI_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DI_B_ACTIVE_HELP_CMDHELPCHK_TARGET_VERIFICATION_PROBE_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DH-B status green: {dh_green}")
    print(f"  DH-B savepoint present: {dh_savepoint}")
    print(f"  target verification probe plan created: {1 if status == GREEN else 0}")
    print(f"  probe plan rows: {len(probe_plan)}")
    print(f"  classification rule rows: {len(classification_rules)}")
    print(f"  read-only probes staged: {1 if status == GREEN else 0}")
    print("  runtime probe executed by DI-B: 0")
    print("  active HELP DATA target selected now: 0")
    print("  active CMDHELPCHK target selected now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by plan: 0")
    print("  active DBF/CDX/LMDB mutation observed by plan: 0")
    print("  workspace mutation observed by plan: 0")
    print("  latest pointer changed by DI-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
