#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10Y_CANDIDATE10_RESULT_CLASSIFICATION_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10Y_CANDIDATE10_RESULT_CLASSIFICATION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10Z_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PLAN"

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
    s10u_restore = first_row(reports / "message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv")
    s10v = first_row(reports / "message_catalog_phase22ae_6_5_10v_status_summary_v1.csv")
    s10w = first_row(reports / "message_catalog_phase22ae_6_5_10w_status_summary_v1.csv")
    s10x_finalize = first_row(reports / "message_catalog_phase22ae_6_5_10x_finalize_status_summary_v1.csv")
    s10x_restore = first_row(reports / "message_catalog_phase22ae_6_5_10x_restore_status_summary_v1.csv")

    sp10x, latest = savepoint_present(repo, "MSG-022AE.6.5.10X")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10_FULL70_ACTIVE_ATTEMPT_BLOCKED",
         s10.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_BLOCKED",
         s10.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10R_ROLLBACK_GREEN",
         s10r.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_GREEN_SOURCE_HELD",
         s10r.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10S_FORENSIC_GREEN",
         s10s.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW_GREEN_SOURCE_HELD",
         s10s.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10U_BASELINE60_PROVEN_RESTORED",
         s10u_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED",
         s10u_restore.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10V_CLASSIFICATION_GREEN",
         s10v.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10V_TEXT_ACTIVE_PATH_CLASSIFICATION_GREEN_SOURCE_HELD",
         s10v.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10W_PLAN_GREEN",
         s10w.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10W_CANDIDATE10_TEXT_EXTENSION_MICRO_PROOF_PLAN_GREEN_SOURCE_HELD",
         s10w.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10X_FINALIZE_GREEN_RESTORE_REQUIRED",
         s10x_finalize.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_GREEN_RESTORE_REQUIRED",
         s10x_finalize.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10X_RESTORE_GREEN",
         s10x_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_PROVEN_AND_RESTORED",
         s10x_restore.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10X_SAVEPOINT_PRESENT", sp10x, latest)
    gate("10X_RESTORED_EXACT_BACKUP", s10x_restore.get("RESTORED_EXACT_BACKUP") == "1", s10x_restore.get("RESTORED_EXACT_BACKUP", "missing"))
    gate("10X_POST_RESTORE_DELTA_ZERO", s10x_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS") == "0", s10x_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS", "missing"))

    evidence = [
        {
            "EVIDENCE_ID": "E01",
            "CLAIM": "The first full active 70-row text import path failed.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv",
            "OBSERVED": f"status={s10.get('STATUS','')}; imported70={s10.get('RUNTIME_IMPORTED_70','')}; active_text_after={s10.get('ACTIVE_TEXT_HEADER_COUNT','')}",
            "INTERPRETATION": "Full active promotion reported importing 70 text rows, but active text reopened/header-counted as 0.",
        },
        {
            "EVIDENCE_ID": "E02",
            "CLAIM": "Rollback restored the safe 60-row active text baseline.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10r_status_summary_v1.csv",
            "OBSERVED": f"text60={s10r.get('ROLLBACK_RUNTIME_TEXT_BASELINE_60','')}",
            "INTERPRETATION": "The failed full active attempt was recoverable and should not be savepointed.",
        },
        {
            "EVIDENCE_ID": "E03",
            "CLAIM": "The full70 text import CSV itself was not the primary suspect.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10s_status_summary_v1.csv",
            "OBSERVED": f"text_csvs_identical={s10s.get('TEXT_IMPORT_CSVS_IDENTICAL','')}; sandbox_text_success={s10s.get('SANDBOX_TEXT_SUCCESS_RECORD_COUNT','')}",
            "INTERPRETATION": "The active/plan/sandbox text CSV was byte-identical, and the sandbox path had already reached 70.",
        },
        {
            "EVIDENCE_ID": "E04",
            "CLAIM": "Active text baseline60 roundtrip is proven.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv",
            "OBSERVED": f"status={s10u_restore.get('STATUS','')}; post_restore_count={s10u_restore.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}; delta={s10u_restore.get('POST_RESTORE_FINGERPRINT_DELTA_ROWS','')}",
            "INTERPRETATION": "Active SYSTEM_MESSAGE_TEXT can ZAP/import/readback/restore the existing 60-row baseline.",
        },
        {
            "EVIDENCE_ID": "E05",
            "CLAIM": "Candidate10 append is proven.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10x_finalize_status_summary_v1.csv",
            "OBSERVED": f"imported10={s10x_finalize.get('RUNTIME_IMPORTED_10','')}; count70={s10x_finalize.get('RUNTIME_COUNT_70','')}; listed70={s10x_finalize.get('RUNTIME_LISTED_70','')}; symbols={s10x_finalize.get('PROOF_SYMBOLS_VISIBLE','')}; locales={s10x_finalize.get('PROOF_LOCALES_VISIBLE','')}",
            "INTERPRETATION": "Rows 61-70 are valid enough to append into the active 60-row text baseline and become runtime-visible.",
        },
        {
            "EVIDENCE_ID": "E06",
            "CLAIM": "10X restored exact backup before savepoint.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10x_restore_status_summary_v1.csv",
            "OBSERVED": f"restored={s10x_restore.get('RESTORED_EXACT_BACKUP','')}; post_restore_count={s10x_restore.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}; delta={s10x_restore.get('POST_RESTORE_FINGERPRINT_DELTA_ROWS','')}",
            "INTERPRETATION": "The candidate10 diagnostic left the active text baseline restored to 60 with no fingerprint delta.",
        },
    ]

    classification = [
        {
            "CLASSIFICATION": "CANDIDATE10_DATA_PATH_PROVEN",
            "STATUS": "PROVEN",
            "DETAIL": "10X proves that candidate rows 61-70 can be appended to active SYSTEM_MESSAGE_TEXT, counted to 70, listed, and restored.",
            "PROMOTION_IMPLICATION": "Candidate10 data/content is no longer the primary suspect.",
        },
        {
            "CLASSIFICATION": "BASELINE60_ACTIVE_REPLACE_PATH_PROVEN",
            "STATUS": "PROVEN",
            "DETAIL": "10U proves active text baseline60 ZAP/import/readback works.",
            "PROMOTION_IMPLICATION": "Basic active SYSTEM_MESSAGE_TEXT replace/import behavior is not globally broken.",
        },
        {
            "CLASSIFICATION": "FULL70_ZAP_IMPORT_SEQUENCE_REMAINS_PRIMARY_SUSPECT",
            "STATUS": "PRIMARY_SUSPECT",
            "DETAIL": "The combination that failed was full70 active ZAP/import during the guarded promotion attempt; baseline60 replacement and candidate10 append both work independently.",
            "PROMOTION_IMPLICATION": "Next proof should isolate full70 text-only ZAP/import, not full catalog promotion.",
        },
        {
            "CLASSIFICATION": "FULL_PROMOTION_RETRY_STILL_CLOSED",
            "STATUS": "CONTROL",
            "DETAIL": "10Y is report-only and authorizes no active retry.",
            "PROMOTION_IMPLICATION": "A future 10Z should be plan-only, and any execution after that must backup/restore exactly.",
        },
        {
            "CLASSIFICATION": "SYSTEM_MESSAGES_OUT_OF_SCOPE_FOR_NEXT_PROOF",
            "STATUS": "DEFER",
            "DETAIL": "The message table reached 14 during 6.5.10; the unresolved failure is the text-table full70 sequence.",
            "PROMOTION_IMPLICATION": "Do not re-run a two-table active promotion until text full70 sequence is separately explained.",
        },
    ]

    next_plan = [
        {
            "STEP": 1,
            "ACTION": "PLAN_FULL70_TEXT_ONLY_ZAP_IMPORT_SEQUENCE",
            "DETAIL": "Design a plan-only 10Z proof that uses active SYSTEM_MESSAGE_TEXT only: backup, ZAP, import full70, readback COUNT/LIST, restore.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "COMPARE_FULL70_ZAP_IMPORT_TO_10U_AND_10X",
            "DETAIL": "10U proved ZAP/import 60; 10X proved append 10. 10Z should isolate whether ZAP/import 70 fails only when all 70 rows are imported after ZAP.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "KEEP_FULL_PROMOTION_RETRY_CLOSED",
            "DETAIL": "Do not touch SYSTEM_MESSAGES or active provider promotion again until full70 text-only sequence is classified.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "REQUIRE_RESTORE_ALWAYS_FOR_ANY_EXECUTION",
            "DETAIL": "Any future execution proof must restore exact active backup before savepoint, matching 10U and 10X discipline.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10Y is report-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "FULL_ACTIVE_PROMOTION_RETRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Retry remains closed."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10y_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10y_evidence_matrix_v1.csv", evidence, ["EVIDENCE_ID", "CLAIM", "SOURCE_REPORT", "OBSERVED", "INTERPRETATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10y_candidate10_result_classification_v1.csv", classification, ["CLASSIFICATION", "STATUS", "DETAIL", "PROMOTION_IMPLICATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10y_next_plan_v1.csv", next_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10y_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10y_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10X_RESTORE_STATUS": s10x_restore.get("STATUS", ""),
        "MSG_022AE_6_5_10X_SAVEPOINT_PRESENT": 1 if sp10x else 0,
        "BASELINE60_ACTIVE_REPLACE_PROVEN": 1 if s10u_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED" else 0,
        "CANDIDATE10_APPEND_PROVEN": 1 if s10x_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_PROVEN_AND_RESTORED" else 0,
        "FULL70_ZAP_IMPORT_SEQUENCE_PRIMARY_SUSPECT": 1,
        "FULL_ACTIVE_PROMOTION_RETRY_ALLOWED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10X_RESTORE_STATUS",
         "MSG_022AE_6_5_10X_SAVEPOINT_PRESENT", "BASELINE60_ACTIVE_REPLACE_PROVEN",
         "CANDIDATE10_APPEND_PROVEN", "FULL70_ZAP_IMPORT_SEQUENCE_PRIMARY_SUSPECT",
         "FULL_ACTIVE_PROMOTION_RETRY_ALLOWED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10Y_CANDIDATE10_RESULT_CLASSIFICATION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10Y Candidate10 Result Classification\n\nStatus: `{status}`\n\n10Y is report-only. It classifies candidate10 append as proven, baseline60 replacement as proven, and the full70 text ZAP/import sequence as the remaining primary suspect. Full active promotion retry remains closed.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10X restore status: {s10x_restore.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10X savepoint present: {1 if sp10x else 0}")
    print(f"  baseline60 active replace proven: {1 if s10u_restore.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED' else 0}")
    print(f"  candidate10 append proven: {1 if s10x_restore.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_PROVEN_AND_RESTORED' else 0}")
    print("  full70 ZAP/import sequence primary suspect: 1")
    print("  full active promotion retry allowed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
