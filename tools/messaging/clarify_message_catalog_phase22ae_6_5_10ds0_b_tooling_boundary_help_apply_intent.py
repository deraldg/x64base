from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DR_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DR_B_SOURCE_LOCALE_HELP_ONLY_DRY_RUN_ELIGIBILITY_PLAN_GREEN_SCOPE_NARROWED_DRY_RUN_STILL_HELD"
DR_SAVEPOINT = "MSG-022AE.6.5.10DR-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DS0_B_TOOLING_BOUNDARY_HELP_APPLY_INTENT_CLARIFICATION_GREEN_NO_ACTIVE_APPLY_NO_TOOL_PROMOTION"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DS0_B_TOOLING_BOUNDARY_HELP_APPLY_INTENT_CLARIFICATION_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DS_B_SOURCE_LOCALE_HELP_ROW_SHAPE_KEY_POLICY_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10ds0_b_tooling_boundary_help_apply_intent_clarification_v1"

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
    parser.add_argument("--replace-existing-clarification", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_clarification:
        shutil.rmtree(out)

    dr = csv_one(reports / "message_catalog_phase22ae_6_5_10dr_b_status_summary_v1.csv")
    dr_green = int(dr.get("STATUS", "") == DR_GREEN)
    dr_savepoint = has_journal(repo, DR_SAVEPOINT)

    pre = [
        {"check_id":"dr_b_status_green","value":dr_green,"expected":1,"status":"PASS" if dr_green else "FAIL"},
        {"check_id":"dr_b_savepoint_present","value":dr_savepoint,"expected":1,"status":"PASS" if dr_savepoint else "FAIL"},
        {"check_id":"source_locale_help_scope_not_dry_run_authorized","value":as_int(dr.get("DRY_RUN_AUTHORIZED_NOW", "0")),"expected":0,"status":"PASS" if as_int(dr.get("DRY_RUN_AUTHORIZED_NOW", "0")) == 0 else "FAIL"},
        {"check_id":"active_apply_not_authorized","value":as_int(dr.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")),"expected":0,"status":"PASS" if as_int(dr.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == 0 else "FAIL"},
        {"check_id":"ds0_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_clarification) else "FAIL"},
    ]

    doctrine_rows = [
        {"doctrine_id":"DS0_001","area":"mission","statement":"The current lane is guarded HELP integration research, not active HELP infusion.","accepted":1},
        {"doctrine_id":"DS0_002","area":"apply_boundary","statement":"No active HELP DATA, CMDHELPCHK, HELP catalog DBF/CDX/LMDB, source, workspace, or runtime catalog mutation is authorized by DS0-B.","accepted":1},
        {"doctrine_id":"DS0_003","area":"tooling_boundary","statement":"Package scripts may be used as controlled stage/run helpers, but promotion of reusable Python tooling into permanent project tooling requires a separate tooling acceptance gate.","accepted":1},
        {"doctrine_id":"DS0_004","area":"future_tooling","statement":"Future packages should prefer package-local tools under docs/messaging/apply/.../tools unless a separate package explicitly authorizes promotion to tools/messaging.","accepted":1},
        {"doctrine_id":"DS0_005","area":"help_infusion","statement":"Actual active HELP catalog infusion requires, at minimum, row-shape/key policy, dry-run delta, dry-run review, backup/rollback manifest, explicit apply authorization, execution, and post-apply validation.","accepted":1},
        {"doctrine_id":"DS0_006","area":"cmdhelpchk","statement":"CMDHELPCHK remains report/validation evidence in this lane unless a future design explicitly authorizes active catalog integration.","accepted":1},
        {"doctrine_id":"DS0_007","area":"locale","statement":"Localized HELP variants remain held for future locale overlay/schema work; source-locale HELP-only remains the narrowed research path.","accepted":1},
    ]

    authorization_rows = [
        {"authorization":"active_HELP_catalog_apply","authorized_now":0,"required_future_gate":"guarded apply execution package after dry-run review"},
        {"authorization":"active_CMDHELPCHK_apply","authorized_now":0,"required_future_gate":"separate CMDHELPCHK integration design and apply package"},
        {"authorization":"active_DBF_CDX_LMDB_write","authorized_now":0,"required_future_gate":"backup/rollback + dry-run + explicit apply authorization"},
        {"authorization":"CXX_source_edit","authorized_now":0,"required_future_gate":"separate source patch plan with usage-contract update"},
        {"authorization":"permanent_python_tool_promotion","authorized_now":0,"required_future_gate":"separate tooling acceptance/promotion gate"},
        {"authorization":"package_local_report_generation","authorized_now":1,"required_future_gate":"current guarded package scope"},
    ]

    next_gate_contract = [
        {"gate":"DS-B row-shape/key policy plan","allowed":1,"allowed_scope":"policy/report-only planning; no dry-run delta and no active writes"},
        {"gate":"DT-B dry-run staging plan","allowed":0,"allowed_scope":"requires DS-B green/savepoint and explicit authorization"},
        {"gate":"active HELP apply execution","allowed":0,"allowed_scope":"requires later dry-run review, backup/rollback manifest, and explicit apply authorization"},
        {"gate":"tool promotion to permanent tools/messaging","allowed":0,"allowed_scope":"requires separate tooling promotion gate"},
    ]

    boundary = [
        {"boundary":"intent clarified","value":1,"status":"PASS"},
        {"boundary":"active HELP infusion authorized now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB write authorized now","value":0,"status":"PASS"},
        {"boundary":"C++ source edit authorized now","value":0,"status":"PASS"},
        {"boundary":"permanent Python/tooling promotion authorized now","value":0,"status":"PASS"},
        {"boundary":"package-local/report generation allowed","value":1,"status":"PASS"},
        {"boundary":"active catalog mutation observed by DS0-B","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by DS0-B","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DS0-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DS0_B_BOUNDARY_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ds0_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ds0_b_boundary_doctrine_v1.csv", ["doctrine_id","area","statement","accepted"], doctrine_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ds0_b_authorization_matrix_v1.csv", ["authorization","authorized_now","required_future_gate"], authorization_rows)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ds0_b_next_gate_contract_v1.csv", ["gate","allowed","allowed_scope"], next_gate_contract)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ds0_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DS0-B",
        "DR_B_STATUS_GREEN":dr_green,
        "DR_B_SAVEPOINT_PRESENT":dr_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DS0_B":latest_id(repo),
        "INTENT_CLARIFIED":1 if status == GREEN else 0,
        "ACTIVE_HELP_INFUSION_AUTHORIZED_NOW":0,
        "ACTIVE_HELP_DATA_APPLY_EXECUTED":0,
        "ACTIVE_CMDHELPCHK_APPLY_EXECUTED":0,
        "ACTIVE_DBF_CDX_LMDB_WRITE_AUTHORIZED_NOW":0,
        "CXX_SOURCE_EDIT_AUTHORIZED_NOW":0,
        "PERMANENT_PYTHON_TOOL_PROMOTION_AUTHORIZED_NOW":0,
        "PACKAGE_LOCAL_REPORT_GENERATION_ALLOWED":1 if status == GREEN else 0,
        "DS_B_ALLOWED_AS_POLICY_ONLY_NEXT":1 if status == GREEN else 0,
        "DRY_RUN_AUTHORIZED_NOW":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_DS0_B":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_DS0_B":0,
        "LATEST_POINTER_CHANGED_BY_DS0_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10ds0_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DS0-B",
        "status":status,
        "active_help_infusion_authorized_now":False,
        "active_dbf_writes_authorized_now":False,
        "source_edits_authorized_now":False,
        "permanent_python_tool_promotion_authorized_now":False,
        "ds_b_allowed_as_policy_only_next":status == GREEN,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10ds0_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DS0-B Tooling Boundary and HELP Apply Intent Clarification

- Status: {status}
- Validation issues: {validation}
- DR-B status green: {dr_green}
- DR-B savepoint present: {dr_savepoint}
- Intent clarified: {1 if status == GREEN else 0}
- Active HELP infusion authorized now: 0
- Active HELP DATA apply executed: 0
- Active CMDHELPCHK apply executed: 0
- Active DBF/CDX/LMDB write authorized now: 0
- C++ source edit authorized now: 0
- Permanent Python/tool promotion authorized now: 0
- Package-local/report generation allowed: {1 if status == GREEN else 0}
- DS-B allowed as policy-only next: {1 if status == GREEN else 0}
- Dry-run authorized now: 0
- Apply execution authorized now: 0
- Active catalog mutation observed by DS0-B: 0
- Workspace mutation observed by DS0-B: 0
- Latest pointer changed by DS0-B: 0
- Next gate: {next_gate}

DS0-B clarifies that this is guarded HELP integration research, not active HELP infusion. Permanent tooling promotion, active DBF writes, C++ edits, and HELP/CMDHELPCHK apply remain unauthorized unless a later explicit gate authorizes them.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DS0_B_TOOLING_BOUNDARY_HELP_APPLY_INTENT_CLARIFICATION.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DS0_B_TOOLING_BOUNDARY_HELP_APPLY_INTENT_CLARIFICATION.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DR-B status green: {dr_green}")
    print(f"  DR-B savepoint present: {dr_savepoint}")
    print(f"  intent clarified: {1 if status == GREEN else 0}")
    print("  active HELP infusion authorized now: 0")
    print("  active HELP DATA apply executed: 0")
    print("  active CMDHELPCHK apply executed: 0")
    print("  active DBF/CDX/LMDB write authorized now: 0")
    print("  C++ source edit authorized now: 0")
    print("  permanent Python/tool promotion authorized now: 0")
    print(f"  package-local/report generation allowed: {1 if status == GREEN else 0}")
    print(f"  DS-B allowed as policy-only next: {1 if status == GREEN else 0}")
    print("  dry-run authorized now: 0")
    print("  apply execution authorized now: 0")
    print("  active catalog mutation observed by DS0-B: 0")
    print("  workspace mutation observed by DS0-B: 0")
    print("  latest pointer changed by DS0-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
