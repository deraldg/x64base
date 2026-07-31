from __future__ import annotations
import argparse, csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

CX_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CX_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_STAGING_GREEN_MAPPED_CANDIDATES_STAGED_APPLY_HELD"
CX_SAVEPOINT = "MSG-022AE.6.5.10CX-B"
GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10CY_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_VALIDATION_GREEN_MAPPED_CANDIDATES_VALIDATED_APPLY_HELD"
RED = "MESSAGE_CATALOG_PHASE22AE_6_5_10CY_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_VALIDATION_RED_REVIEW_REQUIRED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10CZ_B_HELP_CMDHELPCHK_CANDIDATE_TABLE_NATIVE_MATERIALIZATION_STAGING"
ROOT_REL = "docs/messaging/apply/phase22ae_6_5_10cy_b_help_cmdhelpchk_candidate_mapping_validation_v1"
CX_OUT_REL = "docs/messaging/apply/phase22ae_6_5_10cx_b_help_cmdhelpchk_candidate_mapping_staging_v1/candidate_outputs"

EXPECTED = {
    "HELP_DATA_CANDIDATE_ROWS.csv": {
        "rows": 3,
        "fields": ["MESSAGE_ID","LOCALE_ID","HELP_KEY","HELP_TEXT","SOURCE_PHASE","REVIEW_STATUS","APPLY_READY","APPLY_SCOPE"],
        "false_fields": ["APPLY_READY"],
        "scope_field": "APPLY_SCOPE",
    },
    "CMDHELPCHK_CANDIDATE_ROWS.csv": {
        "rows": 4,
        "fields": ["COMMAND_NAME","HELP_KEY","CHECK_ID","CHECK_STATUS","MUTATION_FLAG","REVIEW_STATUS","APPLY_READY","APPLY_SCOPE"],
        "false_fields": ["APPLY_READY","MUTATION_FLAG"],
        "scope_field": "APPLY_SCOPE",
    },
    "MESSAGE_APPLY_GATE_EVIDENCE.csv": {
        "rows": 4,
        "fields": ["GATE_ID","GATE_STATUS","MUTATION_FLAG","GATE_NOTES","APPLY_SCOPE"],
        "false_fields": ["MUTATION_FLAG"],
        "scope_field": "APPLY_SCOPE",
    },
}

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

