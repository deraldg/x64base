#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23R_MESSAGE_SCHEMA_CLEAN_CANDIDATE_GREEN_REPORT_ONLY"
STATUS_BLOCKED = "LOCALE_PHASE23R_MESSAGE_SCHEMA_CLEAN_CANDIDATE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23S_MESSAGE_CATALOG_ACTIVE_SCHEMA_PROMOTION"
REPORT_DIR = Path("docs/locale/reports")

FIELDS_REPORT = Path("docs/locale/reports/locale_phase23q_active_messaging_dbf_fields_v1.csv")
PHASE8_TAG_PLAN = Path("docs/messaging/reports/message_catalog_phase8_index_tag_plan_v1.csv")
PHASE13_TAG_PLAN = Path("docs/messaging/reports/message_catalog_phase13_candidate_cdx_tag_plan_v1.csv")
TARGET_ACTIVE = Path("dottalkpp/data/schemas/messaging/message_catalog.dtschema")
CLEAN_DRAFT = Path("docs/locale/schemas/candidates/phase23r_message_catalog_clean_candidate/message_catalog.dtschema")

VALID_TYPES = {"C", "N", "M", "L", "D", "F", "I", "B", "Y", "T"}
FIELD_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)

def is_valid_field(row: dict[str, str]) -> tuple[bool, str]:
    name = (row.get("DBF_DESCRIPTOR_NAME") or "").strip().upper()
    typ = (row.get("TYPE") or "").strip().upper()
    try:
        length = int((row.get("LENGTH") or "0").strip() or "0")
    except Exception:
        length = 0

    if not name:
        return False, "blank_descriptor_name"
    if not FIELD_RE.match(name):
        return False, f"invalid_descriptor_name:{name}"
    if typ not in VALID_TYPES:
        return False, f"invalid_or_blank_type:{typ}"
    if length <= 0:
        return False, f"invalid_length:{length}"
    return True, "valid"

def load_preferred_tag_rows(repo: Path) -> tuple[str, list[dict[str, str]]]:
    p13 = repo / PHASE13_TAG_PLAN
    rows13 = read_csv(p13)
    if rows13:
        return rel(p13, repo), rows13
    p8 = repo / PHASE8_TAG_PLAN
    rows8 = read_csv(p8)
    if rows8:
        return rel(p8, repo), rows8
    return "", []

def field_block(table: str, fields: list[dict[str, Any]]) -> str:
    lines = [f"TABLE: {table}", "ROLE: active physical Messaging DBF table", "FIELDS:"]
    for row in [r for r in fields if r["TABLE"] == table]:
        nullable = row.get("NULLABLE", "")
        logical = row.get("LOGICAL_NAME", "")
        suffix = ""
        if logical:
            suffix += f" LOGICAL={logical}"
        if nullable != "":
            suffix += f" NULLABLE={nullable}"
        lines.append(f"  {row['FIELD_NAME']} TYPE={row['TYPE']} LEN={row['LENGTH']} DEC={row['DECIMALS']}{suffix}")
    return "\n".join(lines)

