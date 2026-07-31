from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CUB_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CU_B_NATIVE_CANDIDATE_TABLE_MATERIALIZATION_PROOF_REVIEW_GREEN_DBF_CDX_LMDB_READBACK_PROVEN"
CUB_SAVEPOINT = "MSG-022AE.6.5.10CU-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CV_B_NATIVE_MATERIALIZATION_REUSE_DECISION_PACKAGE_GREEN_NATIVE_TABLE_PATH_CONFIRMED_APPLY_HELD"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cv_b_native_materialization_reuse_decision_package_v1"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CW_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_MAPPING_PLAN"

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
    reports = repo / "docs/messaging/reports"
    docs = repo / "docs/messaging"
    out = repo / ROOT_REL

    if out.exists() and args.replace_existing_decision:
        shutil.rmtree(out)

    cu = csv_one(reports / "message_catalog_phase22ae_6_5_10cu_b_status_summary_v1.csv")
    cu_green = int(cu.get("STATUS", "") == CUB_GREEN)
    cu_savepoint = has_journal(repo, CUB_SAVEPOINT)
    native_confirmed = int(str(cu.get("NATIVE_TABLE_MATERIALIZATION_CONFIRMED_NOW", "0")) == "1")
    dbf_proven = int(str(cu.get("DBF_MATERIALIZATION_PROVEN", "0")) == "1")
    cdx_proven = int(str(cu.get("CDX_LMDB_MATERIALIZATION_PROVEN", "0")) == "1")

    pre = [
        {"check_id": "cu_b_status_green", "value": cu_green, "expected": 1, "status": "PASS" if cu_green else "FAIL"},
        {"check_id": "cu_b_savepoint_present", "value": cu_savepoint, "expected": 1, "status": "PASS" if cu_savepoint else "FAIL"},
        {"check_id": "native_table_materialization_confirmed", "value": native_confirmed, "expected": 1, "status": "PASS" if native_confirmed else "FAIL"},
        {"check_id": "dbf_materialization_proven", "value": dbf_proven, "expected": 1, "status": "PASS" if dbf_proven else "FAIL"},
        {"check_id": "cdx_lmdb_materialization_proven", "value": cdx_proven, "expected": 1, "status": "PASS" if cdx_proven else "FAIL"},
        {"check_id": "cv_b_root_absent_or_replace_authorized", "value": int(out.exists()), "expected": 0, "status": "PASS" if (not out.exists() or args.replace_existing_decision) else "FAIL"},
    ]

    decisions = [
        {"decision_id": "CONFIRM_NATIVE_TABLE_MATERIALIZATION_PATH", "selected": 1, "status": "ACCEPTED", "meaning": "DotTalk++ native CREATE/IMPORT/CDX/BUILDLMDB/readback path is proven for fenced candidate tables."},
        {"decision_id": "CONFIRM_PRODUCTION_HELP_CMDHELPCHK_APPLY_NOW", "selected": 0, "status": "HELD", "meaning": "CU-B did not apply active HELP DATA or CMDHELPCHK."},
        {"decision_id": "PLAN_HELP_CMDHELPCHK_CANDIDATE_TABLE_MAPPING", "selected": 1, "status": "SELECTED_NEXT", "meaning": "Map candidate table structures to real HELP DATA/CMDHELPCHK semantics before apply."},
        {"decision_id": "SOURCE_PATCH_NEEDED_NOW", "selected": 0, "status": "NOT_PROVEN", "meaning": "No source patch need is proven by this branch."},
    ]

    boundary = [
        {"boundary": "native table materialization path accepted", "value": 1, "status": "PASS" if native_confirmed else "FAIL"},
        {"boundary": "production HELP/CMDHELPCHK apply confirmed now", "value": 0, "status": "PASS"},
        {"boundary": "apply execution authorized now", "value": 0, "status": "PASS"},
        {"boundary": "source mutation authorized now", "value": 0, "status": "PASS"},
        {"boundary": "HELP DATA apply executed", "value": 0, "status": "PASS"},
        {"boundary": "CMDHELPCHK apply executed", "value": 0, "status": "PASS"},
        {"boundary": "latest pointer changed by CV-B", "value": 0, "status": "PASS"},
    ]

    validation = sum(1 for row in pre + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else "MESSAGE_CATALOG_PHASE22AE_6_5_10CV_B_NATIVE_MATERIALIZATION_REUSE_DECISION_PACKAGE_RED_REVIEW_REQUIRED"
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CV_B_DECISION_PRECONDITIONS"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10cv_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cv_b_decision_rows_v1.csv", ["decision_id","selected","status","meaning"], decisions)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cv_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10CV-B",
        "CORRECTED_CONCEPT": "DotTalk++ native table/materialization command path",
        "CU_B_STATUS_GREEN": cu_green,
        "CU_B_SAVEPOINT_PRESENT": cu_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CV_B": latest_id(repo),
        "NATIVE_TABLE_MATERIALIZATION_ACCEPTED": 1 if native_confirmed else 0,
        "DBF_MATERIALIZATION_PROVEN": dbf_proven,
        "CDX_LMDB_MATERIALIZATION_PROVEN": cdx_proven,
        "PRODUCTION_HELP_CMDHELPCHK_REUSE_CONFIRMED_NOW": 0,
        "REUSE_PATH_CONFIRMED_NOW": 0,
        "SOURCE_PATCH_NEEDED_PROVEN": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "LATEST_POINTER_CHANGED_BY_CV_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cv_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    report = f"""# Phase 22AE.6.5.10CV-B Native Materialization Reuse Decision Package

- Status: {status}
- Validation issues: {validation}
- Native table materialization accepted: {1 if native_confirmed else 0}
- DBF materialization proven: {dbf_proven}
- CDX/LMDB materialization proven: {cdx_proven}
- Production HELP/CMDHELPCHK reuse confirmed now: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Latest pointer changed by CV-B: 0
- Next gate: {next_gate}

CV-B accepts the native candidate table materialization proof, but it does not authorize active HELP DATA/CMDHELPCHK apply. The next step is a candidate-table mapping plan.
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CV_B_NATIVE_MATERIALIZATION_REUSE_DECISION_PACKAGE.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CV_B_NATIVE_MATERIALIZATION_REUSE_DECISION_PACKAGE.md", report)
    write_text(out / "message_catalog_phase22ae_6_5_10cv_b_manifest_v1.json", json.dumps(summary[0], indent=2))

    print(status)
    print(f"  validation issues: {validation}")
    print("  corrected concept: DotTalk++ native table/materialization command path")
    print(f"  CU-B status green: {cu_green}")
    print(f"  CU-B savepoint present: {cu_savepoint}")
    print(f"  native table materialization accepted: {1 if native_confirmed else 0}")
    print(f"  DBF materialization proven: {dbf_proven}")
    print(f"  CDX/LMDB materialization proven: {cdx_proven}")
    print("  production HELP/CMDHELPCHK reuse confirmed now: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  latest pointer changed by CV-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
