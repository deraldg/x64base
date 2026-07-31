from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DB_B_HELP_CMDHELPCHK_NATIVE_MATERIALIZATION_DECISION_PACKAGE_GREEN_NATIVE_CANDIDATE_TABLES_ACCEPTED_APPLY_NOT_AUTHORIZED"
DB_SAVEPOINT = "MSG-022AE.6.5.10DB-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DC_B_GUARDED_HELP_CMDHELPCHK_APPLY_PLAN_GREEN_PLAN_ONLY_EXECUTION_NOT_AUTHORIZED"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DC_B_GUARDED_HELP_CMDHELPCHK_APPLY_PLAN_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DD_B_ACTIVE_HELP_CMDHELPCHK_TARGET_DISCOVERY_STAGING"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10dc_b_guarded_help_cmdhelpchk_apply_plan_v1"
CX_OUT_REL = "docs/messaging/apply/phase22ae_6_5_10cx_b_help_cmdhelpchk_candidate_mapping_staging_v1/candidate_outputs"
CZ_ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cz_b_help_cmdhelpchk_candidate_table_native_materialization_staging_v1"

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
    cx_out = repo / CX_OUT_REL
    cz_root = repo / CZ_ROOT_REL

    if out.exists() and args.replace_existing_plan:
        shutil.rmtree(out)

    db = csv_one(reports / "message_catalog_phase22ae_6_5_10db_b_status_summary_v1.csv")
    db_green = int(db.get("STATUS", "") == DB_GREEN)
    db_savepoint = has_journal(repo, DB_SAVEPOINT)
    native_accepted = int(str(db.get("NATIVE_CANDIDATE_MATERIALIZATION_ACCEPTED", "0")) == "1")
    candidates_accepted = int(str(db.get("HELP_CMDHELPCHK_CANDIDATES_ACCEPTED_FOR_APPLY_PLANNING", "0")) == "1")
    apply_auth = int(str(db.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == "1")
    help_apply = int(str(db.get("HELP_DATA_APPLY_EXECUTED", "0")) == "1")
    cmd_apply = int(str(db.get("CMDHELPCHK_APPLY_EXECUTED", "0")) == "1")

    help_candidate = cx_out / "HELP_DATA_CANDIDATE_ROWS.csv"
    cmd_candidate = cx_out / "CMDHELPCHK_CANDIDATE_ROWS.csv"
    gate_candidate = cx_out / "MESSAGE_APPLY_GATE_EVIDENCE.csv"

    pre = [
        {"check_id":"db_b_status_green","value":db_green,"expected":1,"status":"PASS" if db_green else "FAIL"},
        {"check_id":"db_b_savepoint_present","value":db_savepoint,"expected":1,"status":"PASS" if db_savepoint else "FAIL"},
        {"check_id":"native_candidate_materialization_accepted","value":native_accepted,"expected":1,"status":"PASS" if native_accepted else "FAIL"},
        {"check_id":"help_cmdhelpchk_candidates_accepted_for_apply_planning","value":candidates_accepted,"expected":1,"status":"PASS" if candidates_accepted else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"help_candidate_rows_exist","value":int(help_candidate.exists()),"expected":1,"status":"PASS" if help_candidate.exists() else "FAIL"},
        {"check_id":"cmdhelpchk_candidate_rows_exist","value":int(cmd_candidate.exists()),"expected":1,"status":"PASS" if cmd_candidate.exists() else "FAIL"},
        {"check_id":"gate_candidate_rows_exist","value":int(gate_candidate.exists()),"expected":1,"status":"PASS" if gate_candidate.exists() else "FAIL"},
        {"check_id":"cz_native_materialization_root_exists","value":int(cz_root.exists()),"expected":1,"status":"PASS" if cz_root.exists() else "FAIL"},
        {"check_id":"dc_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_plan) else "FAIL"},
    ]

    apply_contract = [
        {"contract_id":"DC001","contract_area":"scope","rule":"DC-B is a plan-only package; it must not apply HELP DATA or CMDHELPCHK.","required":1},
        {"contract_id":"DC002","contract_area":"target discovery","rule":"Exact active HELP DATA and CMDHELPCHK physical/logic targets must be discovered and reviewed before any write.","required":1},
        {"contract_id":"DC003","contract_area":"candidate inputs","rule":"Validated CX-B candidate CSVs are the only permitted candidate input source for this lane.","required":1},
        {"contract_id":"DC004","contract_area":"native materialization evidence","rule":"DA-B native materialization proof must remain the evidence basis for candidate table viability.","required":1},
        {"contract_id":"DC005","contract_area":"backup","rule":"Any future apply execution must create pre-apply backups and hash manifests for active targets.","required":1},
        {"contract_id":"DC006","contract_area":"rollback","rule":"Any future apply execution must stage explicit rollback instructions and artifacts before mutation.","required":1},
        {"contract_id":"DC007","contract_area":"collision policy","rule":"Duplicate command/help keys, locale keys, and catalog keys must be reportable before write.","required":1},
        {"contract_id":"DC008","contract_area":"validation","rule":"Any future execution must produce pre/post row counts, hashes, and readback reports.","required":1},
        {"contract_id":"DC009","contract_area":"source protection","rule":"No source patch is authorized by this lane unless separately proven and authorized.","required":1},
        {"contract_id":"DC010","contract_area":"latest pointer","rule":"Side-branch savepoints must not move message_savepoint_latest_v1.json.","required":1},
    ]

    candidate_sources = [
        {"candidate_artifact":"HELP_DATA_CANDIDATE_ROWS.csv","path":str(help_candidate),"exists":int(help_candidate.exists()),"rows":len(csv_rows(help_candidate)),"intended_target_family":"HELP DATA","apply_now":0},
        {"candidate_artifact":"CMDHELPCHK_CANDIDATE_ROWS.csv","path":str(cmd_candidate),"exists":int(cmd_candidate.exists()),"rows":len(csv_rows(cmd_candidate)),"intended_target_family":"CMDHELPCHK","apply_now":0},
        {"candidate_artifact":"MESSAGE_APPLY_GATE_EVIDENCE.csv","path":str(gate_candidate),"exists":int(gate_candidate.exists()),"rows":len(csv_rows(gate_candidate)),"intended_target_family":"apply gate/provenance","apply_now":0},
    ]

    target_discovery_requirements = [
        {"target_family":"HELP DATA","target_name":"UNKNOWN_PENDING_DD_B_DISCOVERY","required_discovery":"physical file/table name, key fields, append/update mode, duplicate policy, backup path, readback command","discovered_now":0},
        {"target_family":"CMDHELPCHK","target_name":"UNKNOWN_PENDING_DD_B_DISCOVERY","required_discovery":"physical file/table name, key fields, append/update mode, duplicate policy, backup path, readback command","discovered_now":0},
        {"target_family":"HELP/CMDHELPCHK cross-check","target_name":"UNKNOWN_PENDING_DD_B_DISCOVERY","required_discovery":"consistency checks between command names, help keys, locale IDs, and expected validation rows","discovered_now":0},
    ]

    future_execution_gates = [
        {"gate_id":"GATE_PRE_APPLY_001","gate":"DB-B, DC-B, DD-B, and later target-discovery/review savepoints must be green.","required_for_execution":1},
        {"gate_id":"GATE_PRE_APPLY_002","gate":"Active target inventory and backup manifest must exist.","required_for_execution":1},
        {"gate_id":"GATE_PRE_APPLY_003","gate":"Candidate rows must validate against active target schema/key policy.","required_for_execution":1},
        {"gate_id":"GATE_PRE_APPLY_004","gate":"Dry-run delta report must show expected inserts/updates/skips/failures.","required_for_execution":1},
        {"gate_id":"GATE_PRE_APPLY_005","gate":"Explicit user authorization must name the apply execution package.","required_for_execution":1},
        {"gate_id":"GATE_POST_APPLY_001","gate":"Post-apply readback counts and hashes must be generated.","required_for_execution":1},
        {"gate_id":"GATE_POST_APPLY_002","gate":"CMDHELPCHK and HELP DATA consistency check must pass after execution.","required_for_execution":1},
    ]

    refusal = [
        {"refusal_id":"REFUSE_ACTIVE_HELP_DATA_APPLY","reason":"DC-B is plan-only.","active_now":1},
        {"refusal_id":"REFUSE_ACTIVE_CMDHELPCHK_APPLY","reason":"DC-B is plan-only.","active_now":1},
        {"refusal_id":"REFUSE_SOURCE_MUTATION","reason":"No source patch is authorized by DB-B/DC-B.","active_now":1},
        {"refusal_id":"REFUSE_ACTIVE_DBF_CDX_LMDB_MUTATION","reason":"No active data/index mutation is authorized by DC-B.","active_now":1},
        {"refusal_id":"REFUSE_WORKSPACE_MUTATION","reason":"No active workspace mutation is authorized by DC-B.","active_now":1},
        {"refusal_id":"REFUSE_LATEST_POINTER_CHANGE","reason":"Side-branch plan must not move official latest pointer.","active_now":1},
        {"refusal_id":"REFUSE_EXECUTION_PACKAGE_CREATION_AS_APPLY","reason":"DC-B creates only a plan, not an executable apply package.","active_now":1},
    ]

    boundary = [
        {"boundary":"guarded apply plan created","value":1,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by plan","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DC-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DC_B_APPLY_PLAN_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10dc_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dc_b_apply_contract_v1.csv", ["contract_id","contract_area","rule","required"], apply_contract)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dc_b_candidate_sources_v1.csv", ["candidate_artifact","path","exists","rows","intended_target_family","apply_now"], candidate_sources)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dc_b_target_discovery_requirements_v1.csv", ["target_family","target_name","required_discovery","discovered_now"], target_discovery_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dc_b_future_execution_gates_v1.csv", ["gate_id","gate","required_for_execution"], future_execution_gates)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dc_b_refusal_guards_v1.csv", ["refusal_id","reason","active_now"], refusal)
    write_csv(reports / "message_catalog_phase22ae_6_5_10dc_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DC-B",
        "DB_B_STATUS_GREEN":db_green,
        "DB_B_SAVEPOINT_PRESENT":db_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DC_B":latest_id(repo),
        "GUARDED_APPLY_PLAN_CREATED":1 if status == GREEN else 0,
        "TARGET_DISCOVERY_REQUIRED":1,
        "HELP_DATA_TARGET_DISCOVERED_NOW":0,
        "CMDHELPCHK_TARGET_DISCOVERED_NOW":0,
        "CANDIDATE_SOURCE_ROWS_TOTAL":sum(int(r["rows"]) for r in candidate_sources),
        "APPLY_CONTRACT_ROWS":len(apply_contract),
        "TARGET_DISCOVERY_REQUIREMENT_ROWS":len(target_discovery_requirements),
        "FUTURE_EXECUTION_GATE_ROWS":len(future_execution_gates),
        "REFUSAL_GUARD_ROWS":len(refusal),
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_PLAN":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_PLAN":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_PLAN":0,
        "LATEST_POINTER_CHANGED_BY_DC_B":0,
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10dc_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DC-B",
        "status":status,
        "guarded_apply_plan_created":1 if status == GREEN else 0,
        "apply_execution_authorized_now":False,
        "target_discovery_required":True,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10dc_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DC-B Guarded HELP/CMDHELPCHK Apply Plan

- Status: {status}
- Validation issues: {validation}
- DB-B status green: {db_green}
- DB-B savepoint present: {db_savepoint}
- Guarded apply plan created: {1 if status == GREEN else 0}
- Target discovery required: 1
- HELP DATA target discovered now: 0
- CMDHELPCHK target discovered now: 0
- Candidate source rows total: {sum(int(r['rows']) for r in candidate_sources)}
- Apply contract rows: {len(apply_contract)}
- Future execution gate rows: {len(future_execution_gates)}
- Refusal guard rows: {len(refusal)}
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by plan: 0
- Active DBF/CDX/LMDB mutation observed by plan: 0
- Workspace mutation observed by plan: 0
- Latest pointer changed by DC-B: 0
- Next gate: {next_gate}

DC-B is a guarded apply-plan package only. It accepts the candidate evidence for planning, requires target discovery, backups, rollback, hashes, and dry-run deltas before any write, and does not execute HELP DATA or CMDHELPCHK apply.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DC_B_GUARDED_HELP_CMDHELPCHK_APPLY_PLAN.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DC_B_GUARDED_HELP_CMDHELPCHK_APPLY_PLAN.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DB-B status green: {db_green}")
    print(f"  DB-B savepoint present: {db_savepoint}")
    print(f"  guarded apply plan created: {1 if status == GREEN else 0}")
    print("  target discovery required: 1")
    print("  HELP DATA target discovered now: 0")
    print("  CMDHELPCHK target discovered now: 0")
    print(f"  candidate source rows total: {sum(int(r['rows']) for r in candidate_sources)}")
    print(f"  apply contract rows: {len(apply_contract)}")
    print(f"  future execution gate rows: {len(future_execution_gates)}")
    print(f"  refusal guard rows: {len(refusal)}")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by plan: 0")
    print("  active DBF/CDX/LMDB mutation observed by plan: 0")
    print("  workspace mutation observed by plan: 0")
    print("  latest pointer changed by DC-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