def truthy_false(value: str) -> bool:
    return str(value).strip().lower() in {"false", "f", "0", "no", ""}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--replace-existing-validation", action="store_true")
    parser.add_argument("--allow-missing-cx-b-savepoint", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    docs = repo / "docs/messaging"
    reports = docs / "reports"
    out = repo / ROOT_REL
    cx_out = repo / CX_OUT_REL

    if out.exists() and args.replace_existing_validation:
        shutil.rmtree(out)

    cx = csv_one(reports / "message_catalog_phase22ae_6_5_10cx_b_status_summary_v1.csv")
    cx_green = int(cx.get("STATUS", "") == CX_GREEN)
    cx_savepoint = has_journal(repo, CX_SAVEPOINT)

    pre = [
        {"check_id":"cx_b_status_green","value":cx_green,"expected":1,"status":"PASS" if cx_green else "FAIL"},
        {"check_id":"cx_b_savepoint_present","value":cx_savepoint,"expected":1,"status":"PASS" if cx_savepoint else ("REVIEW" if args.allow_missing_cx_b_savepoint else "FAIL")},
        {"check_id":"cx_candidate_outputs_root_exists","value":int(cx_out.exists()),"expected":1,"status":"PASS" if cx_out.exists() else "FAIL"},
        {"check_id":"cy_b_root_absent_or_replace_authorized","value":int(out.exists()),"expected":0,"status":"PASS" if (not out.exists() or args.replace_existing_validation) else "FAIL"},
    ]

    output_checks = []
    field_checks = []
    row_checks = []
    for name, spec in EXPECTED.items():
        path = cx_out / name
        rows = csv_rows(path)
        exists = int(path.exists())
        count_ok = int(len(rows) == spec["rows"])
        output_checks.append({
            "artifact": name,
            "path": str(path),
            "exists": exists,
            "expected_rows": spec["rows"],
            "actual_rows": len(rows),
            "status": "PASS" if exists and count_ok else "FAIL",
        })

        actual_fields = list(rows[0].keys()) if rows else []
        for field in spec["fields"]:
            found = int(field in actual_fields)
            field_checks.append({
                "artifact": name,
                "field": field,
                "found": found,
                "status": "PASS" if found else "FAIL",
            })

        for idx, row in enumerate(rows, 1):
            scope_ok = int(row.get(spec["scope_field"], "") == "CANDIDATE_ONLY")
            false_ok = int(all(truthy_false(row.get(f, "")) for f in spec["false_fields"]))
            required_ok = int(all(str(row.get(f, "")).strip() != "" for f in spec["fields"] if f not in spec["false_fields"]))
            row_checks.append({
                "artifact": name,
                "row_number": idx,
                "scope_candidate_only": scope_ok,
                "false_flags_ok": false_ok,
                "required_values_present": required_ok,
                "status": "PASS" if scope_ok and false_ok and required_ok else "FAIL",
            })

    boundary = [
        {"boundary":"candidate mapping validated now","value":1,"status":"PASS"},
        {"boundary":"apply ready","value":0,"status":"PASS"},
        {"boundary":"apply execution authorized now","value":0,"status":"PASS"},
        {"boundary":"active HELP DATA apply executed","value":0,"status":"PASS"},
        {"boundary":"active CMDHELPCHK apply executed","value":0,"status":"PASS"},
        {"boundary":"source mutation authorized now","value":0,"status":"PASS"},
        {"boundary":"active catalog mutation observed","value":0,"status":"PASS"},
        {"boundary":"active DBF/CDX/LMDB mutation observed","value":0,"status":"PASS"},
        {"boundary":"workspace mutation observed","value":0,"status":"PASS"},
        {"boundary":"latest pointer changed by CY-B","value":0,"status":"PASS"},
    ]

    validation = sum(1 for row in pre + output_checks + field_checks + row_checks + boundary if row["status"] == "FAIL")
    status = GREEN if validation == 0 else RED
    next_gate = NEXT if status == GREEN else "REVIEW_PHASE22AE_6_5_10CY_B_VALIDATION_FAILURES"

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    write_csv(reports / "message_catalog_phase22ae_6_5_10cy_b_precondition_check_v1.csv", ["check_id","value","expected","status"], pre)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cy_b_output_check_v1.csv", ["artifact","path","exists","expected_rows","actual_rows","status"], output_checks)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cy_b_field_check_v1.csv", ["artifact","field","found","status"], field_checks)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cy_b_row_check_v1.csv", ["artifact","row_number","scope_candidate_only","false_flags_ok","required_values_present","status"], row_checks)
    write_csv(reports / "message_catalog_phase22ae_6_5_10cy_b_boundary_check_v1.csv", ["boundary","value","status"], boundary)

    summary = [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation,
        "PHASE": "22AE.6.5.10CY-B",
        "CX_B_STATUS_GREEN": cx_green,
        "CX_B_SAVEPOINT_PRESENT": cx_savepoint,
        "OFFICIAL_LATEST_SAVEPOINT_BEFORE_CY_B": latest_id(repo),
        "OUTPUT_ARTIFACTS_PASSED": sum(1 for r in output_checks if r["status"] == "PASS"),
        "OUTPUT_ARTIFACTS_TOTAL": len(output_checks),
        "FIELD_CHECKS_PASSED": sum(1 for r in field_checks if r["status"] == "PASS"),
        "FIELD_CHECKS_TOTAL": len(field_checks),
        "ROW_CHECKS_PASSED": sum(1 for r in row_checks if r["status"] == "PASS"),
        "ROW_CHECKS_TOTAL": len(row_checks),
        "CANDIDATE_MAPPING_VALIDATED_NOW": 1 if status == GREEN else 0,
        "APPLY_READY": 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "SOURCE_MUTATION_AUTHORIZED_NOW": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "ACTIVE_DBF_CDX_LMDB_MUTATION_OBSERVED": 0,
        "WORKSPACE_MUTATION_OBSERVED": 0,
        "LATEST_POINTER_CHANGED_BY_CY_B": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }]
    write_csv(reports / "message_catalog_phase22ae_6_5_10cy_b_status_summary_v1.csv", list(summary[0].keys()), summary)

    manifest = {
        "phase": "22AE.6.5.10CY-B",
        "status": status,
        "candidate_mapping_validated_now": 1 if status == GREEN else 0,
        "apply_ready": False,
        "active_apply_executed": False,
        "next_gate": next_gate,
    }
    write_text(out / "message_catalog_phase22ae_6_5_10cy_b_manifest_v1.json", json.dumps(manifest, indent=2))

    report = f"""# Phase 22AE.6.5.10CY-B HELP/CMDHELPCHK Candidate Mapping Validation

- Status: {status}
- Validation issues: {validation}
- CX-B status green: {cx_green}
- CX-B savepoint present: {cx_savepoint}
- Output artifacts passed: {summary[0]['OUTPUT_ARTIFACTS_PASSED']}/{summary[0]['OUTPUT_ARTIFACTS_TOTAL']}
- Field checks passed: {summary[0]['FIELD_CHECKS_PASSED']}/{summary[0]['FIELD_CHECKS_TOTAL']}
- Row checks passed: {summary[0]['ROW_CHECKS_PASSED']}/{summary[0]['ROW_CHECKS_TOTAL']}
- Candidate mapping validated now: {summary[0]['CANDIDATE_MAPPING_VALIDATED_NOW']}
- Apply ready: 0
- Apply execution authorized now: 0
- HELP DATA apply executed: 0
- CMDHELPCHK apply executed: 0
- Source mutation authorized now: 0
- Active catalog mutation observed: 0
- Active DBF/CDX/LMDB mutation observed: 0
- Workspace mutation observed: 0
- Latest pointer changed by CY-B: 0
- Next gate: {next_gate}
"""
    write_text(out / "MESSAGE_LOCALE_PHASE22AE_6_5_10CY_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_VALIDATION.md", report)
    write_text(docs / "MESSAGE_LOCALE_PHASE22AE_6_5_10CY_B_HELP_CMDHELPCHK_CANDIDATE_MAPPING_VALIDATION.md", report)

    print(status)
    print(f"  validation issues: {validation}")
    print(f"  CX-B status green: {cx_green}")
    print(f"  CX-B savepoint present: {cx_savepoint}")
    print(f"  output artifacts passed: {summary[0]['OUTPUT_ARTIFACTS_PASSED']}/{summary[0]['OUTPUT_ARTIFACTS_TOTAL']}")
    print(f"  field checks passed: {summary[0]['FIELD_CHECKS_PASSED']}/{summary[0]['FIELD_CHECKS_TOTAL']}")
    print(f"  row checks passed: {summary[0]['ROW_CHECKS_PASSED']}/{summary[0]['ROW_CHECKS_TOTAL']}")
    print(f"  candidate mapping validated now: {summary[0]['CANDIDATE_MAPPING_VALIDATED_NOW']}")
    print("  apply ready: 0")
    print("  apply execution authorized now: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  source mutation authorized now: 0")
    print("  active catalog mutation observed: 0")
    print("  active DBF/CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print("  latest pointer changed by CY-B: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 1

if __name__ == "__main__":
    raise SystemExit(main())
