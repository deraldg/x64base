#!/usr/bin/env python3
"""
DotTalk++ Messaging Phase 7
Promotion-readiness plan only for SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT.

This script reads the Phase 6 source-side message catalog exports and creates
review reports for a future guarded DBF/catalog promotion.

It intentionally does NOT:
  - create DBF tables
  - write catalog DBFs
  - rebuild HELP DATA
  - mutate CMDHELPCHK
  - run DotTalk++ runtime
  - promote metadata
  - edit source files
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


STATUS_GREEN = "MESSAGE_CATALOG_PHASE7_PROMOTION_READINESS_PLAN_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE7_PROMOTION_READINESS_PLAN_BLOCKED"


REQUIRED_SYSTEM_MESSAGES_COLUMNS = [
    "MESSAGE_ID",
    "SYMBOL",
    "ENUM_NAME",
    "FACILITY",
    "OWNER_SUBSYSTEM",
    "CATEGORY",
    "SEVERITY",
]

REQUIRED_SYSTEM_MESSAGE_TEXT_COLUMNS = [
    "MESSAGE_ID",
    "SYMBOL",
    "ENUM_NAME",
    "LOCALE",
    "TEXT_TEMPLATE",
]

EXPECTED_LOCALES = ["de", "en-US", "es", "fr", "it"]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, object]], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({c: row.get(c, "") for c in columns})


def csv_columns(path: Path) -> List[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            return next(reader)
        except StopIteration:
            return []


def missing_columns(actual: Iterable[str], required: Iterable[str]) -> List[str]:
    aset = set(actual)
    return [c for c in required if c not in aset]


def unique_values(rows: List[Dict[str, str]], key: str) -> List[str]:
    return sorted({(r.get(key) or "").strip() for r in rows if (r.get(key) or "").strip()})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, help="Repository root, e.g. D:\\code\\ccode")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs" / "messaging" / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    phase6_status_path = reports / "message_catalog_phase6_status_summary_v1.csv"
    phase6_messages_path = reports / "message_catalog_phase6_system_messages_v1.csv"
    phase6_text_path = reports / "message_catalog_phase6_system_message_text_v1.csv"
    phase6_validation_path = reports / "message_catalog_phase6_validation_v1.csv"
    phase6_boundary_path = reports / "message_catalog_phase6_boundary_ledger_v1.csv"

    phase6_status = read_csv(phase6_status_path)
    messages = read_csv(phase6_messages_path)
    text_rows = read_csv(phase6_text_path)
    validation_rows = read_csv(phase6_validation_path)
    boundary_rows = read_csv(phase6_boundary_path)

    blockers: List[Dict[str, object]] = []

    def add_blocker(code: str, detail: str) -> None:
        blockers.append({"GATE": code, "STATUS": "FAIL", "DETAIL": detail})

    if not phase6_status:
        add_blocker("PHASE6_STATUS_PRESENT", f"Missing or empty {phase6_status_path}")
    else:
        status = phase6_status[0].get("STATUS", "")
        if status != "MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_GREEN":
            add_blocker("PHASE6_STATUS_GREEN", f"Expected MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_GREEN, got {status!r}")

    if not messages:
        add_blocker("SYSTEM_MESSAGES_ROWS_PRESENT", f"Missing or empty {phase6_messages_path}")

    if not text_rows:
        add_blocker("SYSTEM_MESSAGE_TEXT_ROWS_PRESENT", f"Missing or empty {phase6_text_path}")

    msg_missing = missing_columns(csv_columns(phase6_messages_path), REQUIRED_SYSTEM_MESSAGES_COLUMNS)
    if msg_missing:
        add_blocker("SYSTEM_MESSAGES_REQUIRED_COLUMNS", "Missing: " + ", ".join(msg_missing))

    text_missing = missing_columns(csv_columns(phase6_text_path), REQUIRED_SYSTEM_MESSAGE_TEXT_COLUMNS)
    if text_missing:
        add_blocker("SYSTEM_MESSAGE_TEXT_REQUIRED_COLUMNS", "Missing: " + ", ".join(text_missing))

    if validation_rows:
        add_blocker("PHASE6_VALIDATION_EMPTY", f"Phase 6 validation rows found: {len(validation_rows)}")

    if messages and text_rows:
        message_ids = {(r.get("MESSAGE_ID") or "").strip() for r in messages}
        text_message_ids = {(r.get("MESSAGE_ID") or "").strip() for r in text_rows}
        orphan_text = sorted(text_message_ids - message_ids)
        missing_text_ids = sorted(message_ids - text_message_ids)
        if orphan_text:
            add_blocker("NO_ORPHAN_TEXT_ROWS", "Orphan text MESSAGE_ID values: " + ", ".join(orphan_text))
        if missing_text_ids:
            add_blocker("EVERY_MESSAGE_HAS_TEXT", "Message IDs without text rows: " + ", ".join(missing_text_ids))

        locales = unique_values(text_rows, "LOCALE")
        if locales != EXPECTED_LOCALES:
            add_blocker("EXPECTED_LOCALES_MATCH", f"Expected {EXPECTED_LOCALES}, got {locales}")

        # Every message should have one row for every locale.
        by_msg: Dict[str, set] = {}
        dup_keys: List[str] = []
        seen_keys = set()
        for r in text_rows:
            mid = (r.get("MESSAGE_ID") or "").strip()
            loc = (r.get("LOCALE") or "").strip()
            key = (mid, loc)
            if key in seen_keys:
                dup_keys.append(f"{mid}/{loc}")
            seen_keys.add(key)
            by_msg.setdefault(mid, set()).add(loc)
        for mid in sorted(message_ids):
            locs = by_msg.get(mid, set())
            missing = [l for l in EXPECTED_LOCALES if l not in locs]
            if missing:
                add_blocker("EVERY_MESSAGE_HAS_EVERY_LOCALE", f"MESSAGE_ID {mid} missing locales: {', '.join(missing)}")
        if dup_keys:
            add_blocker("NO_DUPLICATE_MESSAGE_LOCALE_ROWS", "Duplicates: " + ", ".join(sorted(dup_keys)))

    fail_count = len(blockers)
    status = STATUS_GREEN if fail_count == 0 else STATUS_BLOCKED

    now = _dt.datetime.now().isoformat(timespec="seconds")

    status_rows = [{
        "STATUS": status,
        "MESSAGES": len(messages),
        "TEXT_ROWS": len(text_rows),
        "LOCALES": ";".join(unique_values(text_rows, "LOCALE")),
        "VALIDATION_ISSUES": len(validation_rows),
        "PROMOTION_AUTHORIZED": 0,
        "DBF_WRITES": 0,
        "HELP_DATA_MUTATION": 0,
        "CMDHELPCHK_MUTATION": 0,
        "SOURCE_MINING_MUTATION": 0,
        "GENERATED_AT": now,
        "NEXT_GATE": "HOLD_OR_AUTHORIZE_PHASE8_GUARDED_DBF_SCHEMA_STAGING_PLAN",
    }]

    schema_rows = [
        {
            "TABLE_NAME": "SYSTEM_MESSAGES",
            "SOURCE_REPORT": str(phase6_messages_path.relative_to(repo)),
            "SOURCE_ROWS": len(messages),
            "REQUIRED_COLUMNS": ";".join(REQUIRED_SYSTEM_MESSAGES_COLUMNS),
            "MISSING_COLUMNS": ";".join(msg_missing),
            "READINESS": "READY" if not msg_missing and messages else "BLOCKED",
            "PROMOTION_ACTION": "PLAN_ONLY_NO_DBF_WRITE",
        },
        {
            "TABLE_NAME": "SYSTEM_MESSAGE_TEXT",
            "SOURCE_REPORT": str(phase6_text_path.relative_to(repo)),
            "SOURCE_ROWS": len(text_rows),
            "REQUIRED_COLUMNS": ";".join(REQUIRED_SYSTEM_MESSAGE_TEXT_COLUMNS),
            "MISSING_COLUMNS": ";".join(text_missing),
            "READINESS": "READY" if not text_missing and text_rows else "BLOCKED",
            "PROMOTION_ACTION": "PLAN_ONLY_NO_DBF_WRITE",
        },
    ]

    field_map_rows = [
        {"TABLE_NAME": "SYSTEM_MESSAGES", "SOURCE_COLUMN": "MESSAGE_ID", "TARGET_FIELD": "MESSAGE_ID", "TYPE_HINT": "N", "NOTES": "Stable numeric message identity from compiled catalog preview."},
        {"TABLE_NAME": "SYSTEM_MESSAGES", "SOURCE_COLUMN": "SYMBOL", "TARGET_FIELD": "SYMBOL", "TYPE_HINT": "C", "NOTES": "Stable symbolic key, e.g. UNKNOWN_COMMAND."},
        {"TABLE_NAME": "SYSTEM_MESSAGES", "SOURCE_COLUMN": "ENUM_NAME", "TARGET_FIELD": "ENUM_NAME", "TYPE_HINT": "C", "NOTES": "C++ enum name for source/runtime bridge."},
        {"TABLE_NAME": "SYSTEM_MESSAGES", "SOURCE_COLUMN": "FACILITY", "TARGET_FIELD": "FACILITY", "TYPE_HINT": "C", "NOTES": "Facility/lane such as GLOBAL, MESSAGING, DBAREA."},
        {"TABLE_NAME": "SYSTEM_MESSAGES", "SOURCE_COLUMN": "OWNER_SUBSYSTEM", "TARGET_FIELD": "OWNER_SUBSYSTEM", "TYPE_HINT": "C", "NOTES": "Subsystem owner for validation and responsibility."},
        {"TABLE_NAME": "SYSTEM_MESSAGES", "SOURCE_COLUMN": "CATEGORY", "TARGET_FIELD": "CATEGORY", "TYPE_HINT": "C", "NOTES": "Message category such as ERROR, STATUS, HINT."},
        {"TABLE_NAME": "SYSTEM_MESSAGES", "SOURCE_COLUMN": "SEVERITY", "TARGET_FIELD": "SEVERITY", "TYPE_HINT": "C", "NOTES": "INFO/WARNING/ERROR etc."},
        {"TABLE_NAME": "SYSTEM_MESSAGE_TEXT", "SOURCE_COLUMN": "MESSAGE_ID", "TARGET_FIELD": "MESSAGE_ID", "TYPE_HINT": "N", "NOTES": "Foreign key to SYSTEM_MESSAGES.MESSAGE_ID."},
        {"TABLE_NAME": "SYSTEM_MESSAGE_TEXT", "SOURCE_COLUMN": "SYMBOL", "TARGET_FIELD": "SYMBOL", "TYPE_HINT": "C", "NOTES": "Redundant human-readable join key."},
        {"TABLE_NAME": "SYSTEM_MESSAGE_TEXT", "SOURCE_COLUMN": "ENUM_NAME", "TARGET_FIELD": "ENUM_NAME", "TYPE_HINT": "C", "NOTES": "C++ enum bridge for review."},
        {"TABLE_NAME": "SYSTEM_MESSAGE_TEXT", "SOURCE_COLUMN": "LOCALE", "TARGET_FIELD": "LOCALE", "TYPE_HINT": "C", "NOTES": "Locale key, e.g. en-US, it, es."},
        {"TABLE_NAME": "SYSTEM_MESSAGE_TEXT", "SOURCE_COLUMN": "TEXT_TEMPLATE", "TARGET_FIELD": "TEXT_TEMPLATE", "TYPE_HINT": "M/C", "NOTES": "Localized whole-message template with named placeholders."},
    ]

    import_plan_rows = [
        {"STEP": 1, "ACTION": "VERIFY_PHASE6_EXPORTS", "INPUT": "docs/messaging/reports/message_catalog_phase6_*.csv", "OUTPUT": "readiness gate", "MUTATES": 0, "NOTES": "Require Phase 6 green and zero validation rows."},
        {"STEP": 2, "ACTION": "DEFINE_DBF_SCHEMA_PLAN", "INPUT": "phase7 field map", "OUTPUT": "candidate DBF schema script plan", "MUTATES": 0, "NOTES": "Plan only; no DBF creation in Phase 7."},
        {"STEP": 3, "ACTION": "STAGE_CSV_TO_CANDIDATE_IMPORT_INPUTS", "INPUT": "SYSTEM_MESSAGES/SYSTEM_MESSAGE_TEXT CSV", "OUTPUT": "future candidate import package", "MUTATES": 0, "NOTES": "Phase 8 candidate-only staging may copy reports, but not active catalogs."},
        {"STEP": 4, "ACTION": "CREATE_INACTIVE_CANDIDATE_DBF_TABLES", "INPUT": "approved schema", "OUTPUT": "inactive candidate DBFs", "MUTATES": "future_authorization_required", "NOTES": "Not authorized by Phase 7."},
        {"STEP": 5, "ACTION": "IMPORT_AND_VALIDATE_CANDIDATE", "INPUT": "inactive candidate DBFs", "OUTPUT": "candidate readback reports", "MUTATES": "future_authorization_required", "NOTES": "Must stay outside active HELP/META/CMDHELPCHK catalogs until separately authorized."},
        {"STEP": 6, "ACTION": "PROMOTION_DECISION", "INPUT": "candidate readback + boundary ledger", "OUTPUT": "hold/promote decision", "MUTATES": "not_in_phase7", "NOTES": "Promotion explicitly out of scope."},
    ]

    gate_rows = []
    checks = [
        ("PHASE6_STATUS_GREEN", fail_count == 0 or not any(b["GATE"] == "PHASE6_STATUS_GREEN" for b in blockers)),
        ("SYSTEM_MESSAGES_REQUIRED_COLUMNS", not msg_missing),
        ("SYSTEM_MESSAGE_TEXT_REQUIRED_COLUMNS", not text_missing),
        ("PHASE6_VALIDATION_EMPTY", not validation_rows),
        ("PROMOTION_NOT_AUTHORIZED", True),
        ("DBF_WRITES_ZERO", True),
        ("HELP_CMDHELPCHK_MUTATION_ZERO", True),
    ]
    blocker_by_gate = {b["GATE"]: b["DETAIL"] for b in blockers}
    for name, ok in checks:
        gate_rows.append({
            "GATE": name,
            "STATUS": "PASS" if ok and name not in blocker_by_gate else "FAIL",
            "DETAIL": blocker_by_gate.get(name, "OK"),
        })
    # Add any blockers not already represented.
    represented = {r["GATE"] for r in gate_rows}
    for b in blockers:
        if b["GATE"] not in represented:
            gate_rows.append(b)

    boundary_rows_out = [
        {"PROTECTED_SYSTEM": "DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 7 reads Phase 6 CSV reports only. No DBF create/open-for-write/import/promotion."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source files edited by this script."},
        {"PROTECTED_SYSTEM": "RUNTIME_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DotTalk++ runtime execution required."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion authorized or performed."},
    ]

    write_csv(reports / "message_catalog_phase7_status_summary_v1.csv", status_rows,
              ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES", "PROMOTION_AUTHORIZED",
               "DBF_WRITES", "HELP_DATA_MUTATION", "CMDHELPCHK_MUTATION", "SOURCE_MINING_MUTATION",
               "GENERATED_AT", "NEXT_GATE"])
    write_csv(reports / "message_catalog_phase7_schema_readiness_v1.csv", schema_rows,
              ["TABLE_NAME", "SOURCE_REPORT", "SOURCE_ROWS", "REQUIRED_COLUMNS", "MISSING_COLUMNS", "READINESS", "PROMOTION_ACTION"])
    write_csv(reports / "message_catalog_phase7_field_mapping_v1.csv", field_map_rows,
              ["TABLE_NAME", "SOURCE_COLUMN", "TARGET_FIELD", "TYPE_HINT", "NOTES"])
    write_csv(reports / "message_catalog_phase7_import_plan_v1.csv", import_plan_rows,
              ["STEP", "ACTION", "INPUT", "OUTPUT", "MUTATES", "NOTES"])
    write_csv(reports / "message_catalog_phase7_gate_check_v1.csv", gate_rows,
              ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase7_boundary_ledger_v1.csv", boundary_rows_out,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md_path = reports / "MESSAGE_CATALOG_PHASE7_PROMOTION_READINESS_PLAN.md"
    md = f"""# Message Catalog Phase 7 Promotion-Readiness Plan

