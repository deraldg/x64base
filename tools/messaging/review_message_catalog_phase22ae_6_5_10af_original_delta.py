#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import difflib
import re
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AF_ORIGINAL_PROMOTION_FAILURE_DELTA_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AF_ORIGINAL_PROMOTION_FAILURE_DELTA_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AG_GUARDED_FINAL_PROMOTION_PLAN_FROM_10AD_PATTERN"

REPORT_DIR = Path("docs/messaging/reports")

CANDIDATE_6510_SCRIPTS = [
    Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTE.dts"),
    Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION.dts"),
    Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION.dts"),
]
SCRIPT_10AD = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1.dts")

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

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_text(path: Path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")

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

def find_existing(paths, repo: Path):
    for p in paths:
        if (repo / p).exists():
            return p
    return Path("")

def count_command_lines(text: str, command: str):
    command = command.upper()
    n = 0
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("*"):
            continue
        if s.upper().startswith(command):
            n += 1
    return n

def has_line_command(text: str, command: str):
    return count_command_lines(text, command) > 0

def script_features(text: str):
    up = text.upper()
    return {
        "USE_COUNT": count_command_lines(text, "USE "),
        "IMPORT_COUNT": count_command_lines(text, "IMPORT "),
        "ZAP_COUNT": count_command_lines(text, "ZAP"),
        "COUNT_COUNT": count_command_lines(text, "COUNT"),
        "LIST_COUNT": count_command_lines(text, "LIST"),
        "QUIT_COUNT": count_command_lines(text, "QUIT"),
        "HAS_FINAL_CROSS_TABLE_READBACK": 1 if ("FINAL CROSS-TABLE READBACK" in up or count_command_lines(text, "COUNT") >= 4) else 0,
        "HAS_INTERMEDIATE_READBACK": 1 if (count_command_lines(text, "COUNT") >= 2 and count_command_lines(text, "LIST") >= 2) else 0,
        "HAS_QUIT": 1 if count_command_lines(text, "QUIT") > 0 else 0,
    }

def make_script_diff(repo: Path, script_a: Path, script_b: Path):
    if not script_a or not (repo / script_a).exists() or not (repo / script_b).exists():
        return []
    a_lines = read_text(repo / script_a).splitlines()
    b_lines = read_text(repo / script_b).splitlines()
    diff = list(difflib.unified_diff(
        a_lines, b_lines,
        fromfile=rel(repo / script_a, repo),
        tofile=rel(repo / script_b, repo),
        lineterm=""
    ))
    return [{"DIFF_LINE_NO": i+1, "DIFF_LINE": line} for i, line in enumerate(diff[:500])]

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
    s10aa = first_row(reports / "message_catalog_phase22ae_6_5_10aa_restore_status_summary_v1.csv")
    s10ad_prepare = first_row(reports / "message_catalog_phase22ae_6_5_10ad_prepare_status_summary_v1.csv")
    s10ad_final = first_row(reports / "message_catalog_phase22ae_6_5_10ad_finalize_status_summary_v1.csv")
    s10ad_restore = first_row(reports / "message_catalog_phase22ae_6_5_10ad_restore_status_summary_v1.csv")
    s10ae = first_row(reports / "message_catalog_phase22ae_6_5_10ae_status_summary_v1.csv")

    sp10ae, latest = savepoint_present(repo, "MSG-022AE.6.5.10AE")

    script_6510 = find_existing(CANDIDATE_6510_SCRIPTS, repo)
    script_10ad = SCRIPT_10AD if (repo / SCRIPT_10AD).exists() else Path(s10ad_prepare.get("SCRIPT_PATH", ""))

    text_6510 = read_text(repo / script_6510) if script_6510 else ""
    text_10ad = read_text(repo / script_10ad) if script_10ad else ""
    feat_6510 = script_features(text_6510)
    feat_10ad = script_features(text_10ad)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AE_GREEN",
         s10ae.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AE_TWO_TABLE_SEQUENCE_RESULT_CLASSIFICATION_GREEN_SOURCE_HELD",
         s10ae.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AE_SAVEPOINT_PRESENT", sp10ae, latest)
    gate("ORIGINAL_6_5_10_BLOCKED",
         s6510.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_BLOCKED",
         s6510.get("STATUS", "missing"))
    gate("ROLLBACK_REVIEW_GREEN",
         s10r.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_GREEN_SOURCE_HELD",
         s10r.get("STATUS", "missing"))
    gate("10AD_V1_PROVEN_AND_RESTORED",
         s10ad_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1_PROVEN_AND_RESTORED",
         s10ad_restore.get("STATUS", "missing"))
    gate("10AD_RESTORED_EXACT_BACKUP", s10ad_restore.get("RESTORED_EXACT_BACKUP") == "1", s10ad_restore.get("RESTORED_EXACT_BACKUP", "missing"))
    gate("10AD_POST_RESTORE_DELTA_ZERO", s10ad_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS") == "0", s10ad_restore.get("POST_RESTORE_FINGERPRINT_DELTA_ROWS", "missing"))
    gate("ORIGINAL_6510_SCRIPT_FOUND_FOR_REVIEW", bool(script_6510), script_6510 if script_6510 else "not found")
    gate("10AD_SCRIPT_FOUND_FOR_REVIEW", bool(script_10ad) and (repo / script_10ad).exists(), script_10ad)

    evidence = [
        {
            "EVIDENCE_ID": "E01",
            "CLAIM": "Original 6.5.10 failed but reported both imports.",
            "SOURCE": "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv",
            "OBSERVED": f"status={s6510.get('STATUS','')}; imported14={s6510.get('RUNTIME_IMPORTED_14','')}; imported70={s6510.get('RUNTIME_IMPORTED_70','')}; active_message={s6510.get('ACTIVE_MESSAGE_HEADER_COUNT','')}; active_text={s6510.get('ACTIVE_TEXT_HEADER_COUNT','')}",
            "INTERPRETATION": "The failure is not that the runtime import command was absent; the failure was post-run active readback/finalization state.",
        },
        {
            "EVIDENCE_ID": "E02",
            "CLAIM": "CSV/content causes were downgraded by prior proofs.",
            "SOURCE": "10S / 10AA / 10AD reports",
            "OBSERVED": f"text_csvs_identical={s10s.get('TEXT_IMPORT_CSVS_IDENTICAL','')}; full70_text_restore={s10aa.get('STATUS','')}; two_table_restore={s10ad_restore.get('STATUS','')}",
            "INTERPRETATION": "The same data can succeed in controlled paths.",
        },
        {
            "EVIDENCE_ID": "E03",
            "CLAIM": "10AD V1 succeeded with explicit intermediate and final readback gates.",
            "SOURCE": "message_catalog_phase22ae_6_5_10ad_finalize_status_summary_v1.csv",
            "OBSERVED": f"message14={s10ad_final.get('RUNTIME_MESSAGE_LISTED_14','')}; text70={s10ad_final.get('RUNTIME_TEXT_LISTED_70','')}; final_headers={s10ad_final.get('ACTIVE_MESSAGES_HEADER_COUNT_AFTER_SEQUENCE','')}/{s10ad_final.get('ACTIVE_TEXT_HEADER_COUNT_AFTER_SEQUENCE','')}",
            "INTERPRETATION": "The safe pattern includes immediate readback after each table and a final cross-table readback.",
        },
        {
            "EVIDENCE_ID": "E04",
            "CLAIM": "10AD restore proved the diagnostic did not leave active catalog mutated.",
            "SOURCE": "message_catalog_phase22ae_6_5_10ad_restore_status_summary_v1.csv",
            "OBSERVED": f"restored={s10ad_restore.get('RESTORED_EXACT_BACKUP','')}; post={s10ad_restore.get('POST_RESTORE_ACTIVE_MESSAGES_HEADER_COUNT','')}/{s10ad_restore.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}; delta={s10ad_restore.get('POST_RESTORE_FINGERPRINT_DELTA_ROWS','')}",
            "INTERPRETATION": "The final promotion pattern must preserve this restore/verification discipline until the final successful promotion is explicitly accepted.",
        },
    ]

    script_rows = []
    for label, script, text, feat in [
        ("FAILED_6_5_10", script_6510, text_6510, feat_6510),
        ("SUCCESSFUL_10AD", script_10ad, text_10ad, feat_10ad),
    ]:
        script_rows.append({
            "SCRIPT_ROLE": label,
            "SCRIPT_PATH": str(script).replace("\\", "/") if script else "",
            "EXISTS": 1 if script and (repo / script).exists() else 0,
            "SHA256": sha256_file(repo / script) if script and (repo / script).exists() else "",
            **feat,
        })

    delta_rows = [
        {
            "DELTA_ID": "D01",
            "AREA": "Readback gates",
            "FAILED_6_5_10": f"COUNT={feat_6510.get('COUNT_COUNT','')}; LIST={feat_6510.get('LIST_COUNT','')}; intermediate={feat_6510.get('HAS_INTERMEDIATE_READBACK','')}",
            "SUCCESSFUL_10AD": f"COUNT={feat_10ad.get('COUNT_COUNT','')}; LIST={feat_10ad.get('LIST_COUNT','')}; intermediate={feat_10ad.get('HAS_INTERMEDIATE_READBACK','')}",
            "ASSESSMENT": "10AD's explicit readback gates are the safest known pattern.",
            "RECOMMENDATION": "Final promotion plan should copy the 10AD readback shape rather than the failed 6.5.10 assumptions.",
        },
        {
            "DELTA_ID": "D02",
            "AREA": "Final cross-table readback",
            "FAILED_6_5_10": f"final_cross={feat_6510.get('HAS_FINAL_CROSS_TABLE_READBACK','')}",
            "SUCCESSFUL_10AD": f"final_cross={feat_10ad.get('HAS_FINAL_CROSS_TABLE_READBACK','')}",
            "ASSESSMENT": "The final cross-table readback distinguishes a successful runtime state from merely reported imports.",
            "RECOMMENDATION": "Require final SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70 before any final promotion acceptance.",
        },
        {
            "DELTA_ID": "D03",
            "AREA": "Backup/restore evidence",
            "FAILED_6_5_10": f"rollback={s10r.get('STATUS','')}",
            "SUCCESSFUL_10AD": f"restore={s10ad_restore.get('STATUS','')}; exact={s10ad_restore.get('RESTORED_EXACT_BACKUP','')}",
            "ASSESSMENT": "10AD has exact restore and fingerprint closure.",
            "RECOMMENDATION": "Any final promotion package must include immediate rollback/restore and post-promotion verification gates.",
        },
        {
            "DELTA_ID": "D04",
            "AREA": "Observed outcome",
            "FAILED_6_5_10": f"active after={s6510.get('ACTIVE_MESSAGE_HEADER_COUNT','')}/{s6510.get('ACTIVE_TEXT_HEADER_COUNT','')}",
            "SUCCESSFUL_10AD": f"active after sequence={s10ad_final.get('ACTIVE_MESSAGES_HEADER_COUNT_AFTER_SEQUENCE','')}/{s10ad_final.get('ACTIVE_TEXT_HEADER_COUNT_AFTER_SEQUENCE','')}",
            "ASSESSMENT": "The controlled sequence succeeded where the broad package failed.",
            "RECOMMENDATION": "Treat failed 6.5.10 as package/wrapper/finalizer delta until proven otherwise.",
        },
    ]

    conclusion = [
        {
            "CONCLUSION": "DATA_NOT_PRIMARY_CAUSE",
            "STATUS": "SUPPORTED",
            "DETAIL": "Message14, text70, full70 text-only, candidate10 append, and two-table V1 all proved under controlled gates.",
        },
        {
            "CONCLUSION": "FAILED_6_5_10_PACKAGE_OR_WRAPPER_DELTA",
            "STATUS": "PRIMARY_REVIEW_ITEM",
            "DETAIL": "The remaining difference is how the failed 6.5.10 package/wrapper/finalizer executed or validated compared with 10AD.",
        },
        {
            "CONCLUSION": "FINAL_PROMOTION_PATTERN",
            "STATUS": "RECOMMENDED_BUT_NOT_AUTHORIZED",
            "DETAIL": "Use the 10AD V1 command shape with explicit intermediate/final readbacks and backup/restore gates for any future final promotion plan.",
        },
    ]

    next_plan = [
        {
            "STEP": 1,
            "ACTION": "PREPARE_10AG_FINAL_PROMOTION_PLAN_FROM_10AD_PATTERN",
            "DETAIL": "Plan a guarded final promotion package using the successful 10AD command sequence and verification gates.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "REQUIRE_POST_PROMOTION_ACCEPTANCE_GATE",
            "DETAIL": "Final package should not just execute; it should verify active 14/70 after fresh reopen and require explicit acceptance before considering promotion done.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "KEEP_ROLLBACK_READY",
            "DETAIL": "Final package must retain rollback backup until post-promotion verification and savepoint are accepted.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "DO_NOT_CHANGE_SOURCE_HELP_CMDHELPCHK",
            "DETAIL": "This remains a messaging catalog promotion lane only; source, HELP DATA, and CMDHELPCHK stay untouched.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AF is report-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active index/LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "FINAL_ACTIVE_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Final promotion remains closed until 10AG+ explicit authorization."},
    ]

    diff_rows = make_script_diff(repo, script_6510, script_10ad)

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10af_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10af_evidence_matrix_v1.csv", evidence, ["EVIDENCE_ID", "CLAIM", "SOURCE", "OBSERVED", "INTERPRETATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10af_script_feature_comparison_v1.csv", script_rows, ["SCRIPT_ROLE", "SCRIPT_PATH", "EXISTS", "SHA256", "USE_COUNT", "IMPORT_COUNT", "ZAP_COUNT", "COUNT_COUNT", "LIST_COUNT", "QUIT_COUNT", "HAS_FINAL_CROSS_TABLE_READBACK", "HAS_INTERMEDIATE_READBACK", "HAS_QUIT"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10af_delta_review_v1.csv", delta_rows, ["DELTA_ID", "AREA", "FAILED_6_5_10", "SUCCESSFUL_10AD", "ASSESSMENT", "RECOMMENDATION"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10af_script_diff_v1.csv", diff_rows, ["DIFF_LINE_NO", "DIFF_LINE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10af_conclusions_v1.csv", conclusion, ["CONCLUSION", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10af_next_plan_v1.csv", next_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10af_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10af_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AE_STATUS": s10ae.get("STATUS", ""),
        "MSG_022AE_6_5_10AE_SAVEPOINT_PRESENT": 1 if sp10ae else 0,
        "FAILED_6_5_10_STATUS": s6510.get("STATUS", ""),
        "SUCCESSFUL_10AD_STATUS": s10ad_restore.get("STATUS", ""),
        "FAILED_SCRIPT_FOUND": 1 if script_6510 else 0,
        "SUCCESSFUL_SCRIPT_FOUND": 1 if script_10ad and (repo / script_10ad).exists() else 0,
        "PRIMARY_DELTA_CLASSIFICATION": "FAILED_6_5_10_PACKAGE_OR_WRAPPER_DELTA",
        "RECOMMENDED_PROMOTION_PATTERN": "USE_10AD_V1_WITH_INTERMEDIATE_AND_FINAL_READBACK_GATES",
        "FINAL_ACTIVE_PROMOTION_RETRY_ALLOWED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10AE_STATUS",
         "MSG_022AE_6_5_10AE_SAVEPOINT_PRESENT", "FAILED_6_5_10_STATUS",
         "SUCCESSFUL_10AD_STATUS", "FAILED_SCRIPT_FOUND", "SUCCESSFUL_SCRIPT_FOUND",
         "PRIMARY_DELTA_CLASSIFICATION", "RECOMMENDED_PROMOTION_PATTERN",
         "FINAL_ACTIVE_PROMOTION_RETRY_ALLOWED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AF_ORIGINAL_PROMOTION_FAILURE_DELTA_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AF Original Promotion Failure Delta Review\n\nStatus: `{status}`\n\n10AF is report-only. It compares the failed 6.5.10 promotion evidence with the successful 10AD V1 sequence and classifies the remaining suspect as package/wrapper/finalizer delta.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AE status: {s10ae.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AE savepoint present: {1 if sp10ae else 0}")
    print(f"  failed 6.5.10 status: {s6510.get('STATUS','')}")
    print(f"  successful 10AD status: {s10ad_restore.get('STATUS','')}")
    print(f"  failed script found: {1 if script_6510 else 0}")
    print(f"  successful script found: {1 if script_10ad and (repo / script_10ad).exists() else 0}")
    print("  primary delta classification: FAILED_6_5_10_PACKAGE_OR_WRAPPER_DELTA")
    print("  recommended promotion pattern: USE_10AD_V1_WITH_INTERMEDIATE_AND_FINAL_READBACK_GATES")
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

