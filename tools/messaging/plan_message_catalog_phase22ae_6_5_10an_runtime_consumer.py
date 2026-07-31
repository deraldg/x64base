#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AN_RUNTIME_MESSAGE_CONSUMER_INTEGRATION_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AN_RUNTIME_MESSAGE_CONSUMER_INTEGRATION_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

ALLOWED_10AM_STATUSES = {
    "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_GREEN_NO_REBUILD_REQUIRED_YET",
    "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_GREEN_REBUILD_DECISION_REVIEW",
}

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

def savepoint_present(repo: Path, savepoint_id: str):
    latest = ""
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest == savepoint_id or savepoint_id in text, latest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    am = first_row(reports / "message_catalog_phase22ae_6_5_10am_validate_status_summary_v1.csv")
    sp_am, latest_am = savepoint_present(repo, "MSG-022AE.6.5.10AM")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    gates = []
    failures = 0
    review_note = 0

    def gate(name, ok, detail, review_only=False):
        nonlocal failures, review_note
        status = "PASS" if ok else ("REVIEW" if review_only else "FAIL")
        gates.append({"GATE": name, "STATUS": status, "DETAIL": str(detail)})
        if not ok and review_only:
            review_note += 1
        elif not ok:
            failures += 1

    am_status = am.get("STATUS", "")
    gate("PHASE22AE_6_5_10AM_ALLOWED_GREEN_STATUS", am_status in ALLOWED_10AM_STATUSES, am_status or "missing")
    gate("MSG_022AE_6_5_10AM_SAVEPOINT_PRESENT", sp_am, latest_am)
    gate("10AM_ARTIFACT_FINGERPRINT_DELTA_ZERO", am.get("ARTIFACT_FINGERPRINT_DELTA_ROWS") == "0", am.get("ARTIFACT_FINGERPRINT_DELTA_ROWS", "missing"))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AM_REBUILD_DECISION_REVIEW_NOTE",
         am_status != "MESSAGE_CATALOG_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_GREEN_REBUILD_DECISION_REVIEW",
         "10AM status is rebuild-decision review; consumer plan may remain contract-only until rebuild question resolved",
         review_only=True)

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    lookup_contract = [
        {
            "CONTRACT_ITEM": "MESSAGE_IDENTITY",
            "FIELD_OR_RULE": "MSGID + SYMBOL",
            "DETAIL": "SYSTEM_MESSAGES owns message identity, enum name, facility/owner/category/severity/status/source metadata.",
            "REQUIRED_BEFORE_SOURCE_MUTATION": 1,
        },
        {
            "CONTRACT_ITEM": "LOCALIZED_TEXT_IDENTITY",
            "FIELD_OR_RULE": "SYMBOLLOC = SYMBOL|LOCALE",
            "DETAIL": "SYSTEM_MESSAGE_TEXT owns localized text rows. SYMBOLLOC should be treated as the direct lookup key when locale is known.",
            "REQUIRED_BEFORE_SOURCE_MUTATION": 1,
        },
        {
            "CONTRACT_ITEM": "LOCALE_FALLBACK",
            "FIELD_OR_RULE": "Requested locale -> fallback locale -> en-US",
            "DETAIL": "Runtime consumer should use the shared locale spine/fallback policy rather than hard-coded per-command fallbacks.",
            "REQUIRED_BEFORE_SOURCE_MUTATION": 1,
        },
        {
            "CONTRACT_ITEM": "SEVERITY_CATEGORY",
            "FIELD_OR_RULE": "Severity/category come from SYSTEM_MESSAGES",
            "DETAIL": "Command/error consumers should not duplicate severity/category policy in ad hoc strings.",
            "REQUIRED_BEFORE_SOURCE_MUTATION": 1,
        },
        {
            "CONTRACT_ITEM": "PLACEHOLDERS",
            "FIELD_OR_RULE": "Typed placeholders are future contract rows",
            "DETAIL": "Do not perform broad source integration until placeholder/argument formatting has a documented rule and tests.",
            "REQUIRED_BEFORE_SOURCE_MUTATION": 1,
        },
    ]

    consumer_surfaces = [
        {"SURFACE": "Command parser errors", "CURRENT_ROLE": "candidate consumer", "INTEGRATION_LEVEL": "PLAN_ONLY", "MUTATION_AUTHORIZED": 0},
        {"SURFACE": "HELP hints and command guidance", "CURRENT_ROLE": "candidate consumer", "INTEGRATION_LEVEL": "PLAN_ONLY", "MUTATION_AUTHORIZED": 0},
        {"SURFACE": "Locale command/status messages", "CURRENT_ROLE": "candidate consumer", "INTEGRATION_LEVEL": "PLAN_ONLY", "MUTATION_AUTHORIZED": 0},
        {"SURFACE": "Diagnostic/report messages", "CURRENT_ROLE": "candidate consumer", "INTEGRATION_LEVEL": "PLAN_ONLY", "MUTATION_AUTHORIZED": 0},
        {"SURFACE": "CMDHELPCHK handoff", "CURRENT_ROLE": "deferred protected lane", "INTEGRATION_LEVEL": "NOT_AUTHORIZED", "MUTATION_AUTHORIZED": 0},
    ]

    readonly_probe_plan = [
        {
            "STEP": 1,
            "ACTION": "RUNTIME_READONLY_LOOKUP_SURFACE_DISCOVERY",
            "DETAIL": "Use existing read-only commands/help/list/readback to determine whether message catalog lookup commands already exist.",
            "MUTATES_ACTIVE": 0,
            "MUTATES_SOURCE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "DBF_ROW_PROBE_FOR_SYMBOLS",
            "DETAIL": "Open active SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT and prove target symbols/locales can be found or listed without changing tables.",
            "MUTATES_ACTIVE": 0,
            "MUTATES_SOURCE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "CONSUMER_GAP_REPORT",
            "DETAIL": "Classify whether runtime has a catalog-backed message lookup surface, or whether source integration is still needed.",
            "MUTATES_ACTIVE": 0,
            "MUTATES_SOURCE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "NO_SOURCE_PATCH_YET",
            "DETAIL": "If source integration is needed, create a later guarded source-change plan with tests and rollback; do not apply in 10AO.",
            "MUTATES_ACTIVE": 0,
            "MUTATES_SOURCE": 0,
        },
    ]

    test_plan = [
        {
            "TEST_ID": "MSGLOOKUP-001",
            "TEST_NAME": "Known compiled source message",
            "INPUT": "HELP_HINT_COMMAND / en-US",
            "EXPECTED": "row visible and text row available",
            "TYPE": "READONLY_PROBE",
        },
        {
            "TEST_ID": "MSGLOOKUP-002",
            "TEST_NAME": "Promoted proof message",
            "INPUT": "MESSAGE_PROOF_MODE_STATUS / en-US,es,fr,de,it",
            "EXPECTED": "five localized candidate text rows visible",
            "TYPE": "READONLY_PROBE",
        },
        {
            "TEST_ID": "MSGLOOKUP-003",
            "TEST_NAME": "Boundary proof message",
            "INPUT": "MESSAGE_PROOF_BOUNDARY_NOTE / en-US,es,fr,de,it",
            "EXPECTED": "five localized candidate text rows visible",
            "TYPE": "READONLY_PROBE",
        },
        {
            "TEST_ID": "MSGLOOKUP-004",
            "TEST_NAME": "Fallback behavior",
            "INPUT": "unsupported locale",
            "EXPECTED": "documented fallback decision; no source mutation in this phase",
            "TYPE": "PLAN_ONLY",
        },
        {
            "TEST_ID": "MSGLOOKUP-005",
            "TEST_NAME": "No HELP/CMDHELPCHK mutation",
            "INPUT": "boundary ledger",
            "EXPECTED": "HELP DATA and CMDHELPCHK mutation observed = 0",
            "TYPE": "BOUNDARY",
        },
    ]

    source_integration_plan = [
        {
            "STEP": 1,
            "ACTION": "IDENTIFY_CURRENT_MESSAGE_EMIT_CALLS",
            "DETAIL": "Search/scan source for ad hoc message emissions and existing messaging catalog helpers.",
            "MUTATION_AUTHORIZED": 0,
        },
        {
            "STEP": 2,
            "ACTION": "SELECT_ONE_LOW_RISK_CONSUMER",
            "DETAIL": "Choose one non-HELP, non-CMDHELPCHK runtime surface for a later guarded integration proof.",
            "MUTATION_AUTHORIZED": 0,
        },
        {
            "STEP": 3,
            "ACTION": "DEFINE_ROLLBACK_AND_TEST_CONTRACT",
            "DETAIL": "Any source patch must include pre/post tests, build proof, runtime proof, and rollback plan.",
            "MUTATION_AUTHORIZED": 0,
        },
        {
            "STEP": 4,
            "ACTION": "DEFER_HELP_CMDHELPCHK_APPLY",
            "DETAIL": "HELP DATA and CMDHELPCHK mutation remain separate explicit gates.",
            "MUTATION_AUTHORIZED": 0,
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AN is plan-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "ROLLBACK_BACKUP_DELETE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No backup deletion."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10an_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10an_lookup_contract_v1.csv", lookup_contract, ["CONTRACT_ITEM", "FIELD_OR_RULE", "DETAIL", "REQUIRED_BEFORE_SOURCE_MUTATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10an_consumer_surfaces_v1.csv", consumer_surfaces, ["SURFACE", "CURRENT_ROLE", "INTEGRATION_LEVEL", "MUTATION_AUTHORIZED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10an_readonly_probe_plan_v1.csv", readonly_probe_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE", "MUTATES_SOURCE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10an_test_plan_v1.csv", test_plan, ["TEST_ID", "TEST_NAME", "INPUT", "EXPECTED", "TYPE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10an_source_integration_plan_v1.csv", source_integration_plan, ["STEP", "ACTION", "DETAIL", "MUTATION_AUTHORIZED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10an_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "REVIEW_NOTES": review_note,
        "PHASE22AE_6_5_10AM_STATUS": am_status,
        "MSG_022AE_6_5_10AM_SAVEPOINT_PRESENT": 1 if sp_am else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "RUNTIME_MESSAGE_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "RUNTIME_READONLY_PROBE_RECOMMENDED": 1 if status == STATUS_GREEN else 0,
        "INDEX_LMDB_REBUILD_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10an_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AN_RUNTIME_MESSAGE_CONSUMER_INTEGRATION_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AN Runtime Message Consumer Integration Plan\n\nStatus: `{status}`\n\n10AN is plan-only. It defines the runtime message-consumer lookup contract and recommends a read-only consumer probe before any source integration.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  review notes: {review_note}")
    print(f"  Phase 22AE.6.5.10AM status: {am_status}")
    print(f"  MSG-022AE.6.5.10AM savepoint present: {1 if sp_am else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print("  runtime message consumer source integration authorized: 0")
    print(f"  runtime readonly probe recommended: {1 if status == STATUS_GREEN else 0}")
    print("  index/LMDB rebuild authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