def tag_block(table: str, tags: list[dict[str, str]]) -> str:
    table_tags = [r for r in tags if (r.get("TABLE_NAME") or "").strip().upper() == table]
    lines = ["TAGS:"]
    if not table_tags:
        lines.append("  TAG_RECONCILIATION_PENDING")
        return "\n".join(lines)
    for row in table_tags:
        tag = row.get("TAG_NAME", "")
        expr = row.get("EXPRESSION", "")
        unique = row.get("UNIQUE", "")
        req = row.get("REQUIRED_FOR", "")
        lines.append(f"  {tag} EXPR={expr} UNIQUE={unique} REQUIRED_FOR={req}")
    return "\n".join(lines)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--accept-report-only-clean-candidate", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23q = first_row(reports / "locale_phase23q_message_schema_reconciliation_status_summary_v1.csv")
    latest = {}
    latest_path = reports / "locale_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("OPERATOR_ACCEPTED_REPORT_ONLY_CLEAN_CANDIDATE",
         args.accept_report_only_clean_candidate,
         "requires --accept-report-only-clean-candidate")
    gate("PHASE23Q_RECONCILIATION_GREEN",
         phase23q.get("STATUS") == "LOCALE_PHASE23Q_MESSAGE_CATALOG_SCHEMA_RECONCILIATION_GREEN_REPORT_ONLY",
         phase23q.get("STATUS", ""))
    gate("PHASE23Q_VALIDATION_ZERO",
         phase23q.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23q.get('VALIDATION_ISSUES', '')}")
    review("LATEST_SAVEPOINT_IS_23Q_OR_LATER",
           latest.get("savepoint_id") in {"LOC-023Q-MESSAGE-SCHEMA-RECON", "LOC-023R-MESSAGE-SCHEMA-CLEAN"},
           f"latest_savepoint={latest.get('savepoint_id', '')}")

    raw_fields = read_csv(repo / FIELDS_REPORT)
    gate("PHASE23Q_FIELD_REPORT_PRESENT", len(raw_fields) > 0, rel(repo / FIELDS_REPORT, repo))

    valid_rows: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    for row in raw_fields:
        ok, reason = is_valid_field(row)
        out = {
            "TABLE": (row.get("TABLE") or "").strip().upper(),
            "ORDINAL": row.get("ORDINAL", ""),
            "FIELD_NAME": (row.get("DBF_DESCRIPTOR_NAME") or "").strip().upper(),
            "TYPE": (row.get("TYPE") or "").strip().upper(),
            "LENGTH": row.get("LENGTH", ""),
            "DECIMALS": row.get("DECIMALS", ""),
            "RECONCILE_STATUS": "VALID_FIELD" if ok else "FILTERED_OUT",
            "REASON": reason,
        }
        if ok:
            valid_rows.append(out)
        else:
            invalid_rows.append(out)

    system_messages_fields = [r for r in valid_rows if r["TABLE"] == "SYSTEM_MESSAGES"]
    system_text_fields = [r for r in valid_rows if r["TABLE"] == "SYSTEM_MESSAGE_TEXT"]

    gate("SYSTEM_MESSAGES_VALID_FIELDS_PRESENT",
         len(system_messages_fields) >= 9,
         f"valid_fields={len(system_messages_fields)}")
    gate("SYSTEM_MESSAGE_TEXT_VALID_FIELDS_PRESENT",
         len(system_text_fields) >= 8,
         f"valid_fields={len(system_text_fields)}")
    review("INVALID_DESCRIPTOR_ROWS_FOUND_AND_FILTERED",
           len(invalid_rows) > 0,
           f"invalid_rows={len(invalid_rows)}")

    tag_source, tag_rows = load_preferred_tag_rows(repo)
    gate("MESSAGE_TAG_PLAN_PRESENT",
         len(tag_rows) > 0,
         tag_source)

    draft = repo / CLEAN_DRAFT
    draft.parent.mkdir(parents=True, exist_ok=True)

    draft_text = f"""# message_catalog.dtschema
# Phase 23R clean candidate.
# Target active path after later authorization:
#   dottalkpp/data/schemas/messaging/message_catalog.dtschema
#
# Source evidence:
#   docs/locale/reports/locale_phase23q_active_messaging_dbf_fields_v1.csv
#   {tag_source}
#
# Reconciliation notes:
#   Phase 23Q raw DBF header scan exposed invalid x64 descriptor tokens.
#   Phase 23R filters invalid/blank descriptors and keeps only field-like rows.
#   This remains a candidate draft until active promotion is explicitly authorized.

SCHEMA_ID: MESSAGE_CATALOG
SCHEMA_STATUS: CLEAN_CANDIDATE_FILTERED_FROM_ACTIVE_DBF_FIELD_EVIDENCE
ACTIVE_SCHEMA_TARGET: dottalkpp/data/schemas/messaging/message_catalog.dtschema
PROMOTION_STATUS: NOT_PROMOTED

{field_block("SYSTEM_MESSAGES", valid_rows)}
{tag_block("SYSTEM_MESSAGES", tag_rows)}

{field_block("SYSTEM_MESSAGE_TEXT", valid_rows)}
{tag_block("SYSTEM_MESSAGE_TEXT", tag_rows)}

EXPECTED_RUNTIME_PROOF:
  MESSAGE_COUNT: 12
  TEXT_ROW_COUNT: 60
  LOCALES: de;en-US;es;fr;it

PROMOTION_REQUIREMENTS:
  PHASE23R_CLEAN_CANDIDATE_REVIEWED: required
  ACTIVE_SCHEMA_PROMOTION_AUTHORIZED: required
  NO_ACTIVE_DBF_CDX_LMDB_MUTATION: required
"""
    draft.write_text(draft_text, encoding="utf-8")

    draft_rows = [{
        "DRAFT_PATH": rel(draft, repo),
        "TARGET_PATH": str(TARGET_ACTIVE).replace("\\", "/"),
        "SCHEMA_ID": "MESSAGE_CATALOG",
        "STATUS": "CLEAN_CANDIDATE_READY_FOR_PROMOTION_PLAN",
        "BYTES": draft.stat().st_size,
        "SHA256": sha256_file(draft),
    }]

    promotion_plan = [
        {
            "STEP": 1,
            "ACTION": "REVIEW_CLEAN_CANDIDATE",
            "DETAIL": "Confirm filtered field rows match intended active Messaging physical schema.",
        },
        {
            "STEP": 2,
            "ACTION": "PROMOTE_MESSAGE_SCHEMA_CONTRACT_ONLY",
            "DETAIL": "Later guarded phase may create dottalkpp/data/schemas/messaging/message_catalog.dtschema from the clean candidate.",
        },
        {
            "STEP": 3,
            "ACTION": "VALIDATE_HASH_AND_REQUIRED_TEXT",
            "DETAIL": "Validate active schema hash equals clean candidate and includes required tables/tags.",
        },
        {
            "STEP": 4,
            "ACTION": "UPDATE_MSGMGR_STATUS",
            "DETAIL": "After active schema promotion, change MSGMGR STATUS from held to active Messaging schema path.",
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_SCHEMA_CONTRACTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active schema promotion in Phase 23R."},
        {"PROTECTED_SYSTEM": "DOCS_CANDIDATE_SCHEMA_DRAFTS", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1, "DETAIL": "Clean candidate schema draft created under docs/locale/schemas/candidates."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "BUILD_RUNTIME", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No build/runtime execution."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "locale_phase23r_message_schema_clean_candidate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "REPORT_ONLY_CLEAN_CANDIDATE": 1,
        "ACTIVE_SCHEMA_MUTATION_AUTHORIZED": 0,
        "ACTIVE_SCHEMA_FILES_CREATED": 0,
        "CANDIDATE_SCHEMA_DRAFTS_CREATED": 1,
        "RAW_FIELD_ROWS": len(raw_fields),
        "VALID_FIELD_ROWS": len(valid_rows),
        "FILTERED_DESCRIPTOR_ROWS": len(invalid_rows),
        "TAG_ROWS": len(tag_rows),
        "TAG_SOURCE": tag_source,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "REPORT_ONLY_CLEAN_CANDIDATE",
         "ACTIVE_SCHEMA_MUTATION_AUTHORIZED", "ACTIVE_SCHEMA_FILES_CREATED",
         "CANDIDATE_SCHEMA_DRAFTS_CREATED", "RAW_FIELD_ROWS", "VALID_FIELD_ROWS",
         "FILTERED_DESCRIPTOR_ROWS", "TAG_ROWS", "TAG_SOURCE", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23r_message_schema_clean_candidate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23r_message_schema_valid_fields_v1.csv", valid_rows,
              ["TABLE", "ORDINAL", "FIELD_NAME", "TYPE", "LENGTH", "DECIMALS", "RECONCILE_STATUS", "REASON"])
    write_csv(reports / "locale_phase23r_message_schema_filtered_descriptors_v1.csv", invalid_rows,
              ["TABLE", "ORDINAL", "FIELD_NAME", "TYPE", "LENGTH", "DECIMALS", "RECONCILE_STATUS", "REASON"])
    write_csv(reports / "locale_phase23r_message_schema_tag_rows_v1.csv", tag_rows,
              ["TABLE_NAME", "TAG_NAME", "EXPRESSION", "UNIQUE", "REQUIRED_FOR", "EXECUTE_IN_PHASE13"])
    write_csv(reports / "locale_phase23r_message_schema_candidate_draft_v1.csv", draft_rows,
              ["DRAFT_PATH", "TARGET_PATH", "SCHEMA_ID", "STATUS", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23r_message_schema_promotion_plan_v1.csv", promotion_plan,
              ["STEP", "ACTION", "DETAIL"])
    write_csv(reports / "locale_phase23r_message_schema_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    doc = repo / "docs/locale/LOCALE_PHASE23R_MESSAGE_SCHEMA_CLEAN_CANDIDATE.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(f"""# Locale Phase 23R — Message Schema Clean Candidate

Status: `{status}`

Phase 23Q exposed invalid raw DBF descriptor rows in the active Messaging field
scan. Phase 23R filters those invalid descriptor rows and creates a clean
candidate schema draft:

```text
{rel(draft, repo)}
```

This phase does not promote the active schema contract.

## Next gate

```text
{NEXT_GATE}
```
""", encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print("  report-only clean candidate: 1")
    print("  active schema mutation authorized: 0")
    print("  active schema files created: 0")
    print("  candidate schema drafts created: 1")
    print(f"  raw field rows: {len(raw_fields)}")
    print(f"  valid field rows: {len(valid_rows)}")
    print(f"  filtered descriptor rows: {len(invalid_rows)}")
    print(f"  tag rows: {len(tag_rows)}")
    print(f"  tag source: {tag_source}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
