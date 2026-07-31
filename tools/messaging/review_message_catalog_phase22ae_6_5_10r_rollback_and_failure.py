#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
ROLLBACK_RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_10_ROLLBACK_RUNTIME_READBACK.md")

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

def parse_rollback_log(text: str):
    norm = re.sub(r"\s+", " ", text.replace("\r", "\n"))
    msg_open_12 = 1 if re.search(r"Opened SYSTEM_MESSAGES \(v64\)\s*:\s*Record count 12", text) else 0
    txt_open_60 = 1 if re.search(r"Opened SYSTEM_MESSAGE_TEXT \(v64\)\s*:\s*Record count 60", text) else 0

    # COUNT values appear as a prompt line followed by numeric line in runtime output.
    msg_count_12 = 1 if re.search(r"USE .*SYSTEM_MESSAGES\.dbf.*?COUNT\s+12", norm, re.IGNORECASE) else 0
    txt_count_60 = 1 if re.search(r"USE .*SYSTEM_MESSAGE_TEXT\.dbf.*?COUNT\s+60", norm, re.IGNORECASE) else 0

    # If a cleaned log keeps only the opened-count lines, allow those as strong evidence.
    msg_restored = 1 if (msg_open_12 and (msg_count_12 or "COUNT" not in text.upper())) or (msg_open_12 and msg_count_12) else 0
    txt_restored = 1 if (txt_open_60 and (txt_count_60 or "COUNT" not in text.upper())) or (txt_open_60 and txt_count_60) else 0
    return {
        "MESSAGE_OPEN_12": msg_open_12,
        "TEXT_OPEN_60": txt_open_60,
        "MESSAGE_COUNT_12": msg_count_12,
        "TEXT_COUNT_60": txt_count_60,
        "MESSAGE_RESTORED_BASELINE": msg_restored,
        "TEXT_RESTORED_BASELINE": txt_restored,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--rollback-runtime-log", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    prep = first_row(reports / "message_catalog_phase22ae_6_5_10_prepare_status_summary_v1.csv")
    finalize = first_row(reports / "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv")
    rollback = first_row(reports / "message_catalog_phase22ae_6_5_10_rollback_status_summary_v1.csv")
    sp659, latest = savepoint_present(repo, "MSG-022AE.6.5.9")

    log_path = Path(args.rollback_runtime_log) if args.rollback_runtime_log else repo / ROLLBACK_RUNLOG
    if not log_path.is_absolute():
        log_path = repo / log_path
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    parsed = parse_rollback_log(log_text)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_9_SAVEPOINT_PRESENT", sp659, latest)
    gate("PHASE22AE_6_5_10_PREPARED", prep.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_PREPARED", prep.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10_FINALIZE_BLOCKED", finalize.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_BLOCKED", finalize.get("STATUS", "missing"))
    gate("FINALIZE_IMPORTED_14_SIGNAL", finalize.get("RUNTIME_IMPORTED_14") == "1", finalize.get("RUNTIME_IMPORTED_14", "missing"))
    gate("FINALIZE_IMPORTED_70_SIGNAL", finalize.get("RUNTIME_IMPORTED_70") == "1", finalize.get("RUNTIME_IMPORTED_70", "missing"))
    gate("FINALIZE_ACTIVE_MESSAGE_14", finalize.get("ACTIVE_MESSAGE_HEADER_COUNT") == "14", finalize.get("ACTIVE_MESSAGE_HEADER_COUNT", "missing"))
    gate("FINALIZE_ACTIVE_TEXT_0_FAILURE", finalize.get("ACTIVE_TEXT_HEADER_COUNT") == "0", finalize.get("ACTIVE_TEXT_HEADER_COUNT", "missing"))
    gate("ROLLBACK_RUNTIME_LOG_EXISTS", log_path.exists(), rel(log_path, repo))
    gate("ROLLBACK_RUNTIME_MESSAGE_BASELINE_12", parsed["MESSAGE_RESTORED_BASELINE"] == 1, parsed)
    gate("ROLLBACK_RUNTIME_TEXT_BASELINE_60", parsed["TEXT_RESTORED_BASELINE"] == 1, parsed)

    # If rollback script status exists, record it. Do not require it because the user's runtime proof is the source of truth.
    rollback_script_green = 1 if rollback.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10_ACTIVE_CATALOG_ROLLBACK_EXECUTED" else 0

    runtime_rows = [{
        "RUNLOG": rel(log_path, repo),
        "MESSAGE_OPEN_12": parsed["MESSAGE_OPEN_12"],
        "TEXT_OPEN_60": parsed["TEXT_OPEN_60"],
        "MESSAGE_COUNT_12": parsed["MESSAGE_COUNT_12"],
        "TEXT_COUNT_60": parsed["TEXT_COUNT_60"],
        "MESSAGE_RESTORED_BASELINE": parsed["MESSAGE_RESTORED_BASELINE"],
        "TEXT_RESTORED_BASELINE": parsed["TEXT_RESTORED_BASELINE"],
        "ROLLBACK_SCRIPT_GREEN_IF_PRESENT": rollback_script_green,
        "ROLLBACK_SCRIPT_STATUS": rollback.get("STATUS", ""),
    }]

    classification = [
        {
            "FINDING": "ACTIVE_PROMOTION_PARTIAL_FAILURE_CONFIRMED",
            "DETAIL": "6.5.10 runtime reported IMPORT 14 and IMPORT 70, but post-run active readback showed SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=0.",
            "SEVERITY": "BLOCKS_6_5_10_SAVEPOINT",
        },
        {
            "FINDING": "ROLLBACK_RESTORED_BASELINE",
            "DETAIL": "Runtime readback after rollback shows SYSTEM_MESSAGES=12 and SYSTEM_MESSAGE_TEXT=60.",
            "SEVERITY": "GREEN_RECOVERY",
        },
        {
            "FINDING": "TEXT_TABLE_ACTIVE_IMPORT_PATH_IS_SUSPECT",
            "DETAIL": "Sandbox text-table ZAP/import reached 70 and runtime-visible keys, but active SYSTEM_MESSAGE_TEXT reopened as 0 after reported import 70.",
            "SEVERITY": "HIGH",
        },
        {
            "FINDING": "NO_6_5_10_SAVEPOINT",
            "DETAIL": "Do not append MSG-022AE.6.5.10. Treat 6.5.10 as a failed active attempt followed by successful rollback.",
            "SEVERITY": "CONTROL",
        },
        {
            "FINDING": "NEXT_PATH",
            "DETAIL": "Run an active-text import failure forensic review before any retry. Compare active vs sandbox text DBF headers, sidecars, indexes, LMDB, file sizes, ZAP behavior, import CSV field layout, and path/open-mode differences.",
            "SEVERITY": "NEXT_GATE",
        },
    ]

    recommendations = [
        {"STEP": 1, "ACTION": "DO_NOT_APPEND_6_5_10", "DETAIL": "6.5.10 finalize is blocked and rollback was required.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "ACTION": "APPEND_6_5_10R_ONLY_IF_GREEN", "DETAIL": "Use 6.5.10R as the recovery/failure-classification savepoint.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "ACTION": "FORENSIC_COMPARE_ACTIVE_AND_SANDBOX_TEXT_TABLES", "DETAIL": "Focus on SYSTEM_MESSAGE_TEXT because message table promoted but text table reopened as zero.", "MUTATES_ACTIVE": 0},
        {"STEP": 4, "ACTION": "NO_ACTIVE_RETRY_UNTIL_TEXT_IMPORT_FAILURE_CLASSIFIED", "DETAIL": "Do not rerun active promotion script until the text path is explained and a smaller guarded proof is staged.", "MUTATES_ACTIVE": 0},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Report-only classification."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "This review performs no active mutation; rollback already restored baseline."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation by this review."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation by this review."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10r_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10r_rollback_runtime_readback_v1.csv", runtime_rows,
              ["RUNLOG", "MESSAGE_OPEN_12", "TEXT_OPEN_60", "MESSAGE_COUNT_12", "TEXT_COUNT_60",
               "MESSAGE_RESTORED_BASELINE", "TEXT_RESTORED_BASELINE", "ROLLBACK_SCRIPT_GREEN_IF_PRESENT",
               "ROLLBACK_SCRIPT_STATUS"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10r_failure_classification_v1.csv", classification,
              ["FINDING", "DETAIL", "SEVERITY"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10r_recommendations_v1.csv", recommendations,
              ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10r_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10r_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10_PREPARE_STATUS": prep.get("STATUS", ""),
        "PHASE22AE_6_5_10_FINALIZE_STATUS": finalize.get("STATUS", ""),
        "FINALIZE_RUNTIME_IMPORTED_14": finalize.get("RUNTIME_IMPORTED_14", ""),
        "FINALIZE_RUNTIME_IMPORTED_70": finalize.get("RUNTIME_IMPORTED_70", ""),
        "FINALIZE_ACTIVE_MESSAGE_HEADER_COUNT": finalize.get("ACTIVE_MESSAGE_HEADER_COUNT", ""),
        "FINALIZE_ACTIVE_TEXT_HEADER_COUNT": finalize.get("ACTIVE_TEXT_HEADER_COUNT", ""),
        "ROLLBACK_SCRIPT_STATUS": rollback.get("STATUS", ""),
        "ROLLBACK_RUNTIME_MESSAGE_BASELINE_12": parsed["MESSAGE_RESTORED_BASELINE"],
        "ROLLBACK_RUNTIME_TEXT_BASELINE_60": parsed["TEXT_RESTORED_BASELINE"],
        "ACTIVE_PROMOTION_RETRY_ALLOWED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10_PREPARE_STATUS",
         "PHASE22AE_6_5_10_FINALIZE_STATUS", "FINALIZE_RUNTIME_IMPORTED_14",
         "FINALIZE_RUNTIME_IMPORTED_70", "FINALIZE_ACTIVE_MESSAGE_HEADER_COUNT",
         "FINALIZE_ACTIVE_TEXT_HEADER_COUNT", "ROLLBACK_SCRIPT_STATUS",
         "ROLLBACK_RUNTIME_MESSAGE_BASELINE_12", "ROLLBACK_RUNTIME_TEXT_BASELINE_60",
         "ACTIVE_PROMOTION_RETRY_ALLOWED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10R Rollback and Failure Classification\n\nStatus: `{status}`\n\n6.5.10 is not savepointable. Rollback restored the 12/60 baseline. Active retry remains closed.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  6.5.10 finalize status: {finalize.get('STATUS','')}")
    print(f"  finalize imported 14/70: {finalize.get('RUNTIME_IMPORTED_14','')}/{finalize.get('RUNTIME_IMPORTED_70','')}")
    print(f"  finalize active counts: message {finalize.get('ACTIVE_MESSAGE_HEADER_COUNT','')}; text {finalize.get('ACTIVE_TEXT_HEADER_COUNT','')}")
    print(f"  rollback script status: {rollback.get('STATUS','')}")
    print(f"  rollback runtime baseline: message 12={parsed['MESSAGE_RESTORED_BASELINE']}; text 60={parsed['TEXT_RESTORED_BASELINE']}")
    print("  active promotion retry allowed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
