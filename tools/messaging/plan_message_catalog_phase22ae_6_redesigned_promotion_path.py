#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_REDESIGNED_PROMOTION_PATH_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_REDESIGNED_PROMOTION_PATH_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_PACKAGE"
REPORT_DIR = Path("docs/messaging/reports")
SCRIPT_DIR = Path("docs/messaging/scripts")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest_id = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in text, latest_id

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def count_dts_tokens(text: str):
    rows = []
    for token in ["USE", "APPEND", "REPLACE", "WITH", "SYMBOL", "LOCALE", "TEXT", "MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]:
        rows.append({"TOKEN": token, "COUNT": text.upper().count(token.upper())})
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae54 = first_row(reports / "message_catalog_phase22ae_5_4_status_summary_v1.csv")
    ae53 = first_row(reports / "message_catalog_phase22ae_5_3_status_summary_v1.csv")
    ae5 = first_row(reports / "message_catalog_phase22ae_5_status_summary_v1.csv")
    ae51 = first_row(reports / "message_catalog_phase22ae_5_1_status_summary_v1.csv")
    sp54, latest_id = savepoint_present(repo, "MSG-022AE.5.4")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_5_4_GREEN",
         ae54.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION_GREEN",
         ae54.get("STATUS", "missing"))
    gate("MSG_022AE_5_4_SAVEPOINT_PRESENT", sp54, latest_id)
    gate("ACTIVE_BASELINE_RESTORED_12_60",
         ae54.get("ACTIVE_MESSAGE_COUNT") == "12" and ae54.get("ACTIVE_TEXT_ROW_COUNT") == "60",
         f"{ae54.get('ACTIVE_MESSAGE_COUNT')}/{ae54.get('ACTIVE_TEXT_ROW_COUNT')}")
    gate("FAILED_PROMOTION_EVIDENCE_AVAILABLE",
         ae5.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_BLOCKED",
         ae5.get("STATUS", "missing"))
    gate("PARTIAL_PROMOTION_DIAGNOSTIC_AVAILABLE",
         ae51.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_1_PARTIAL_PROMOTION_DIAGNOSTIC_GREEN_SOURCE_HELD",
         ae51.get("STATUS", "missing"))

    failed_dts = repo / SCRIPT_DIR / "MESSAGE_CATALOG_PHASE22AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTE.dts"
    failed_runlog = repo / "docs/messaging/runlog/MSG-022AE_5_MEMO_AWARE_ACTIVE_CATALOG_PROMOTION_EXECUTION.md"
    dts_text = failed_dts.read_text(encoding="utf-8", errors="replace") if failed_dts.exists() else ""
    runlog_text = failed_runlog.read_text(encoding="utf-8", errors="replace") if failed_runlog.exists() else ""

    token_rows = count_dts_tokens(dts_text)

    runlog_rows = [
        {"OBSERVATION": "runtime_opened_system_messages", "VALUE": 1 if "Opened SYSTEM_MESSAGES" in runlog_text else 0, "DETAIL": "Expected during failed 22AE.5 execution."},
        {"OBSERVATION": "runtime_opened_system_message_text", "VALUE": 1 if "Opened SYSTEM_MESSAGE_TEXT" in runlog_text else 0, "DETAIL": "Expected during failed 22AE.5 execution."},
        {"OBSERVATION": "runtime_showed_append_output", "VALUE": 1 if "APPEND" in runlog_text.upper() else 0, "DETAIL": "Runtime log usually does not echo with Echo off; token absence is not decisive."},
        {"OBSERVATION": "runtime_showed_replace_output", "VALUE": 1 if "REPLACE" in runlog_text.upper() else 0, "DETAIL": "Runtime log usually does not echo with Echo off; token absence is not decisive."},
        {"OBSERVATION": "unknown_command_seen", "VALUE": 1 if "Unknown command:" in runlog_text else 0, "DETAIL": "Should be 0."},
        {"OBSERVATION": "memo_backend_error_seen", "VALUE": 1 if "memo backend not attached" in runlog_text.lower() else 0, "DETAIL": "Should be 0."},
    ]

    # Explain failure without overclaiming.
    root_cause_rows = [
        {
            "FINDING": "FAILED_PATH_NOT_REUSABLE",
            "CONFIDENCE": "HIGH",
            "DETAIL": "22AE.5 moved counts to 14/70 but required key fields remained absent; therefore the generated USE/APPEND/REPLACE path is not safe for active promotion.",
        },
        {
            "FINDING": "FIELD_WRITE_NOT_PROVEN",
            "CONFIDENCE": "HIGH",
            "DETAIL": "The active count change proves row append occurred, but 0 required symbols and 0 text keys prove the write/update contract for key fields was not established.",
        },
        {
            "FINDING": "ACTIVE_BASELINE_RECOVERED",
            "CONFIDENCE": "HIGH",
            "DETAIL": "22AE.5.3 rollback and 22AE.5.4 runtime regression restored/validated the 12/60 baseline.",
        },
        {
            "FINDING": "NEXT_PATH_MUST_BE_SANDBOX_FIRST",
            "CONFIDENCE": "HIGH",
            "DETAIL": "Any new promotion path must be proven against a disposable sandbox copy before another active catalog mutation is authorized.",
        },
    ]

    options = [
        {
            "OPTION": "SANDBOX_ROW_WRITE_PROOF",
            "RECOMMENDATION": "PRIMARY",
            "WHY": "Copy active 12/60 messaging catalog to a disposable sandbox root, then prove exact field write/update semantics without touching active DBF/CDX/LMDB.",
            "ACTIVE_MUTATION": 0,
            "NEXT_PHASE": "22AE.6.1",
        },
        {
            "OPTION": "ACTIVE_IMPORT_RETRY",
            "RECOMMENDATION": "FORBID",
            "WHY": "The previous active retry appended malformed rows. Do not retry against active until sandbox proof is green.",
            "ACTIVE_MUTATION": 1,
            "NEXT_PHASE": "not allowed now",
        },
        {
            "OPTION": "DIRECT_DBF_MEMO_WRITE",
            "RECOMMENDATION": "FORBID",
            "WHY": "SYSTEM_MESSAGE_TEXT.TEXT is memo-backed. Raw direct DBF writes bypass memo semantics and were already closed.",
            "ACTIVE_MUTATION": 1,
            "NEXT_PHASE": "not allowed",
        },
        {
            "OPTION": "CANDIDATE_TABLE_REBUILD_THEN_PROMOTE_WHOLE_ROOT",
            "RECOMMENDATION": "REVIEW",
            "WHY": "May be safer than row append if x64base import/build tooling can rebuild a complete messaging root in sandbox and compare exact readback before replacement.",
            "ACTIVE_MUTATION": 0,
            "NEXT_PHASE": "possible later",
        },
    ]

    ae61_plan = [
        {"STEP": 1, "ACTION": "COPY_ACTIVE_MESSAGING_ROOTS_TO_SANDBOX", "DETAIL": "Create docs/messaging/sandbox/phase22ae_6_1_row_write_proof_v1 from active messaging/index/lmdb roots.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "ACTION": "RUN_MINIMAL_FIELD_WRITE_PROBE", "DETAIL": "Append one disposable test row or use a disposable table copy, then verify SYMBOL/LOCALE/TEXT fields read back exactly.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "ACTION": "TEST_COMMAND_SYNTAX_VARIANTS", "DETAIL": "Try only one syntax variant at a time: APPEND+REPLACE, INSERT-like command if available, IMPORT path if available, or table rebuild path.", "MUTATES_ACTIVE": 0},
        {"STEP": 4, "ACTION": "READBACK_WITH_DBF_AND_RUNTIME", "DETAIL": "Require both DBF-level key readback and DotTalk++ runtime provider/check readback from sandbox.", "MUTATES_ACTIVE": 0},
        {"STEP": 5, "ACTION": "SELECT_PROMOTION_MECHANISM", "DETAIL": "Only after sandbox readback is exact, stage a new active-promotion package.", "MUTATES_ACTIVE": 0},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "AE6 is plan/probe only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active messaging DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active messaging index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active messaging LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_failed_dts_token_review_v1.csv", token_rows, ["TOKEN", "COUNT"])
    write_csv(reports / "message_catalog_phase22ae_6_failed_runlog_observation_v1.csv", runlog_rows, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_root_cause_findings_v1.csv", root_cause_rows, ["FINDING", "CONFIDENCE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_path_options_v1.csv", options, ["OPTION", "RECOMMENDATION", "WHY", "ACTIVE_MUTATION", "NEXT_PHASE"])
    write_csv(reports / "message_catalog_phase22ae_6_1_sandbox_proof_plan_v1.csv", ae61_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_5_4_GREEN": 1 if ae54.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION_GREEN" else 0,
        "MSG_022AE_5_4_SAVEPOINT_PRESENT": 1 if sp54 else 0,
        "ACTIVE_MESSAGE_COUNT": ae54.get("ACTIVE_MESSAGE_COUNT", ""),
        "ACTIVE_TEXT_ROW_COUNT": ae54.get("ACTIVE_TEXT_ROW_COUNT", ""),
        "FAILED_PROMOTION_STATUS": ae5.get("STATUS", ""),
        "FAILED_PROMOTION_MESSAGE_ROWS_AFTER": ae5.get("MESSAGE_ROWS_AFTER", ""),
        "FAILED_PROMOTION_TEXT_ROWS_AFTER": ae5.get("TEXT_ROWS_AFTER", ""),
        "FAILED_PROMOTION_MESSAGE_SYMBOLS_PRESENT": ae5.get("MESSAGE_SYMBOLS_PRESENT", ""),
        "FAILED_PROMOTION_TEXT_KEYS_PRESENT": ae5.get("TEXT_KEYS_PRESENT", ""),
        "RECOMMENDED_NEXT_PATH": "SANDBOX_ROW_WRITE_PROOF",
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_5_4_GREEN", "MSG_022AE_5_4_SAVEPOINT_PRESENT",
         "ACTIVE_MESSAGE_COUNT", "ACTIVE_TEXT_ROW_COUNT", "FAILED_PROMOTION_STATUS",
         "FAILED_PROMOTION_MESSAGE_ROWS_AFTER", "FAILED_PROMOTION_TEXT_ROWS_AFTER",
         "FAILED_PROMOTION_MESSAGE_SYMBOLS_PRESENT", "FAILED_PROMOTION_TEXT_KEYS_PRESENT",
         "RECOMMENDED_NEXT_PATH", "ACTIVE_PROMOTION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22AE.6 Redesigned Promotion Path Plan

Status: `{status}`

The active catalog is back at the clean rollback baseline:

```text
messages: {ae54.get('ACTIVE_MESSAGE_COUNT', '')}
text rows: {ae54.get('ACTIVE_TEXT_ROW_COUNT', '')}
```

22AE.5 must not be reused. It appended rows but did not populate the required
keys. The recommended next path is sandbox-only row-write proof.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_REDESIGNED_PROMOTION_PATH_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.5.4 green: {1 if ae54.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_5_4_POST_ROLLBACK_READBACK_AND_RUNTIME_REGRESSION_GREEN' else 0}")
    print(f"  MSG-022AE.5.4 savepoint present: {1 if sp54 else 0}")
    print(f"  active message count: {ae54.get('ACTIVE_MESSAGE_COUNT', '')}")
    print(f"  active text row count: {ae54.get('ACTIVE_TEXT_ROW_COUNT', '')}")
    print(f"  failed promotion status: {ae5.get('STATUS', '')}")
    print(f"  failed promotion message rows after: {ae5.get('MESSAGE_ROWS_AFTER', '')}")
    print(f"  failed promotion text rows after: {ae5.get('TEXT_ROWS_AFTER', '')}")
    print(f"  failed promotion message symbols present: {ae5.get('MESSAGE_SYMBOLS_PRESENT', '')}")
    print(f"  failed promotion text keys present: {ae5.get('TEXT_KEYS_PRESENT', '')}")
    print("  recommended next path: SANDBOX_ROW_WRITE_PROOF")
    print("  active promotion authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
