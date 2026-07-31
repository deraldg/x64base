#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AE_TWO_TABLE_SEQUENCE_RESULT_CLASSIFICATION_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AE_TWO_TABLE_SEQUENCE_RESULT_CLASSIFICATION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AF_ORIGINAL_PROMOTION_FAILURE_DELTA_REVIEW"

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
    s10ab = first_row(reports / "message_catalog_phase22ae_6_5_10ab_status_summary_v1.csv")
    s10ac = first_row(reports / "message_catalog_phase22ae_6_5_10ac_status_summary_v1.csv")
    s10ad_prepare = first_row(reports / "message_catalog_phase22ae_6_5_10ad_prepare_status_summary_v1.csv")
    s10ad_final = first_row(reports / "message_catalog_phase22ae_6_5_10ad_finalize_status_summary_v1.csv")
    s10ad_restore = first_row(reports / "message_catalog_phase22ae_6_5_10ad_restore_status_summary_v1.csv")

    sp10ad, latest = savepoint_present(repo, "MSG-022AE.6.5.10AD")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("ORIGINAL_6_5_10_ACTIVE_PROMOTION_BLOCKED",
         s6510.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_BLOCKED",
         s6510.get("STATUS", "missing"))
    gate("ORIGINAL_6_5_10_ROLLBACK_CLASSIFIED_GREEN",
         s10r.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_GREEN_SOURCE_HELD",
         s10r.get("STATUS", "missing"))
    gate("10AB_REDIRECTED_TO_TWO_TABLE_SEQUENCE",
         s10ab.get("TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT") == "1",
         s10ab.get("TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT", "missing"))
    gate("10AC_TWO_TABLE_PLAN_GREEN",
         s10ac.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AC_TWO_TABLE_PROMOTION_SEQUENCE_PLAN_GREEN_SOURCE_HELD",
         s10ac.get("STATUS", "missing"))
    gate("10AD_PREPARED_V1",
         s10ad_prepare.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1_PREPARED",
         s10ad_prepare.get("STATUS", "missing"))
    gate("10AD_FINALIZE_GREEN_RESTORE_REQUIRED",
         s10ad_final.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1_GREEN_RESTORE_REQUIRED",
         s10ad_final.get("STATUS", "missing"))
    gate("10AD_RESTORE_GREEN",
         s10ad_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1_PROVEN_AND_RESTORED",
         s10ad_restore.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AD_SAVEPOINT_PRESENT", sp10ad, latest)
    gate("10AD_RESTORED_EXACT_BACKUP", s10ad_restore.get("RESTORED_EXACT_BACKUP") == "1", s10ad_restore.get("RESTORED_EXACT_BACKUP", "missing"))
    gate("10AD_POST_RESTORE_DELTA_ZERO", s10ad_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS") == "0", s10ad_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS", "missing"))
    gate("10AD_FINAL_COUNTS_RESTORED_TO_BASELINE",
         s10ad_restore.get("POST_RESTORE_ACTIVE_MESSAGES_HEADER_COUNT") == "12" and s10ad_restore.get("POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT") == "60",
         f"messages={s10ad_restore.get('POST_RESTORE_ACTIVE_MESSAGES_HEADER_COUNT','')}; text={s10ad_restore.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}")

    evidence = [
        {
            "EVIDENCE_ID": "E01",
            "CLAIM": "The original 6.5.10 broad active promotion failed and was rolled back.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv; message_catalog_phase22ae_6_5_10r_status_summary_v1.csv",
            "OBSERVED": f"6.5.10={s6510.get('STATUS','')}; 10R={s10r.get('STATUS','')}",
            "INTERPRETATION": "The failed path remains real evidence, but it is now a historical failed package/run rather than the proven table operation.",
        },
        {
            "EVIDENCE_ID": "E02",
            "CLAIM": "Prior isolated text-table probes eliminated the text CSV and text-only import path.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10ab_status_summary_v1.csv",
            "OBSERVED": f"baseline60={s10ab.get('BASELINE60_REPLACE_PROVEN','')}; candidate10={s10ab.get('CANDIDATE10_APPEND_PROVEN','')}; full70_text={s10ab.get('FULL70_TEXT_ZAP_IMPORT_PROVEN','')}",
            "INTERPRETATION": "Text rows and text-only ZAP/import are not the remaining primary suspects.",
        },
        {
            "EVIDENCE_ID": "E03",
            "CLAIM": "The 10AD V1 two-table sequence was prepared from 10AC plan inputs.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10ad_prepare_status_summary_v1.csv",
            "OBSERVED": f"variant={s10ad_prepare.get('VARIANT_ID','')}; message14={s10ad_prepare.get('MESSAGE14_ROWS','')}; text70={s10ad_prepare.get('TEXT70_ROWS','')}",
            "INTERPRETATION": "10AD directly tested the message-first/text-second sequence that had been the remaining suspect.",
        },
        {
            "EVIDENCE_ID": "E04",
            "CLAIM": "10AD V1 succeeded at runtime with readback after each table.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10ad_finalize_status_summary_v1.csv",
            "OBSERVED": f"import14={s10ad_final.get('RUNTIME_IMPORTED_14','')}; msg_count14={s10ad_final.get('RUNTIME_MESSAGE_COUNT_14','')}; msg_list14={s10ad_final.get('RUNTIME_MESSAGE_LISTED_14','')}; import70={s10ad_final.get('RUNTIME_IMPORTED_70','')}; text_count70={s10ad_final.get('RUNTIME_TEXT_COUNT_70','')}; text_list70={s10ad_final.get('RUNTIME_TEXT_LISTED_70','')}",
            "INTERPRETATION": "The basic message-first/text-second active two-table operation is proven when executed with explicit readback gates.",
        },
        {
            "EVIDENCE_ID": "E05",
            "CLAIM": "10AD restored exact active backups before savepoint.",
            "SOURCE_REPORT": "message_catalog_phase22ae_6_5_10ad_restore_status_summary_v1.csv",
            "OBSERVED": f"restored={s10ad_restore.get('RESTORED_EXACT_BACKUP','')}; post_msg={s10ad_restore.get('POST_RESTORE_ACTIVE_MESSAGES_HEADER_COUNT','')}; post_text={s10ad_restore.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}; delta={s10ad_restore.get('POST_RESTORE_FINGERPRINT_DELTA_ROWS','')}",
            "INTERPRETATION": "The diagnostic did not leave active message catalogs mutated.",
        },
    ]

    classification = [
        {
            "CLASSIFICATION": "V1_MESSAGE_FIRST_TEXT_SECOND_SEQUENCE",
            "STATUS": "PROVEN",
            "DETAIL": "10AD proves SYSTEM_MESSAGES first, then SYSTEM_MESSAGE_TEXT, with readback after each table.",
            "IMPLICATION": "The broad two-table operation itself is no longer the primary failure suspect.",
        },
        {
            "CLASSIFICATION": "ORIGINAL_6_5_10_FAILURE",
            "STATUS": "UNRESOLVED_HISTORICAL_FAILURE",
            "DETAIL": "6.5.10 still failed, but the same data and same table order now succeed in the controlled 10AD V1 shape.",
            "IMPLICATION": "Focus shifts to package/script differences, wrapper details, missing intermediate readback, open-state timing, or run-environment differences.",
        },
        {
            "CLASSIFICATION": "DATA_OR_FIELD_MAP_CAUSE",
            "STATUS": "DOWNGRADED",
            "DETAIL": "Message14, text70, candidate10, baseline60, and full70 text-only paths have all been proven.",
            "IMPLICATION": "Do not keep chasing CSV identity or canonical field-map as the primary cause for this specific failure.",
        },
        {
            "CLASSIFICATION": "FINAL_ACTIVE_PROMOTION_RETRY",
            "STATUS": "NOT_YET_AUTHORIZED",
            "DETAIL": "10AE is report-only and does not authorize final active promotion.",
            "IMPLICATION": "Next step should compare failed 6.5.10 behavior against successful 10AD behavior before any final promotion package.",
        },
    ]

    next_plan = [
        {
            "STEP": 1,
            "ACTION": "ORIGINAL_PROMOTION_FAILURE_DELTA_REVIEW",
            "DETAIL": "Compare the failed 6.5.10 package/script/reports against the successful 10AD V1 package/script/reports.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "COMPARE_RUNTIME_SCRIPT_SHAPE",
            "DETAIL": "Identify whether 6.5.10 lacked intermediate readback/reopen gates, used different input pathing, touched both tables differently, or finalized against stale state.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "COMPARE_BACKUP_RESTORE_AND_FINGERPRINT_SCOPE",
            "DETAIL": "Ensure future final promotion copies 10AD's backup/restore and final readback discipline, not the failed 6.5.10 assumptions.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "PREPARE_FINAL_PROMOTION_ONLY_AFTER_DELTA_REVIEW",
            "DETAIL": "A final active promotion package should be authorized only after the delta review classifies exactly what changed between 6.5.10 and 10AD.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AE is report-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active index/LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "FINAL_ACTIVE_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Final promotion remains closed."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ae_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ae_evidence_matrix_v1.csv", evidence, ["EVIDENCE_ID", "CLAIM", "SOURCE_REPORT", "OBSERVED", "INTERPRETATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ae_two_table_result_classification_v1.csv", classification, ["CLASSIFICATION", "STATUS", "DETAIL", "IMPLICATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ae_next_plan_v1.csv", next_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ae_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10ae_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AD_RESTORE_STATUS": s10ad_restore.get("STATUS", ""),
        "MSG_022AE_6_5_10AD_SAVEPOINT_PRESENT": 1 if sp10ad else 0,
        "V1_MESSAGE_FIRST_TEXT_SECOND_PROVEN": 1 if s10ad_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1_PROVEN_AND_RESTORED" else 0,
        "ORIGINAL_6_5_10_FAILURE_REMAINS_REVIEW_ITEM": 1,
        "PRIMARY_SUSPECT_NOW": "FAILED_6_5_10_PACKAGE_OR_WRAPPER_DELTA",
        "FINAL_ACTIVE_PROMOTION_RETRY_ALLOWED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10AD_RESTORE_STATUS",
         "MSG_022AE_6_5_10AD_SAVEPOINT_PRESENT", "V1_MESSAGE_FIRST_TEXT_SECOND_PROVEN",
         "ORIGINAL_6_5_10_FAILURE_REMAINS_REVIEW_ITEM", "PRIMARY_SUSPECT_NOW",
         "FINAL_ACTIVE_PROMOTION_RETRY_ALLOWED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AE_TWO_TABLE_SEQUENCE_RESULT_CLASSIFICATION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AE Two-Table Sequence Result Classification\n\nStatus: `{status}`\n\n10AE is report-only. It records 10AD V1 as proven and redirects the remaining review to the delta between failed 6.5.10 and successful 10AD.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AD restore status: {s10ad_restore.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AD savepoint present: {1 if sp10ad else 0}")
    print(f"  V1 message-first/text-second proven: {1 if s10ad_restore.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1_PROVEN_AND_RESTORED' else 0}")
    print("  original 6.5.10 failure remains review item: 1")
    print("  primary suspect now: FAILED_6_5_10_PACKAGE_OR_WRAPPER_DELTA")
    print("  final active promotion retry allowed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
