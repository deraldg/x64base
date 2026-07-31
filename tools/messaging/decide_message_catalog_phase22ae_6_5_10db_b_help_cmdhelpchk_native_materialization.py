from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

DAB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DA_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_PROOF_REVIEW_GREEN_DBF_CDX_LMDB_READBACK_PROVEN_APPLY_HELD"
DAB_SAVEPOINT = "MSG-022AE.6.5.10DA-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10DB_B_HELP_CMDHELPCHK_NATIVE_MATERIALIZATION_DECISION_PACKAGE_GREEN_NATIVE_CANDIDATE_TABLES_ACCEPTED_APPLY_NOT_AUTHORIZED"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10DB_B_HELP_CMDHELPCHK_NATIVE_MATERIALIZATION_DECISION_PACKAGE_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10DC_B_GUARDED_HELP_CMDHELPCHK_APPLY_PLAN"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10db_b_help_cmdhelpchk_native_materialization_decision_package_v1"

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
    parser.add_argument("--replace-existing-decision", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_decision:
        shutil.rmtree(out)

    da = csv_one(reports / "message_catalog_phase22ae_6_5_10da_b_status_summary_v1.csv")
    da_green = int(da.get("STATUS", "") == DAB_GREEN)
    da_savepoint = has_journal(repo, DAB_SAVEPOINT)
    native_proven = int(str(da.get("HELP_CMDHELPCHK_CANDIDATE_NATIVE_MATERIALIZATION_PROVEN", "0")) == "1")
    apply_ready = int(str(da.get("APPLY_READY", "0")) == "1")
    apply_auth = int(str(da.get("APPLY_EXECUTION_AUTHORIZED_NOW", "0")) == "1")
    help_apply = int(str(da.get("HELP_DATA_APPLY_EXECUTED", "0")) == "1")
    cmd_apply = int(str(da.get("CMDHELPCHK_APPLY_EXECUTED", "0")) == "1")

    pre = [
        {"check_id":"da_b_status_green","value":da_green,"expected":1,"status":"PASS" if da_green else "FAIL"},
        {"check_id":"da_b_savepoint_present","value":da_savepoint,"expected":1,"status":"PASS" if da_savepoint else "FAIL"},
        {"check_id":"native_candidate_materialization_proven","value":native_proven,"expected":1,"status":"PASS" if native_proven else "FAIL"},
        {"check_id":"apply_ready_not_set","value":apply_ready,"expected":0,"status":"PASS" if apply_ready == 0 else "FAIL"},
        {"check_id":"apply_execution_not_authorized","value":apply_auth,"expected":0,"status":"PASS" if apply_auth == 0 else "FAIL"},
        {"check_id":"help_data_apply_not_executed","value":help_apply,"expected":0,"status":"PASS" if help_apply == 0 else "FAIL"},
        {"check_id":"cmdhelpchk_apply_not_executed","value":cmd_apply,"expected":0,"status":"PASS" if cmd_apply == 0 else "FAIL"},
        {"check_id":"db_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_decision) else "FAIL"},
    ]

    decisions = [
        {"decision_id":"DB001_ACCEPT_NATIVE_CANDIDATE_TABLE_MATERIALIZATION","selected":1,"decision_status":"ACCEPTED","meaning":"DA-B proves fenced HELPDATA_CZ, CMDHELP_CZ, and GATEEV_CZ can be created, imported, indexed, LMDB-built, ordered, and read back through DotTalk++ native commands.","apply_execution_now":0},
        {"decision_id":"DB002_DO_NOT_TREAT_CANDIDATES_AS_PRODUCTION_HELP_DATA","selected":1,"decision_status":"HELD","meaning":"Candidate rows are structurally proven but are not active HELP DATA/CMDHELPCHK records yet.","apply_execution_now":0},
        {"decision_id":"DB003_REQUIRE_GUARDED_APPLY_PLAN_BEFORE_EXECUTION","selected":1,"decision_status":"SELECTED_NEXT","meaning":"Next package should plan guarded apply rules, source/target paths, backups, rollback, hash checks, and validation gates without executing apply.","apply_execution_now":0},
        {"decision_id":"DB004_AUTHORIZE_APPLY_EXECUTION_NOW","selected":0,"decision_status":"NOT_AUTHORIZED","meaning":"No active HELP DATA or CMDHELPCHK mutation is authorized at DB-B.","apply_execution_now":0},
        {"decision_id":"DB005_SOURCE_PATCH_REQUIRED_NOW","selected":0,"decision_status":"NOT_PROVEN","meaning":"Native candidate materialization is green; source patch need is not proven by this branch.","apply_execution_now":0},
    ]

    apply_plan_requirements = [
        {"req_id":"DC001","requirement":"Identify exact active HELP DATA and CMDHELPCHK target artifacts and row semantics before any write.","required":1},
        {"req_id":"DC002","requirement":"Define candidate-to-active row transformation and collision/duplicate policy.","required":1},
        {"req_id":"DC003","requirement":"Require backups, file hashes, rollback manifest, and pre/post validation reports.","required":1},
        {"req_id":"DC004","requirement":"Preserve source-comment contracts and perform no source mutation unless separately authorized.","required":1},
        {"req_id":"DC005","requirement":"Keep DC-B as a plan only; no active HELP/CMDHELPCHK apply execution.","required":1},
        {"req_id":"DC006","requirement":"Require later execution package only after explicit authorization and review of DC-B plan.","required":1},
        {"req_id":"DC007","requirement":"Continue to report official latest pointer separately from side-branch savepoints.","required":1},
    ]

    boundary = [
        {"boundary":"native candidate materialization accepted","value":1 if native_proven else 0,"status":"PASS" if native_proven else "FAIL"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"source patch needed proven","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed by decision","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed by decision","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed by decision","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by DB-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10DB_B_DECISION_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10db_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10db_b_decision_rows_v1.csv", ["decision_id","selected","decision_status","meaning","apply_execution_now"], decisions)
    write_csv(reports / "message_catalog_phase22ae_6_5_10db_b_apply_plan_requirements_v1.csv", ["req_id","requirement","required"], apply_plan_requirements)
    write_csv(reports / "message_catalog_phase22ae_6_5_10db_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS":status,
        "VALIDATION_ISSUES":validation,
        "PHASE":"22AE.6.5.10DB-B",
        "DA_B_STATUS_GREEN":da_green,
        "DA_B_SAVEPOINT_PRESENT":da_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_DB_B":latest_id(repo),
        "NATIVE_CANDIDATE_MATERIALIZATION_ACCEPTED":1 if native_proven else 0,
        "HELP_CMDHELPCHK_CANDIDATES_ACCEPTED_FOR_APPLY_PLANNING":1 if native_proven else 0,
        "APPLY_READY":0,
        "APPLY_EXECUTION_AUTHORIZED_NOW":0,
        "HELP_DATA_APPLY_EXECUTED":0,
        "CMDHELPCHK_APPLY_EXECUTED":0,
        "SOURCE_PATCH_NEEDED_PROVEN":0,
        "SOURCE_MUTATION_AUTHORIZED_NOW":0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_DECISION":0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED_BY_DECISION":0,
        "WORKSPACE_MUTATION_OBSERVED_BY_DECISION":0,
        "LATEST_POINTER_CHANGED_BY_DB_B":0,
        "SELECTED_NEXT_PACKAGE":"DC-B guarded HELP/CMDHELPCHK apply plan",
        "NEXT_GATE":next_gate,
        "REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10db_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase":"22AE.6.5.10DB-B",
        "status":status,
        "native_candidate_materialization_accepted":1 if native_proven else 0,
        "apply_ready":False,
        "apply_execution_authorized_now":False,
        "next_gate":next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10db_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10DB-B HELP/CMDHELPCHK Native Materialization Decision Package

- Status: {status}
- Validation issues: {validation}
- DA-B status green: {da_green}
- DA-B savepoint present: {da_savepoint}
- Native candidate materialization accepted: {1 if native_proven else 0}
- HELP/CMDHELPCHK candidates accepted for apply planning: {1 if native_proven else 0}
- Apply ready: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source patch needed proven: 0
- Source mutation authorized now: 0
- Active catalog mutation observed by decision: 0
- Active DBF/CDX/LMDB mutation observed by decision: 0
- Workspace mutation observed by decision: 0
- Latest pointer changed by DB-B: 0
- Selected next package: DC-B guarded HELP/CMDHELPCHK apply plan
- Next gate: {next_gate}

DB-B accepts the fenced native candidate-table materialization proof from DA-B, but it does not authorize active HELP DATA or CMDHELPCHK apply. The next step is a guarded apply-plan package only.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10DB_B_HELP_CMDHELPCHK_NATIVE_MATERIALIZATION_DECISION_PACKAGE.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10DB_B_HELP_CMDHELPCHK_NATIVE_MATERIALIZATION_DECISION_PACKAGE.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  DA-B status green: {da_green}")
    print(f"  DA-B savepoint present: {da_savepoint}")
    print(f"  native candidate materialization accepted: {1 if native_proven else 0}")
    print(f"  HELP/CMDHELPCHK candidates accepted for apply planning: {1 if native_proven else 0}")
    print("  apply ready: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source patch needed proven: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed by decision: 0")
    print("  active DBF/CDX/LMDB mutation observed by decision: 0")
    print("  workspace mutation observed by decision: 0")
    print("  latest pointer changed by DB-B: 0")
    print("  selected next package: DC-B guarded HELP/CMDHELPCHK apply plan")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