Status: **{status}**

Generated: {now}

## Scope

Phase 7 is a report-only promotion-readiness plan for a future DBF-backed message catalog.

It consumes the Phase 6 exports:

- `message_catalog_phase6_system_messages_v1.csv`
- `message_catalog_phase6_system_message_text_v1.csv`

It plans the future catalog tables:

- `SYSTEM_MESSAGES`
- `SYSTEM_MESSAGE_TEXT`

## Summary

- Messages: {len(messages)}
- Text rows: {len(text_rows)}
- Locales: {", ".join(unique_values(text_rows, "LOCALE"))}
- Phase 6 validation rows: {len(validation_rows)}
- Promotion authorized: 0
- DBF writes: 0

## Boundary

No DBF catalogs, HELP DATA, CMDHELPCHK, source-mining lanes, source files, runtime state,
or active catalogs are mutated by this phase.

## Next Gate

`HOLD_OR_AUTHORIZE_PHASE8_GUARDED_DBF_SCHEMA_STAGING_PLAN`

Phase 8, if authorized, should still be candidate-only / inactive-catalog staging first.
"""
    md_path.write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {len(messages)}")
    print(f"  text rows: {len(text_rows)}")
    print(f"  locales: {', '.join(unique_values(text_rows, 'LOCALE'))}")
    print(f"  validation issues: {len(validation_rows)}")
    print(f"  promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2


if __name__ == "__main__":
    raise SystemExit(main())
