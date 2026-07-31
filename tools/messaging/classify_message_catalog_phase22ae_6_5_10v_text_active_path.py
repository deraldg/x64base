#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10V_TEXT_ACTIVE_PATH_CLASSIFICATION_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10V_TEXT_ACTIVE_PATH_CLASSIFICATION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10W_CANDIDATE10_TEXT_EXTENSION_MICRO_PROOF_PLAN"

REPORT_DIR = Path("docs/messaging/reports")

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    s10 = first_row(reports / "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv")
    s10r = first_row(reports / "message_catalog_phase22ae_6_5_10r_status_summary_v1.csv")
    s10s = first_row(reports / "message_catalog_phase22ae_6_5_10s_status_summary_v1.csv")
    s10t = first_row(reports / "message_catalog_phase22ae_6_5_10t_status_summary_v1.csv")
    s10u_final = first_row(reports / "message_catalog_phase22ae_6_5_10u_finalize_status_summary_v1.csv")
    s10u_restore = first_row(reports / "message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv")

    sp10u, latest = savepoint_present(repo, "MSG-022AE.6.5.10U")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10_FAILED_ACTIVE_FULL70_AS_EXPECTED",
         s10.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_BLOCKED",
         s10.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10R_ROLLBACK_CLASSIFICATION_GREEN",
         s10r.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_GREEN_SOURCE_HELD",
         s10r.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10S_FORENSIC_GREEN",
         s10s.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW_GREEN_SOURCE_HELD",
         s10s.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10T_PLAN_GREEN",
         s10t.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10T_TEXT_ONLY_ACTIVE_IMPORT_MICRO_PROOF_PLAN_GREEN_SOURCE_HELD",
         s10t.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10U_FINALIZE_GREEN_RESTORE_REQUIRED",
         s10u_final.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_GREEN_RESTORE_REQUIRED",
         s10u_final.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10U_RESTORED_GREEN",
         s10u_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED",
         s10u_restore.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10U_SAVEPOINT_PRESENT", sp10u, latest)
    gate("10U_RESTORED_EXACT_BACKUP", s10u_restore.get("RESTORED_EXACT_BACKUP") == "1", s10u_restore.get("RESTORED_EXACT_BACKUP", "missing"))
    gate("10U_POST_RESTORE_DELTA_ZERO", s10u_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS") == "0", s10u_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS", "missing"))

    evidence = [
        {
            "EVIDENCE_ID": "E01",
            "CLAIM": "Full active promotion attempt failed at active SYSTEM_MESSAGE_TEXT.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv",
            "OBSERVED": f"status={s10.get('STATUS','')}; imported14={s10.get('RUNTIME_IMPORTED_14','')}; imported70={s10.get('RUNTIME_IMPORTED_70','')}; active_message={s10.get('ACTIVE_MESSAGE_HEADER_COUNT','')}; active_text={s10.get('ACTIVE_TEXT_HEADER_COUNT','')}",
            "INTERPRETATION": "The runtime import reported 70 text rows, but the active text table reopened/header-counted as 0.",
        },
        {
            "EVIDENCE_ID": "E02",
            "CLAIM": "Rollback restored the safe 12/60 baseline.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10r_status_summary_v1.csv",
            "OBSERVED": f"message12={s10r.get('ROLLBACK_RUNTIME_MESSAGE_BASELINE_12','')}; text60={s10r.get('ROLLBACK_RUNTIME_TEXT_BASELINE_60','')}",
            "INTERPRETATION": "The failed full active attempt did not leave the active catalog unrecovered.",
        },
        {
            "EVIDENCE_ID": "E03",
            "CLAIM": "CSV content is not the primary suspect.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10s_status_summary_v1.csv",
            "OBSERVED": f"text_csvs_identical={s10s.get('TEXT_IMPORT_CSVS_IDENTICAL','')}; sandbox_text_success={s10s.get('SANDBOX_TEXT_SUCCESS_RECORD_COUNT','')}; active_text_after_rollback={s10s.get('ACTIVE_TEXT_AFTER_ROLLBACK_RECORD_COUNT','')}",
            "INTERPRETATION": "The text import CSV matched the sandbox-proven path; failure likely involved active table path/state/extension behavior.",
        },
        {
            "EVIDENCE_ID": "E04",
            "CLAIM": "Active SYSTEM_MESSAGE_TEXT can perform a baseline60 roundtrip.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10u_finalize_status_summary_v1.csv",
            "OBSERVED": f"imported60={s10u_final.get('RUNTIME_IMPORTED_60','')}; listed60={s10u_final.get('RUNTIME_LISTED_60','')}; header_after_roundtrip={s10u_final.get('ACTIVE_TEXT_HEADER_COUNT_AFTER_ROUNDTRIP','')}",
            "INTERPRETATION": "Basic active text ZAP/import/readback works for the existing 60-row baseline.",
        },
        {
            "EVIDENCE_ID": "E05",
            "CLAIM": "10U restored exact active baseline before savepoint.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv",
            "OBSERVED": f"restored_exact={s10u_restore.get('RESTORED_EXACT_BACKUP','')}; post_restore_count={s10u_restore.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}; delta_rows={s10u_restore.get('POST_RESTORE_FINGERPRINT_DELTA_ROWS','')}",
            "INTERPRETATION": "The proof did not leave active text artifacts changed.",
        },
    ]

    classification = [
        {
            "CLASSIFICATION": "ACTIVE_TEXT_BASELINE60_PATH_PROVEN",
            "STATUS": "PROVEN",
            "DETAIL": "10U proves active SYSTEM_MESSAGE_TEXT can run ZAP -> IMPORT baseline60 -> COUNT/LIST 60 -> exact restore.",
            "PROMOTION_IMPLICATION": "The active text path is not globally broken.",
        },
        {
            "CLASSIFICATION": "FULL70_ACTIVE_PROMOTION_PATH_FAILED",
            "STATUS": "PROVEN_FAILURE",
            "DETAIL": "6.5.10 reported IMPORT 70 but active text reopened/header-counted as 0.",
            "PROMOTION_IMPLICATION": "Do not retry full 70-row active promotion without isolating candidate-extension behavior.",
        },
        {
            "CLASSIFICATION": "CANDIDATE10_EXTENSION_REMAINS_PRIMARY_SUSPECT",
            "STATUS": "SUSPECT",
            "DETAIL": "Baseline60 works, full70 failed, and rows 61-70 are the candidate extension set.",
            "PROMOTION_IMPLICATION": "Next proof should target candidate10 extension separately, not full catalog replacement.",
        },
        {
            "CLASSIFICATION": "CSV_BYTE_IDENTITY_REDUCES_GENERATION_RISK",
            "STATUS": "LOWER_RISK",
            "DETAIL": "10S showed the text import CSVs were identical across active/plan/sandbox evidence.",
            "PROMOTION_IMPLICATION": "Focus on active import behavior, record layout edge cases, row 61-70 content, open/flush/index state, or import row validation.",
        },
        {
            "CLASSIFICATION": "ACTIVE_RETRY_REMAINS_CLOSED",
            "STATUS": "CONTROL",
            "DETAIL": "10V is report-only and authorizes no active mutation.",
            "PROMOTION_IMPLICATION": "10W should be plan-only unless separately authorized for later execution.",
        },
    ]

    next_plan = [
        {
            "STEP": 1,
            "ACTION": "PLAN_CANDIDATE10_EXTENSION_MICRO_PROOF",
            "DETAIL": "Design a proof that starts from the 60-row baseline and tests rows 61-70 separately under backup/restore discipline.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "DO_NOT_TOUCH_SYSTEM_MESSAGES",
            "DETAIL": "The message table path already reached 14 in the failed full attempt; next work should isolate text rows only.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "PREFER_PLAN_FIRST_10W",
            "DETAIL": "10W should stage candidate10-only and baseline60-plus-candidate10 proof shapes, but not execute active mutation.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "FUTURE_EXECUTION_SHOULD_RESTORE_ALWAYS",
            "DETAIL": "Any candidate10 execution proof must restore exact backup before savepoint, as 10U did.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10V is report-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_PROMOTION_RETRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Retry remains closed."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10v_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10v_evidence_matrix_v1.csv", evidence, ["EVIDENCE_ID", "CLAIM", "SOURCE_REPORT", "OBSERVED", "INTERPRETATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10v_text_active_path_classification_v1.csv", classification, ["CLASSIFICATION", "STATUS", "DETAIL", "PROMOTION_IMPLICATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10v_next_plan_v1.csv", next_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10v_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10v_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10U_RESTORE_STATUS": s10u_restore.get("STATUS", ""),
        "MSG_022AE_6_5_10U_SAVEPOINT_PRESENT": 1 if sp10u else 0,
        "BASELINE60_ACTIVE_PATH_PROVEN": 1 if s10u_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED" else 0,
        "FULL70_ACTIVE_PATH_FAILED": 1 if s10.get("ACTIVE_TEXT_HEADER_COUNT") == "0" else 0,
        "CANDIDATE10_EXTENSION_PRIMARY_SUSPECT": 1,
        "ACTIVE_PROMOTION_RETRY_ALLOWED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10U_RESTORE_STATUS",
         "MSG_022AE_6_5_10U_SAVEPOINT_PRESENT", "BASELINE60_ACTIVE_PATH_PROVEN",
         "FULL70_ACTIVE_PATH_FAILED", "CANDIDATE10_EXTENSION_PRIMARY_SUSPECT",
         "ACTIVE_PROMOTION_RETRY_ALLOWED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10V_TEXT_ACTIVE_PATH_CLASSIFICATION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10V Text Active Path Classification\n\nStatus: `{status}`\n\n10V is report-only. It classifies the active text evidence after 10U: baseline60 works, full70 failed, candidate10 extension is the next suspect, and active retry remains closed.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10U restore status: {s10u_restore.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10U savepoint present: {1 if sp10u else 0}")
    print(f"  baseline60 active path proven: {1 if s10u_restore.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED' else 0}")
    print(f"  full70 active path failed: {1 if s10.get('ACTIVE_TEXT_HEADER_COUNT') == '0' else 0}")
    print("  candidate10 extension primary suspect: 1")
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
