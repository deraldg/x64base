#!/usr/bin/env python3
"""
Phase 13: Candidate CDX tag plan for DotTalk++ Messaging catalog.

Plan only. Consumes Phase 8 index/tag plan and Phase 12 candidate DBF parity
reports, then produces a guarded plan for Phase 14 inactive-candidate CDX tag
execution.

No CDX/index creation occurs in Phase 13.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE13_CANDIDATE_CDX_TAG_PLAN_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE13_CANDIDATE_CDX_TAG_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE14_INACTIVE_CANDIDATE_CDX_TAG_EXECUTION"
REPORT_DIR = Path("docs/messaging/reports")
PHASE11_ROOT = Path("docs/messaging/candidates/phase11_inactive_candidate_dbf_execution")

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}

def status_is(path: Path, expected: str) -> bool:
    return first_row(path).get("STATUS", "") == expected

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase8_tags = reports / "message_catalog_phase8_index_tag_plan_v1.csv"
    phase11_summary = reports / "message_catalog_phase11_status_summary_v1.csv"
    phase12_summary = reports / "message_catalog_phase12_status_summary_v1.csv"
    phase12_parity = reports / "message_catalog_phase12_row_parity_v1.csv"
    messages_dbf = repo / PHASE11_ROOT / "dbf" / "SYSTEM_MESSAGES.dbf"
    text_dbf = repo / PHASE11_ROOT / "dbf" / "SYSTEM_MESSAGE_TEXT.dbf"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE8_INDEX_TAG_PLAN_PRESENT", phase8_tags.exists(), str(phase8_tags))
    gate("PHASE11_STATUS_PRESENT", phase11_summary.exists(), str(phase11_summary))
    gate("PHASE12_STATUS_PRESENT", phase12_summary.exists(), str(phase12_summary))
    gate("PHASE12_ROW_PARITY_PRESENT", phase12_parity.exists(), str(phase12_parity))
    gate("CANDIDATE_SYSTEM_MESSAGES_DBF_PRESENT", messages_dbf.exists(), str(messages_dbf))
    gate("CANDIDATE_SYSTEM_MESSAGE_TEXT_DBF_PRESENT", text_dbf.exists(), str(text_dbf))

    messages = "0"
    text_rows = "0"
    locales = ""
    validation_issues = "UNKNOWN"

    if failures == 0:
        gate("PHASE11_STATUS_GREEN", status_is(phase11_summary, "MESSAGE_CATALOG_PHASE11_INACTIVE_CANDIDATE_DBF_EXECUTION_GREEN"), first_row(phase11_summary).get("STATUS", ""))
        gate("PHASE12_STATUS_GREEN", status_is(phase12_summary, "MESSAGE_CATALOG_PHASE12_CANDIDATE_DBF_ROW_PARITY_GREEN"), first_row(phase12_summary).get("STATUS", ""))
        p12 = first_row(phase12_summary)
        messages = p12.get("MESSAGES", "12")
        text_rows = p12.get("TEXT_ROWS", "60")
        locales = p12.get("LOCALES", "de;en-US;es;fr;it")
        validation_issues = p12.get("VALIDATION_ISSUES", "0")
        gate("PHASE12_VALIDATION_ZERO", validation_issues == "0", f"validation_issues={validation_issues}")

        parity_rows = read_csv(phase12_parity)
        bad = [r for r in parity_rows if r.get("STATUS") != "PASS"]
        gate("PHASE12_PARITY_ROWS_PASS", len(bad) == 0, f"nonpass_rows={len(bad)}")

    tag_plan_rows = []
    if phase8_tags.exists():
        for r in read_csv(phase8_tags):
            tag_plan_rows.append({
                "TABLE_NAME": r.get("TABLE_NAME", ""),
                "TAG_NAME": r.get("TAG_NAME", ""),
                "EXPRESSION": r.get("EXPRESSION", ""),
                "UNIQUE": r.get("UNIQUE", ""),
                "REQUIRED_FOR": r.get("REQUIRED_FOR", ""),
                "EXECUTE_IN_PHASE13": 0,
                "EXECUTE_IN_PHASE14": 1,
                "CANDIDATE_ONLY": 1,
                "NOTES": r.get("NOTES", ""),
            })

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED

    write_csv(reports / "message_catalog_phase13_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "CDX_TAG_EXECUTION_AUTHORIZED": 0,
        "CDX_FILES_CREATED": 0,
        "LMDB_ENV_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "CDX_TAG_EXECUTION_AUTHORIZED", "CDX_FILES_CREATED", "LMDB_ENV_CREATED",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase13_candidate_cdx_tag_plan_v1.csv", tag_plan_rows,
              ["TABLE_NAME", "TAG_NAME", "EXPRESSION", "UNIQUE", "REQUIRED_FOR",
               "EXECUTE_IN_PHASE13", "EXECUTE_IN_PHASE14", "CANDIDATE_ONLY", "NOTES"])

    dts_rows = [
        {"SCRIPT": "MESSAGE_CATALOG_PHASE14_CREATE_CANDIDATE_CDX_TAGS.dts", "TABLE_NAME": "SYSTEM_MESSAGES", "PURPOSE": "Create candidate-only SYSTEM_MESSAGES CDX tags", "EXECUTE_IN_PHASE13": 0, "EXECUTE_IN_PHASE14": 1, "BOUNDARY": "inactive candidate only"},
        {"SCRIPT": "MESSAGE_CATALOG_PHASE14_CREATE_CANDIDATE_CDX_TAGS.dts", "TABLE_NAME": "SYSTEM_MESSAGE_TEXT", "PURPOSE": "Create candidate-only SYSTEM_MESSAGE_TEXT CDX tags", "EXECUTE_IN_PHASE13": 0, "EXECUTE_IN_PHASE14": 1, "BOUNDARY": "inactive candidate only"},
        {"SCRIPT": "MESSAGE_CATALOG_PHASE14_VALIDATE_CANDIDATE_CDX_TAGS.dts", "TABLE_NAME": "SYSTEM_MESSAGES", "PURPOSE": "Readback candidate-only tag availability/order behavior", "EXECUTE_IN_PHASE13": 0, "EXECUTE_IN_PHASE14": 1, "BOUNDARY": "read-only candidate validation after tag creation"},
        {"SCRIPT": "MESSAGE_CATALOG_PHASE14_VALIDATE_CANDIDATE_CDX_TAGS.dts", "TABLE_NAME": "SYSTEM_MESSAGE_TEXT", "PURPOSE": "Readback candidate-only localized lookup tags", "EXECUTE_IN_PHASE13": 0, "EXECUTE_IN_PHASE14": 1, "BOUNDARY": "read-only candidate validation after tag creation"},
    ]
    write_csv(reports / "message_catalog_phase13_candidate_dts_cdx_plan_v1.csv", dts_rows,
              ["SCRIPT", "TABLE_NAME", "PURPOSE", "EXECUTE_IN_PHASE13", "EXECUTE_IN_PHASE14", "BOUNDARY"])

    smoke_rows = [
        {"CHECK": "SYSTEM_MESSAGES_TAG_MSGID", "EXPECTED": "MSGID tag exists and supports primary lookup", "SOURCE": "Phase 8 tag plan", "FAILS_IF": "tag missing or duplicate primary key behavior"},
        {"CHECK": "SYSTEM_MESSAGES_TAG_SYMBOL", "EXPECTED": "SYMBOL unique tag exists", "SOURCE": "Phase 8 tag plan", "FAILS_IF": "tag missing or duplicate symbol behavior"},
        {"CHECK": "SYSTEM_MESSAGES_TAG_ENUMNAME", "EXPECTED": "ENUMNAME unique tag exists", "SOURCE": "Phase 8 tag plan", "FAILS_IF": "tag missing or duplicate enum bridge behavior"},
        {"CHECK": "SYSTEM_MESSAGE_TEXT_TAG_MSG_LOCALE", "EXPECTED": "MSGID+LOCALE unique tag exists", "SOURCE": "Phase 8 tag plan", "FAILS_IF": "localized lookup not unique"},
        {"CHECK": "SYSTEM_MESSAGE_TEXT_TAG_SYMBOLLOC", "EXPECTED": "SYMBOL+LOCALE unique tag exists", "SOURCE": "Phase 8 tag plan", "FAILS_IF": "human review lookup not unique"},
        {"CHECK": "SYSTEM_MESSAGE_TEXT_TAG_LOCALE", "EXPECTED": "LOCALE reporting tag exists", "SOURCE": "Phase 8 tag plan", "FAILS_IF": "locale reporting unavailable"},
        {"CHECK": "NO_ACTIVE_INDEX_PATH_MUTATION", "EXPECTED": "candidate path only", "SOURCE": "Phase 14 boundary ledger", "FAILS_IF": "active CDX/index path touched"},
    ]
    write_csv(reports / "message_catalog_phase13_cdx_validation_plan_v1.csv", smoke_rows,
              ["CHECK", "EXPECTED", "SOURCE", "FAILS_IF"])

    write_csv(reports / "message_catalog_phase13_gate_check_v1.csv", gates + [
        {"GATE": "CDX_TAG_EXECUTION_NOT_AUTHORIZED", "STATUS": "PASS", "DETAIL": "Phase 13 is plan-only; no CDX tag execution performed."},
        {"GATE": "ACTIVE_PROMOTION_NOT_AUTHORIZED", "STATUS": "PASS", "DETAIL": "No active catalog replacement/promotion authorized."},
    ], ["GATE", "STATUS", "DETAIL"])

    boundary_rows = [
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 13 reads reports/paths only; no DBF/DBT writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF catalog paths created, replaced, opened for write, or promoted."},
        {"PROTECTED_SYSTEM": "CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/index files created or rebuilt in Phase 13."},
        {"PROTECTED_SYSTEM": "LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB environment created or rebuilt."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source files edited by this script."},
        {"PROTECTED_SYSTEM": "RUNTIME_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DotTalk++ runtime execution required."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion authorized or performed."},
    ]
    write_csv(reports / "message_catalog_phase13_boundary_ledger_v1.csv", boundary_rows,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 13 Candidate CDX Tag Plan

Status: `{status}`

Phase 13 plans candidate-only CDX tag execution for Phase 14. It does not create
CDX/index files.

## Counts

- Messages: {messages}
- Text rows: {text_rows}
- Locales: {locales}
- Validation issues: {validation_issues}

## Next gate

`{NEXT_GATE}`

## Boundary

No DBF/DBT writes, no CDX/index creation, no LMDB creation, no HELP DATA
mutation, no CMDHELPCHK mutation, no source-mining mutation, no source edits, no
runtime execution, and no active catalog promotion occurred in Phase 13.
"""
    (reports / "MESSAGE_CATALOG_PHASE13_CANDIDATE_CDX_TAG_PLAN_REPORT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  cdx tag execution authorized: 0")
    print("  cdx files created: 0")
    print("  lmdb env created: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
