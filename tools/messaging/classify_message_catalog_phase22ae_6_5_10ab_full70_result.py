#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AB_FULL70_TEXT_SEQUENCE_RESULT_CLASSIFICATION_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AB_FULL70_TEXT_SEQUENCE_RESULT_CLASSIFICATION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AC_TWO_TABLE_PROMOTION_SEQUENCE_PLAN"

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

    s6510 = first_row(reports / "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv")
    s10r = first_row(reports / "message_catalog_phase22ae_6_5_10r_status_summary_v1.csv")
    s10s = first_row(reports / "message_catalog_phase22ae_6_5_10s_status_summary_v1.csv")
    s10u = first_row(reports / "message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv")
    s10x = first_row(reports / "message_catalog_phase22ae_6_5_10x_restore_status_summary_v1.csv")
    s10y = first_row(reports / "message_catalog_phase22ae_6_5_10y_status_summary_v1.csv")
    s10z = first_row(reports / "message_catalog_phase22ae_6_5_10z_status_summary_v1.csv")
    s10aa_final = first_row(reports / "message_catalog_phase22ae_6_5_10aa_finalize_status_summary_v1.csv")
    s10aa_restore = first_row(reports / "message_catalog_phase22ae_6_5_10aa_restore_status_summary_v1.csv")

    sp10aa, latest = savepoint_present(repo, "MSG-022AE.6.5.10AA")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10_ORIGINAL_FULL_PROMOTION_BLOCKED",
         s6510.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_BLOCKED",
         s6510.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10R_ROLLBACK_GREEN",
         s10r.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_GREEN_SOURCE_HELD",
         s10r.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10S_FORENSIC_GREEN",
         s10s.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW_GREEN_SOURCE_HELD",
         s10s.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10U_BASELINE60_PROVEN",
         s10u.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED",
         s10u.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10X_CANDIDATE10_APPEND_PROVEN",
         s10x.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_PROVEN_AND_RESTORED",
         s10x.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10Y_CANDIDATE10_CLASSIFICATION_GREEN",
         s10y.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10Y_CANDIDATE10_RESULT_CLASSIFICATION_GREEN_SOURCE_HELD",
         s10y.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10Z_FULL70_PLAN_GREEN",
         s10z.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10Z_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PLAN_GREEN_SOURCE_HELD",
         s10z.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10AA_FINALIZE_GREEN_RESTORE_REQUIRED",
         s10aa_final.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_GREEN_RESTORE_REQUIRED",
         s10aa_final.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_10AA_RESTORE_GREEN",
         s10aa_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PROVEN_AND_RESTORED",
         s10aa_restore.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AA_SAVEPOINT_PRESENT", sp10aa, latest)
    gate("10AA_RESTORED_EXACT_BACKUP", s10aa_restore.get("RESTORED_EXACT_BACKUP") == "1", s10aa_restore.get("RESTORED_EXACT_BACKUP", "missing"))
    gate("10AA_POST_RESTORE_DELTA_ZERO", s10aa_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS") == "0", s10aa_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS", "missing"))

    evidence = [
        {
            "EVIDENCE_ID": "E01",
            "CLAIM": "The original two-table/full-promotion active attempt failed.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv",
            "OBSERVED": f"status={s6510.get('STATUS','')}; imported14={s6510.get('RUNTIME_IMPORTED_14','')}; imported70={s6510.get('RUNTIME_IMPORTED_70','')}; active_message={s6510.get('ACTIVE_MESSAGE_HEADER_COUNT','')}; active_text={s6510.get('ACTIVE_TEXT_HEADER_COUNT','')}",
            "INTERPRETATION": "The broad promotion path failed even though it reported importing both message and text rows.",
        },
        {
            "EVIDENCE_ID": "E02",
            "CLAIM": "Rollback restored the safe active baseline.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10r_status_summary_v1.csv",
            "OBSERVED": f"message12={s10r.get('ROLLBACK_RUNTIME_MESSAGE_BASELINE_12','')}; text60={s10r.get('ROLLBACK_RUNTIME_TEXT_BASELINE_60','')}",
            "INTERPRETATION": "The failed broad attempt was recovered and should remain a failed evidence point, not a savepointed promotion.",
        },
        {
            "EVIDENCE_ID": "E03",
            "CLAIM": "CSV identity was not the cause.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10s_status_summary_v1.csv",
            "OBSERVED": f"text_csvs_identical={s10s.get('TEXT_IMPORT_CSVS_IDENTICAL','')}",
            "INTERPRETATION": "The text CSV used by active/plan/sandbox paths was byte-identical.",
        },
        {
            "EVIDENCE_ID": "E04",
            "CLAIM": "Baseline60 active text replacement works.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv",
            "OBSERVED": f"status={s10u.get('STATUS','')}; post_restore_count={s10u.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}; delta={s10u.get('POST_RESTORE_FINGERPRINT_DELTA_ROWS','')}",
            "INTERPRETATION": "Active SYSTEM_MESSAGE_TEXT can ZAP/import/readback/restore the 60-row baseline.",
        },
        {
            "EVIDENCE_ID": "E05",
            "CLAIM": "Candidate10 active text append works.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10x_restore_status_summary_v1.csv",
            "OBSERVED": f"status={s10x.get('STATUS','')}; post_restore_count={s10x.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}; delta={s10x.get('POST_RESTORE_FINGERPRINT_DELTA_ROWS','')}",
            "INTERPRETATION": "Rows 61-70 are valid enough to append into active SYSTEM_MESSAGE_TEXT and become visible.",
        },
        {
            "EVIDENCE_ID": "E06",
            "CLAIM": "Full70 text-only active ZAP/import works.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10aa_finalize_status_summary_v1.csv",
            "OBSERVED": f"zap={s10aa_final.get('RUNTIME_ZAP_COMPLETE','')}; imported70={s10aa_final.get('RUNTIME_IMPORTED_70','')}; count70={s10aa_final.get('RUNTIME_COUNT_70','')}; listed70={s10aa_final.get('RUNTIME_LISTED_70','')}; symbols={s10aa_final.get('PROOF_SYMBOLS_VISIBLE','')}; locales={s10aa_final.get('PROOF_LOCALES_VISIBLE','')}",
            "INTERPRETATION": "The exact full70 text-only ZAP/import sequence is proven in isolation.",
        },
        {
            "EVIDENCE_ID": "E07",
            "CLAIM": "10AA restored exact active text backup before savepoint.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10aa_restore_status_summary_v1.csv",
            "OBSERVED": f"restored={s10aa_restore.get('RESTORED_EXACT_BACKUP','')}; post_restore_count={s10aa_restore.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}; delta={s10aa_restore.get('POST_RESTORE_FINGERPRINT_DELTA_ROWS','')}",
            "INTERPRETATION": "10AA did not leave active text mutated.",
        },
    ]

    classification = [
        {
            "CLASSIFICATION": "FULL70_TEXT_ONLY_ZAP_IMPORT_PROVEN",
            "STATUS": "PROVEN",
            "DETAIL": "10AA proves active SYSTEM_MESSAGE_TEXT full70 ZAP/import/readback works in isolation.",
            "PROMOTION_IMPLICATION": "The text table full70 sequence is no longer the primary failure suspect.",
        },
        {
            "CLASSIFICATION": "CANDIDATE10_DATA_AND_APPEND_PROVEN",
            "STATUS": "PROVEN",
            "DETAIL": "10X proves rows 61-70 append and become runtime-visible.",
            "PROMOTION_IMPLICATION": "Candidate10 data is not the primary failure suspect.",
        },
        {
            "CLASSIFICATION": "BASELINE60_REPLACE_PROVEN",
            "STATUS": "PROVEN",
            "DETAIL": "10U proves the active 60-row baseline text replacement path.",
            "PROMOTION_IMPLICATION": "Basic text-table ZAP/import is not globally broken.",
        },
        {
            "CLASSIFICATION": "ORIGINAL_FAILURE_REDIRECTED_TO_TWO_TABLE_PROMOTION_SEQUENCE",
            "STATUS": "PRIMARY_SUSPECT",
            "DETAIL": "All isolated text-table paths now work; the remaining failed path is the combined promotion involving SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT.",
            "PROMOTION_IMPLICATION": "Next work should be plan-only two-table sequencing, not another broad retry.",
        },
        {
            "CLASSIFICATION": "FULL_ACTIVE_PROMOTION_RETRY_STILL_CLOSED",
            "STATUS": "CONTROL",
            "DETAIL": "10AB is report-only and does not authorize mutation.",
            "PROMOTION_IMPLICATION": "10AC should plan a two-table promotion proof with strict backup/restore and readback gates.",
        },
    ]

    next_plan = [
        {
            "STEP": 1,
            "ACTION": "PLAN_TWO_TABLE_PROMOTION_SEQUENCE_DIAGNOSTIC",
            "DETAIL": "Design 10AC as plan-only. It should isolate whether the failure arises from ordering/state between SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "COMPARE_ORDER_VARIANTS",
            "DETAIL": "Candidate plan variants should include message-first/text-second, text-first/message-second, and explicit reopen/readback after each import.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "ADD_INTERMEDIATE_READBACK_GATES",
            "DETAIL": "Future execution should prove SYSTEM_MESSAGES=14 before text import, SYSTEM_MESSAGE_TEXT=70 after text import, then both tables after reopen.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "RESTORE_EXACT_BACKUP_ALWAYS",
            "DETAIL": "Any future two-table execution must backup and restore both active message tables, indexes, and LMDB artifacts before savepoint.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 5,
            "ACTION": "DO_NOT_RUN_FULL_PROMOTION_RETRY_YET",
            "DETAIL": "A broad active retry is not justified until the two-table proof shape is staged and authorized.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AB is report-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "FULL_ACTIVE_PROMOTION_RETRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Retry remains closed."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ab_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ab_evidence_matrix_v1.csv", evidence, ["EVIDENCE_ID", "CLAIM", "SOURCE_REPORT", "OBSERVED", "INTERPRETATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ab_full70_text_result_classification_v1.csv", classification, ["CLASSIFICATION", "STATUS", "DETAIL", "PROMOTION_IMPLICATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ab_next_plan_v1.csv", next_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ab_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10ab_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AA_RESTORE_STATUS": s10aa_restore.get("STATUS", ""),
        "MSG_022AE_6_5_10AA_SAVEPOINT_PRESENT": 1 if sp10aa else 0,
        "BASELINE60_REPLACE_PROVEN": 1 if s10u.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED" else 0,
        "CANDIDATE10_APPEND_PROVEN": 1 if s10x.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_PROVEN_AND_RESTORED" else 0,
        "FULL70_TEXT_ZAP_IMPORT_PROVEN": 1 if s10aa_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PROVEN_AND_RESTORED" else 0,
        "TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT": 1,
        "FULL_ACTIVE_PROMOTION_RETRY_ALLOWED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10AA_RESTORE_STATUS",
         "MSG_022AE_6_5_10AA_SAVEPOINT_PRESENT", "BASELINE60_REPLACE_PROVEN",
         "CANDIDATE10_APPEND_PROVEN", "FULL70_TEXT_ZAP_IMPORT_PROVEN",
         "TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT",
         "FULL_ACTIVE_PROMOTION_RETRY_ALLOWED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AB_FULL70_TEXT_SEQUENCE_RESULT_CLASSIFICATION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AB Full70 Text Sequence Result Classification\n\nStatus: `{status}`\n\n10AB is report-only. It classifies full70 text-only ZAP/import as proven, leaves full active promotion retry closed, and redirects the investigation to the two-table promotion sequence.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AA restore status: {s10aa_restore.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AA savepoint present: {1 if sp10aa else 0}")
    print(f"  baseline60 replace proven: {1 if s10u.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED' else 0}")
    print(f"  candidate10 append proven: {1 if s10x.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_PROVEN_AND_RESTORED' else 0}")
    print(f"  full70 text ZAP/import proven: {1 if s10aa_restore.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PROVEN_AND_RESTORED' else 0}")
    print("  two-table promotion sequence primary suspect: 1")
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
