#!/usr/bin/env python3
"""
DotTalk++ Messaging Phase 8: guarded DBF schema staging plan only.

Reads Phase 6/7 message catalog report artifacts and emits planning CSV/Markdown
for future inactive candidate DBF schema staging. This script is intentionally
report-only: it creates report files under docs/messaging/reports and does not
create DBF/CDX/LMDB artifacts, mutate HELP/CMDHELPCHK, edit source, or run the
DotTalk++ runtime.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import pathlib
import sys
from typing import Dict, Iterable, List, Tuple

STATUS_GREEN = "MESSAGE_CATALOG_PHASE8_DBF_SCHEMA_STAGING_PLAN_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE8_DBF_SCHEMA_STAGING_PLAN_BLOCKED"


def read_csv(path: pathlib.Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: pathlib.Path, rows: List[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def norm_boolish(v: object) -> str:
    return str(v).strip().lower()


def get_first(rows: List[Dict[str, str]], key: str, default: str = "") -> str:
    return rows[0].get(key, default) if rows else default


def make_schema_rows() -> List[Dict[str, object]]:
    # DBF-friendly field names are <= 10 chars where practical. Longer logical
    # names are retained in notes and source mappings for SelfDoc readability.
    return [
        # SYSTEM_MESSAGES planned physical table: SYSMSG.dbf or SYSTEM_MESSAGES.dbf depending on final layout policy.
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":1, "FIELD_NAME":"MSGID", "LOGICAL_NAME":"MESSAGE_ID", "TYPE":"N", "WIDTH":10, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"MESSAGE_ID", "TAG_CANDIDATE":1, "NOTES":"Stable numeric message identity from compiled/source catalog."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":2, "FIELD_NAME":"SYMBOL", "LOGICAL_NAME":"SYMBOL", "TYPE":"C", "WIDTH":64, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"SYMBOL", "TAG_CANDIDATE":1, "NOTES":"Stable symbolic message key, e.g. UNKNOWN_COMMAND."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":3, "FIELD_NAME":"ENUMNAME", "LOGICAL_NAME":"ENUM_NAME", "TYPE":"C", "WIDTH":64, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"ENUM_NAME", "TAG_CANDIDATE":1, "NOTES":"C++ enum bridge for source/runtime readback."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":4, "FIELD_NAME":"FACILITY", "LOGICAL_NAME":"FACILITY", "TYPE":"C", "WIDTH":32, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"FACILITY", "TAG_CANDIDATE":1, "NOTES":"Facility/lane such as GLOBAL, MESSAGING, DBAREA."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":5, "FIELD_NAME":"OWNER", "LOGICAL_NAME":"OWNER_SUBSYSTEM", "TYPE":"C", "WIDTH":64, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"OWNER_SUBSYSTEM", "TAG_CANDIDATE":1, "NOTES":"Responsible owner/subsystem for validation and stewardship."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":6, "FIELD_NAME":"CATEGORY", "LOGICAL_NAME":"CATEGORY", "TYPE":"C", "WIDTH":32, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"CATEGORY", "TAG_CANDIDATE":1, "NOTES":"Message category such as ERROR, STATUS, HINT."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":7, "FIELD_NAME":"SEVERITY", "LOGICAL_NAME":"SEVERITY", "TYPE":"C", "WIDTH":16, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"SEVERITY", "TAG_CANDIDATE":1, "NOTES":"INFO/WARNING/ERROR etc."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":8, "FIELD_NAME":"STATUS", "LOGICAL_NAME":"STATUS", "TYPE":"C", "WIDTH":16, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"", "TAG_CANDIDATE":0, "NOTES":"Candidate default: ACTIVE. Added for future lifecycle management."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":9, "FIELD_NAME":"SRC", "LOGICAL_NAME":"SOURCE", "TYPE":"C", "WIDTH":32, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"", "TAG_CANDIDATE":0, "NOTES":"Candidate default: COMPILED_PHASE6_EXPORT."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "FIELD_ORDER":10, "FIELD_NAME":"NOTES", "LOGICAL_NAME":"NOTES", "TYPE":"M", "WIDTH":10, "DECIMALS":0, "NULLABLE":1, "SOURCE_COLUMN":"", "TAG_CANDIDATE":0, "NOTES":"Optional memo notes; may be deferred if memo is not desired for phase-8/9 candidate staging."},
        # SYSTEM_MESSAGE_TEXT planned physical table: SYSMSGTXT.dbf or SYSTEM_MESSAGE_TEXT.dbf depending on final layout policy.
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "FIELD_ORDER":1, "FIELD_NAME":"MSGID", "LOGICAL_NAME":"MESSAGE_ID", "TYPE":"N", "WIDTH":10, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"MESSAGE_ID", "TAG_CANDIDATE":1, "NOTES":"Foreign key to SYSTEM_MESSAGES.MSGID."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "FIELD_ORDER":2, "FIELD_NAME":"SYMBOL", "LOGICAL_NAME":"SYMBOL", "TYPE":"C", "WIDTH":64, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"SYMBOL", "TAG_CANDIDATE":1, "NOTES":"Redundant symbolic join key for human review and safer diagnostics."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "FIELD_ORDER":3, "FIELD_NAME":"ENUMNAME", "LOGICAL_NAME":"ENUM_NAME", "TYPE":"C", "WIDTH":64, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"ENUM_NAME", "TAG_CANDIDATE":1, "NOTES":"C++ enum bridge for review."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "FIELD_ORDER":4, "FIELD_NAME":"LOCALE", "LOGICAL_NAME":"LOCALE", "TYPE":"C", "WIDTH":16, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"LOCALE", "TAG_CANDIDATE":1, "NOTES":"Locale key such as en-US, it, es."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "FIELD_ORDER":5, "FIELD_NAME":"TEXT", "LOGICAL_NAME":"TEXT_TEMPLATE", "TYPE":"M", "WIDTH":10, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"TEXT_TEMPLATE", "TAG_CANDIDATE":0, "NOTES":"Localized whole-message template with named placeholders. Memo field avoids DBF C-width pressure."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "FIELD_ORDER":6, "FIELD_NAME":"TXTHASH", "LOGICAL_NAME":"TEXT_HASH", "TYPE":"C", "WIDTH":64, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"", "TAG_CANDIDATE":1, "NOTES":"Future candidate SHA-256 hash of TEXT_TEMPLATE for readback/parity checks."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "FIELD_ORDER":7, "FIELD_NAME":"STATUS", "LOGICAL_NAME":"STATUS", "TYPE":"C", "WIDTH":16, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"", "TAG_CANDIDATE":0, "NOTES":"Candidate default: ACTIVE/REVIEW as needed."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "FIELD_ORDER":8, "FIELD_NAME":"SRC", "LOGICAL_NAME":"SOURCE", "TYPE":"C", "WIDTH":32, "DECIMALS":0, "NULLABLE":0, "SOURCE_COLUMN":"", "TAG_CANDIDATE":0, "NOTES":"Candidate default: COMPILED_PHASE6_EXPORT."},
    ]


def make_index_rows() -> List[Dict[str, object]]:
    return [
        {"TABLE_NAME":"SYSTEM_MESSAGES", "TAG_NAME":"MSGID", "EXPRESSION":"STR(MSGID,10,0)", "UNIQUE":1, "REQUIRED_FOR":"primary lookup", "NOTES":"Stable numeric key; final expression may use runtime-supported numeric tag expression."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "TAG_NAME":"SYMBOL", "EXPRESSION":"SYMBOL", "UNIQUE":1, "REQUIRED_FOR":"symbol lookup", "NOTES":"Primary human/runtime symbolic lookup."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "TAG_NAME":"ENUMNAME", "EXPRESSION":"ENUMNAME", "UNIQUE":1, "REQUIRED_FOR":"C++ enum bridge", "NOTES":"Supports source/runtime bridge validation."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "TAG_NAME":"SEVERITY", "EXPRESSION":"SEVERITY", "UNIQUE":0, "REQUIRED_FOR":"reporting", "NOTES":"Group/report by severity."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "TAG_NAME":"FACILITY", "EXPRESSION":"FACILITY", "UNIQUE":0, "REQUIRED_FOR":"reporting", "NOTES":"Group/report by facility/lane."},
        {"TABLE_NAME":"SYSTEM_MESSAGES", "TAG_NAME":"OWNER", "EXPRESSION":"OWNER", "UNIQUE":0, "REQUIRED_FOR":"stewardship", "NOTES":"Group/report by owner subsystem."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "TAG_NAME":"MSG_LOCALE", "EXPRESSION":"STR(MSGID,10,0)+LOCALE", "UNIQUE":1, "REQUIRED_FOR":"localized template lookup", "NOTES":"Composite lookup candidate; final expression should match DotTalk++ CDX expression support."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "TAG_NAME":"SYMBOLLOC", "EXPRESSION":"SYMBOL+LOCALE", "UNIQUE":1, "REQUIRED_FOR":"human review lookup", "NOTES":"Redundant symbol+locale candidate."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "TAG_NAME":"LOCALE", "EXPRESSION":"LOCALE", "UNIQUE":0, "REQUIRED_FOR":"locale reporting", "NOTES":"List/report available locale coverage."},
        {"TABLE_NAME":"SYSTEM_MESSAGE_TEXT", "TAG_NAME":"TXTHASH", "EXPRESSION":"TXTHASH", "UNIQUE":0, "REQUIRED_FOR":"parity/readback", "NOTES":"Detect changed templates after import/export cycles."},
    ]


def make_candidate_path_rows(repo_root: pathlib.Path) -> List[Dict[str, object]]:
    base = pathlib.Path("docs/messaging/candidates/phase8_dbf_schema_staging")
    return [
        {"PATH_ROLE":"candidate_root", "RELATIVE_PATH":base.as_posix(), "CREATE_IN_PHASE8":0, "NOTES":"Future inactive candidate root. Phase 8 plan only does not create it."},
        {"PATH_ROLE":"candidate_dbf", "RELATIVE_PATH":(base / "dbf").as_posix(), "CREATE_IN_PHASE8":0, "NOTES":"Future inactive candidate DBF staging directory."},
        {"PATH_ROLE":"candidate_indexes", "RELATIVE_PATH":(base / "indexes").as_posix(), "CREATE_IN_PHASE8":0, "NOTES":"Future inactive candidate CDX/index staging directory."},
        {"PATH_ROLE":"candidate_lmdb", "RELATIVE_PATH":(base / "lmdb").as_posix(), "CREATE_IN_PHASE8":0, "NOTES":"Future inactive candidate LMDB staging directory if BUILDLMDB is used."},
        {"PATH_ROLE":"candidate_import_inputs", "RELATIVE_PATH":(base / "import_inputs").as_posix(), "CREATE_IN_PHASE8":0, "NOTES":"Future copies of Phase 6 CSVs used as import inputs."},
        {"PATH_ROLE":"candidate_reports", "RELATIVE_PATH":"docs/messaging/reports", "CREATE_IN_PHASE8":1, "NOTES":"Only report path written by Phase 8."},
    ]


def make_staging_steps() -> List[Dict[str, object]]:
    return [
        {"STEP":1, "ACTION":"VERIFY_PHASE6_AND_PHASE7_GREEN", "PHASE":"planning", "EXECUTES_NOW":1, "MUTATES_PROTECTED_SYSTEM":0, "DETAIL":"Read Phase 6/7 CSV reports and gate checks."},
        {"STEP":2, "ACTION":"ACCEPT_SCHEMA_PLAN_FOR_REVIEW", "PHASE":"planning", "EXECUTES_NOW":1, "MUTATES_PROTECTED_SYSTEM":0, "DETAIL":"Emit DBF field/type/index/tag staging plan rows."},
        {"STEP":3, "ACTION":"SELECT_INACTIVE_CANDIDATE_PATH_POLICY", "PHASE":"planning", "EXECUTES_NOW":1, "MUTATES_PROTECTED_SYSTEM":0, "DETAIL":"Report future candidate DBF/CDX/LMDB directories without creating them."},
        {"STEP":4, "ACTION":"FUTURE_CREATE_CANDIDATE_TABLES", "PHASE":"future", "EXECUTES_NOW":0, "MUTATES_PROTECTED_SYSTEM":0, "DETAIL":"Future guarded package only; create inactive candidate tables, not active metadata."},
        {"STEP":5, "ACTION":"FUTURE_IMPORT_AND_READBACK", "PHASE":"future", "EXECUTES_NOW":0, "MUTATES_PROTECTED_SYSTEM":0, "DETAIL":"Future guarded package only; import Phase 6 rows and validate counts/hash/readback."},
        {"STEP":6, "ACTION":"FUTURE_PROMOTION_DECISION", "PHASE":"future", "EXECUTES_NOW":0, "MUTATES_PROTECTED_SYSTEM":0, "DETAIL":"Separate explicit authorization required before any active catalog promotion."},
    ]


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args(argv)

    repo = pathlib.Path(args.repo_root).resolve()
    reports = repo / "docs" / "messaging" / "reports"
    phase6_status = read_csv(reports / "message_catalog_phase6_status_summary_v1.csv")
    phase6_msgs = read_csv(reports / "message_catalog_phase6_system_messages_v1.csv")
    phase6_text = read_csv(reports / "message_catalog_phase6_system_message_text_v1.csv")
    phase6_validation = read_csv(reports / "message_catalog_phase6_validation_v1.csv")
    phase7_status = read_csv(reports / "message_catalog_phase7_status_summary_v1.csv")
    phase7_gate = read_csv(reports / "message_catalog_phase7_gate_check_v1.csv")

    gate_rows: List[Dict[str, object]] = []
    def gate(name: str, passed: bool, detail: str) -> None:
        gate_rows.append({"GATE": name, "STATUS": "PASS" if passed else "FAIL", "DETAIL": detail})

    p6_green = get_first(phase6_status, "STATUS") == "MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_GREEN"
    p7_green = get_first(phase7_status, "STATUS") == "MESSAGE_CATALOG_PHASE7_PROMOTION_READINESS_PLAN_GREEN"
    gate("PHASE6_STATUS_GREEN", p6_green, "OK" if p6_green else "Phase 6 status is missing or not green.")
    gate("PHASE7_STATUS_GREEN", p7_green, "OK" if p7_green else "Phase 7 status is missing or not green.")
    gate("PHASE6_MESSAGES_PRESENT", len(phase6_msgs) > 0, f"rows={len(phase6_msgs)}")
    gate("PHASE6_TEXT_PRESENT", len(phase6_text) > 0, f"rows={len(phase6_text)}")
    gate("PHASE6_VALIDATION_EMPTY", len(phase6_validation) == 0, f"validation_rows={len(phase6_validation)}")
    p7_failures = [r for r in phase7_gate if str(r.get("STATUS", "")).upper() != "PASS"]
    gate("PHASE7_GATES_ALL_PASS", len(p7_failures) == 0 and len(phase7_gate) > 0, f"failures={len(p7_failures)} gate_rows={len(phase7_gate)}")
    gate("DBF_STAGING_NOT_AUTHORIZED", True, "Phase 8 is plan-only; candidate DBF creation/import not authorized.")
    gate("ACTIVE_PROMOTION_NOT_AUTHORIZED", True, "No active catalog promotion authorized.")

    failed = [r for r in gate_rows if r["STATUS"] != "PASS"]
    status = STATUS_GREEN if not failed else STATUS_BLOCKED

    schema_rows = make_schema_rows()
    index_rows = make_index_rows()
    path_rows = make_candidate_path_rows(repo)
    steps = make_staging_steps()

    boundary_rows = [
        {"PROTECTED_SYSTEM":"DBF_CATALOGS", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"Phase 8 creates DBF schema staging reports only. No DBF files/tables created or opened for write."},
        {"PROTECTED_SYSTEM":"CDX_INDEXES", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"No CDX/index files created or rebuilt."},
        {"PROTECTED_SYSTEM":"LMDB", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"No LMDB environment created or rebuilt."},
        {"PROTECTED_SYSTEM":"HELP_DATA", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM":"SOURCE_MINING", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"No source-mining mutation."},
        {"PROTECTED_SYSTEM":"SOURCE_CODE", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"No source files edited by this script."},
        {"PROTECTED_SYSTEM":"RUNTIME_EXECUTION", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"No DotTalk++ runtime execution required."},
        {"PROTECTED_SYSTEM":"CATALOG_PROMOTION", "MUTATION_ALLOWED":0, "OBSERVED_MUTATION":0, "DETAIL":"No active catalog promotion authorized or performed."},
    ]

    locales = sorted({r.get("LOCALE", "") for r in phase6_text if r.get("LOCALE")})
    status_rows = [{
        "STATUS": status,
        "MESSAGES": len(phase6_msgs),
        "TEXT_ROWS": len(phase6_text),
        "LOCALES": ";".join(locales),
        "VALIDATION_ISSUES": len(phase6_validation),
        "SCHEMA_ROWS": len(schema_rows),
        "INDEX_ROWS": len(index_rows),
        "DBF_STAGING_AUTHORIZED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": "HOLD_OR_AUTHORIZE_PHASE9_INACTIVE_CANDIDATE_DBF_STAGING_PACKAGE" if status == STATUS_GREEN else "FIX_PHASE8_PRECONDITION_FAILURES",
    }]

    write_csv(reports / "message_catalog_phase8_status_summary_v1.csv", status_rows, list(status_rows[0].keys()))
    write_csv(reports / "message_catalog_phase8_dbf_schema_plan_v1.csv", schema_rows, ["TABLE_NAME","FIELD_ORDER","FIELD_NAME","LOGICAL_NAME","TYPE","WIDTH","DECIMALS","NULLABLE","SOURCE_COLUMN","TAG_CANDIDATE","NOTES"])
    write_csv(reports / "message_catalog_phase8_index_tag_plan_v1.csv", index_rows, ["TABLE_NAME","TAG_NAME","EXPRESSION","UNIQUE","REQUIRED_FOR","NOTES"])
    write_csv(reports / "message_catalog_phase8_candidate_path_plan_v1.csv", path_rows, ["PATH_ROLE","RELATIVE_PATH","CREATE_IN_PHASE8","NOTES"])
    write_csv(reports / "message_catalog_phase8_staging_steps_v1.csv", steps, ["STEP","ACTION","PHASE","EXECUTES_NOW","MUTATES_PROTECTED_SYSTEM","DETAIL"])
    write_csv(reports / "message_catalog_phase8_gate_check_v1.csv", gate_rows, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase8_boundary_ledger_v1.csv", boundary_rows, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    report = reports / "MESSAGE_CATALOG_PHASE8_DBF_SCHEMA_STAGING_PLAN_REPORT.md"
    report.write_text("\n".join([
        "# Message Catalog Phase 8 DBF Schema Staging Plan",
        "",
        f"Status: `{status}`",
        "",
        "Phase 8 is a guarded planning stage for future inactive DBF candidate staging of `SYSTEM_MESSAGES` and `SYSTEM_MESSAGE_TEXT`.",
        "",
        "## Counts",
        f"- Messages: {len(phase6_msgs)}",
        f"- Text rows: {len(phase6_text)}",
        f"- Locales: {', '.join(locales)}",
        f"- Validation issues: {len(phase6_validation)}",
        f"- Planned schema rows: {len(schema_rows)}",
        f"- Planned index/tag rows: {len(index_rows)}",
        "",
        "## Boundary",
        "No DBF/CDX/LMDB files are created. No HELP DATA, CMDHELPCHK, source-mining, source-code, runtime, or active catalog promotion mutation occurs.",
        "",
        "## Next Gate",
        status_rows[0]["NEXT_GATE"],
        "",
    ]), encoding="utf-8")

    print(status)
    print(f"  messages: {len(phase6_msgs)}")
    print(f"  text rows: {len(phase6_text)}")
    print(f"  locales: {', '.join(locales)}")
    print(f"  validation issues: {len(phase6_validation)}")
    print("  dbf staging authorized: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
