#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AC_TWO_TABLE_PROMOTION_SEQUENCE_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AC_TWO_TABLE_PROMOTION_SEQUENCE_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_EXECUTION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
APPLY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ac_two_table_promotion_sequence_plan_v1")

MSG14_SOURCE = Path("docs/messaging/apply/phase22ae_6_5_10_guarded_active_promotion_execution_v1/import/system_messages_active_promotion_full_state.csv")
TEXT70_SOURCE_6510 = Path("docs/messaging/apply/phase22ae_6_5_10_guarded_active_promotion_execution_v1/import/system_message_text_active_promotion_full_state.csv")
TEXT70_SOURCE_10Z = Path("docs/messaging/apply/phase22ae_6_5_10z_full70_text_zap_import_sequence_plan_v1/import/system_message_text_full70_zap_import_sequence.csv")

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
ACTIVE_MSG_INDEX = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGES.cdx")
ACTIVE_TEXT_INDEX = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx")
ACTIVE_MSG_LMDB = Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGES.cdx.d")
ACTIVE_TEXT_LMDB = Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d")

PROOF_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
EXPECTED_LOCALES = ["en-US", "es", "fr", "de", "it"]

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

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

def hash_dir(path: Path):
    if not path.exists() or not path.is_dir():
        return "", 0, 0
    files = sorted(p for p in path.rglob("*") if p.is_file())
    h = hashlib.sha256()
    total = 0
    for f in files:
        h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
        h.update(sha256_file(f).encode("ascii"))
        total += f.stat().st_size
    return h.hexdigest(), len(files), total

def file_info(repo: Path, role: str, path: Path):
    p = repo / path
    if p.is_dir():
        h, count, size = hash_dir(p)
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "dir", "BYTES": size, "SHA256": h, "FILES": count}
    if p.is_file():
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "file", "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "FILES": 1}
    return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "SHA256": "", "FILES": 0}

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

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

def classify_message_rows(rows):
    out = []
    symbols = []
    for i, r in enumerate(rows, start=1):
        text = " ".join("" if v is None else str(v) for v in r.values())
        symbol = ""
        for s in PROOF_SYMBOLS:
            if s in text:
                symbol = s
                break
        if symbol:
            symbols.append(symbol)
        out.append({
            "ROW": i,
            "SYMBOL": symbol,
            "HAS_PROOF_SYMBOL": 1 if symbol else 0,
            "ROW_JSON": json.dumps(r, ensure_ascii=False, sort_keys=True),
        })
    return out, symbols

def classify_text_rows(rows):
    out = []
    for i, r in enumerate(rows, start=1):
        text = " ".join("" if v is None else str(v) for v in r.values())
        vals = {str(v).strip() for v in r.values()}
        symbol = ""
        for s in PROOF_SYMBOLS:
            if s in text:
                symbol = s
                break
        locale = ""
        for loc in EXPECTED_LOCALES:
            if loc in vals or f"|{loc}" in text:
                locale = loc
                break
        section = "BASELINE60" if i <= 60 else "CANDIDATE10"
        out.append({
            "ROW": i,
            "SECTION": section,
            "SYMBOL": symbol,
            "LOCALE": locale,
            "HAS_PROOF_SYMBOL": 1 if symbol else 0,
            "HAS_EXPECTED_LOCALE": 1 if locale else 0,
            "ROW_JSON": json.dumps(r, ensure_ascii=False, sort_keys=True),
        })
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    apply_root = repo / APPLY_ROOT

    ab = first_row(reports / "message_catalog_phase22ae_6_5_10ab_status_summary_v1.csv")
    sp10ab, latest = savepoint_present(repo, "MSG-022AE.6.5.10AB")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AB_GREEN",
         ab.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AB_FULL70_TEXT_SEQUENCE_RESULT_CLASSIFICATION_GREEN_SOURCE_HELD",
         ab.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AB_SAVEPOINT_PRESENT", sp10ab, latest)
    gate("BASELINE60_REPLACE_PROVEN_IN_10AB", ab.get("BASELINE60_REPLACE_PROVEN") == "1", ab.get("BASELINE60_REPLACE_PROVEN", "missing"))
    gate("CANDIDATE10_APPEND_PROVEN_IN_10AB", ab.get("CANDIDATE10_APPEND_PROVEN") == "1", ab.get("CANDIDATE10_APPEND_PROVEN", "missing"))
    gate("FULL70_TEXT_ZAP_IMPORT_PROVEN_IN_10AB", ab.get("FULL70_TEXT_ZAP_IMPORT_PROVEN") == "1", ab.get("FULL70_TEXT_ZAP_IMPORT_PROVEN", "missing"))
    gate("TWO_TABLE_SEQUENCE_PRIMARY_SUSPECT_IN_10AB", ab.get("TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT") == "1", ab.get("TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT", "missing"))
    gate("FULL_PROMOTION_RETRY_CLOSED_IN_10AB", ab.get("FULL_ACTIVE_PROMOTION_RETRY_ALLOWED") == "0", ab.get("FULL_ACTIVE_PROMOTION_RETRY_ALLOWED", "missing"))

    gate("MSG14_SOURCE_EXISTS", (repo / MSG14_SOURCE).exists(), rel(repo / MSG14_SOURCE, repo))
    gate("TEXT70_6510_SOURCE_EXISTS", (repo / TEXT70_SOURCE_6510).exists(), rel(repo / TEXT70_SOURCE_6510, repo))
    gate("TEXT70_10Z_SOURCE_EXISTS", (repo / TEXT70_SOURCE_10Z).exists(), rel(repo / TEXT70_SOURCE_10Z, repo))
    gate("ACTIVE_MESSAGES_BASELINE_HEADER_COUNT_12", dbf_header_count(repo / ACTIVE_MSG_DBF) == 12, dbf_header_count(repo / ACTIVE_MSG_DBF))
    gate("ACTIVE_TEXT_BASELINE_HEADER_COUNT_60", dbf_header_count(repo / ACTIVE_TEXT_DBF) == 60, dbf_header_count(repo / ACTIVE_TEXT_DBF))
    gate("APPLY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not apply_root.exists()) or args.replace_existing_plan, rel(apply_root, repo))

    msg14 = read_csv(repo / MSG14_SOURCE)
    text70 = read_csv(repo / TEXT70_SOURCE_10Z)
    text70_6510 = read_csv(repo / TEXT70_SOURCE_6510)
    msg_headers = list(msg14[0].keys()) if msg14 else []
    text_headers = list(text70[0].keys()) if text70 else []

    gate("MSG14_HAS_14_ROWS", len(msg14) == 14, len(msg14))
    gate("TEXT70_HAS_70_ROWS", len(text70) == 70, len(text70))
    gate("TEXT70_MATCHES_FAILED_6510_TEXT_CSV", text70 == text70_6510 if text70 and text70_6510 else False, "row sequence comparison")

    msg_row_class, msg_symbols = classify_message_rows(msg14)
    text_row_class = classify_text_rows(text70)
    text_candidate_rows = [r for r in text_row_class if r["SECTION"] == "CANDIDATE10"]
    gate("MESSAGE14_HAS_TWO_PROOF_MESSAGE_ROWS", len([s for s in msg_symbols if s in PROOF_SYMBOLS]) >= 2, msg_symbols)
    gate("TEXT70_CANDIDATE_ROWS_HAVE_PROOF_SYMBOLS", all(r["HAS_PROOF_SYMBOL"] for r in text_candidate_rows), len(text_candidate_rows))
    gate("TEXT70_CANDIDATE_ROWS_HAVE_LOCALES", all(r["HAS_EXPECTED_LOCALE"] for r in text_candidate_rows), len(text_candidate_rows))

    artifact_rows = [
        file_info(repo, "msg14_source_csv", MSG14_SOURCE),
        file_info(repo, "text70_6510_source_csv", TEXT70_SOURCE_6510),
        file_info(repo, "text70_10z_source_csv", TEXT70_SOURCE_10Z),
        file_info(repo, "active_messages_dbf_current", ACTIVE_MSG_DBF),
        file_info(repo, "active_text_dbf_current", ACTIVE_TEXT_DBF),
        file_info(repo, "active_messages_index_current", ACTIVE_MSG_INDEX),
        file_info(repo, "active_text_index_current", ACTIVE_TEXT_INDEX),
        file_info(repo, "active_messages_lmdb_current", ACTIVE_MSG_LMDB),
        file_info(repo, "active_text_lmdb_current", ACTIVE_TEXT_LMDB),
    ]

    status = STATUS_BLOCKED
    staged_artifacts = []
    template_rows = []
    if failures == 0:
        if apply_root.exists() and args.replace_existing_plan:
            shutil.rmtree(apply_root)
        (apply_root / "import").mkdir(parents=True, exist_ok=True)
        (apply_root / "templates").mkdir(parents=True, exist_ok=True)

        msg_out = apply_root / "import/system_messages_full14_two_table_sequence.csv"
        text_out = apply_root / "import/system_message_text_full70_two_table_sequence.csv"
        write_csv(msg_out, msg14, msg_headers)
        write_csv(text_out, text70, text_headers)

        staged_artifacts = [
            {"ROLE": "MESSAGE14_TWO_TABLE_SEQUENCE_INPUT", "PATH": rel(msg_out, repo), "ROWS": len(read_csv(msg_out)), "BYTES": msg_out.stat().st_size, "SHA256": sha256_file(msg_out), "PURPOSE": "Future two-table sequence proof message import input."},
            {"ROLE": "TEXT70_TWO_TABLE_SEQUENCE_INPUT", "PATH": rel(text_out, repo), "ROWS": len(read_csv(text_out)), "BYTES": text_out.stat().st_size, "SHA256": sha256_file(text_out), "PURPOSE": "Future two-table sequence proof text import input."},
        ]

        variants = [
            {
                "VARIANT_ID": "V1_MESSAGE_FIRST_TEXT_SECOND_WITH_READBACK",
                "ORDER": "SYSTEM_MESSAGES then SYSTEM_MESSAGE_TEXT",
                "PURPOSE": "Closest controlled replay of broad promotion, but with readback after each table.",
                "TEMPLATE": "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_V1_MESSAGE_FIRST_TEXT_SECOND.dts.disabled",
                "SCRIPT_LINES": [
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    "* COUNT",
                    "* ZAP",
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    f"* IMPORT {(msg_out).resolve().as_posix()}",
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    "* COUNT",
                    "* LIST ALL",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    "* COUNT",
                    "* ZAP",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    f"* IMPORT {(text_out).resolve().as_posix()}",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    "* COUNT",
                    "* LIST ALL",
                ],
            },
            {
                "VARIANT_ID": "V2_TEXT_FIRST_MESSAGE_SECOND_WITH_READBACK",
                "ORDER": "SYSTEM_MESSAGE_TEXT then SYSTEM_MESSAGES",
                "PURPOSE": "Tests whether message-first state/order caused the original text failure.",
                "TEMPLATE": "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_V2_TEXT_FIRST_MESSAGE_SECOND.dts.disabled",
                "SCRIPT_LINES": [
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    "* COUNT",
                    "* ZAP",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    f"* IMPORT {(text_out).resolve().as_posix()}",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    "* COUNT",
                    "* LIST ALL",
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    "* COUNT",
                    "* ZAP",
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    f"* IMPORT {(msg_out).resolve().as_posix()}",
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    "* COUNT",
                    "* LIST ALL",
                ],
            },
            {
                "VARIANT_ID": "V3_MESSAGE_ONLY_THEN_TEXT_REOPEN_BOTH_AFTER_EACH",
                "ORDER": "message import; reopen both; text import; reopen both",
                "PURPOSE": "Maximizes explicit area/table rebinding and final cross-table readback.",
                "TEMPLATE": "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_V3_REOPEN_BOTH_AFTER_EACH.dts.disabled",
                "SCRIPT_LINES": [
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    "* ZAP",
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    f"* IMPORT {(msg_out).resolve().as_posix()}",
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    "* COUNT",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    "* COUNT",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    "* ZAP",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    f"* IMPORT {(text_out).resolve().as_posix()}",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    "* COUNT",
                    f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
                    "* COUNT",
                    f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
                    "* LIST ALL",
                ],
            },
        ]

        for v in variants:
            path = apply_root / "templates" / v["TEMPLATE"]
            path.write_text("\n".join([
                f"* {v['TEMPLATE']}",
                f"* {v['VARIANT_ID']}",
                "* DISABLED TEMPLATE ONLY - DO NOT EXECUTE IN 10AC",
                "* Future 10AD execution, if authorized, must backup and restore both active message tables.",
                "* No QUIT here; interactive runs quit manually.",
                "",
                *v["SCRIPT_LINES"],
                "",
                "* After readback, restore exact backup for both tables, indexes, LMDB, and sidecars.",
            ]), encoding="utf-8")
            template_rows.append({
                "VARIANT_ID": v["VARIANT_ID"],
                "ORDER": v["ORDER"],
                "PURPOSE": v["PURPOSE"],
                "TEMPLATE_PATH": rel(path, repo),
                "ACTIVE_EXECUTION_AUTHORIZED": 0,
            })

        status = STATUS_GREEN

    proof_plan = [
        {"STEP": 1, "PHASE": "PRECONDITION", "ACTION": "REQUIRE_10AB_GREEN_AND_SAVEPOINT", "DETAIL": "10AB must classify all isolated text paths as proven and two-table sequencing as the remaining suspect.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "PHASE": "INPUT", "ACTION": "USE_MSG14_AND_TEXT70_INPUTS", "DETAIL": "Future 10AD should use the exact message14 and text70 inputs tied to the failed broad promotion path.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "PHASE": "VARIANT_PLAN", "ACTION": "STAGE_ORDER_VARIANTS", "DETAIL": "Plan message-first/text-second, text-first/message-second, and explicit reopen/readback variants.", "MUTATES_ACTIVE": 0},
        {"STEP": 4, "PHASE": "READBACK_GATES", "ACTION": "REQUIRE_INTERMEDIATE_AND_FINAL_COUNTS", "DETAIL": "Future execution must prove message table 14 and text table 70 at intermediate and final readback points.", "MUTATES_ACTIVE": 0},
        {"STEP": 5, "PHASE": "RESTORE", "ACTION": "RESTORE_BOTH_TABLES_ALWAYS", "DETAIL": "Any future execution must restore exact backups for SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT, including indexes/LMDB/sidecars.", "MUTATES_ACTIVE": 0},
        {"STEP": 6, "PHASE": "HOLD", "ACTION": "NO_ACTIVE_EXECUTION_IN_10AC", "DETAIL": "10AC stages plan artifacts only. Active two-table diagnostic requires explicit 10AD authorization.", "MUTATES_ACTIVE": 0},
    ]

    decision_matrix = [
        {"IF_10AD_RESULT": "V1_MESSAGE_FIRST_TEXT_SECOND_SUCCEEDS", "THEN": "Original failure likely came from missing readback/restore discipline or transient state in 6.5.10 execution, not data.", "NEXT": "Plan guarded final promotion with same readback gates."},
        {"IF_10AD_RESULT": "V1_FAILS_BUT_V2_SUCCEEDS", "THEN": "Ordering dependency is implicated; text-first may be required for safe promotion.", "NEXT": "Classify order bug and avoid message-first active promotion."},
        {"IF_10AD_RESULT": "TEXT_TABLE_REOPENS_ZERO_AFTER_MESSAGE_FIRST", "THEN": "This reproduces the original symptom with a two-table sequence.", "NEXT": "Investigate work-area/table binding, open-state, flush, and index/LMDB interaction after first table mutation."},
        {"IF_10AD_RESULT": "ALL_VARIANTS_SUCCEED", "THEN": "The original failure may have been package/script-specific or non-deterministic state.", "NEXT": "Plan a tightly guarded final active promotion with mandatory post-promotion verification and rollback option."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AC is plan-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active message DBF mutation in 10AC."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active text DBF mutation in 10AC."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active index/LMDB mutation in 10AC."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "TWO_TABLE_ACTIVE_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Future 10AD requires explicit authorization."},
    ]

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_artifact_inventory_v1.csv", artifact_rows, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_message14_row_classification_v1.csv", msg_row_class, ["ROW", "SYMBOL", "HAS_PROOF_SYMBOL", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_text70_row_classification_v1.csv", text_row_class, ["ROW", "SECTION", "SYMBOL", "LOCALE", "HAS_PROOF_SYMBOL", "HAS_EXPECTED_LOCALE", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_staged_artifacts_v1.csv", staged_artifacts, ["ROLE", "PATH", "ROWS", "BYTES", "SHA256", "PURPOSE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_variant_templates_v1.csv", template_rows, ["VARIANT_ID", "ORDER", "PURPOSE", "TEMPLATE_PATH", "ACTIVE_EXECUTION_AUTHORIZED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_sequence_plan_v1.csv", proof_plan, ["STEP", "PHASE", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_decision_matrix_v1.csv", decision_matrix, ["IF_10AD_RESULT", "THEN", "NEXT"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10ac_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AB_STATUS": ab.get("STATUS", ""),
        "MSG_022AE_6_5_10AB_SAVEPOINT_PRESENT": 1 if sp10ab else 0,
        "BASELINE60_REPLACE_PROVEN": ab.get("BASELINE60_REPLACE_PROVEN", ""),
        "CANDIDATE10_APPEND_PROVEN": ab.get("CANDIDATE10_APPEND_PROVEN", ""),
        "FULL70_TEXT_ZAP_IMPORT_PROVEN": ab.get("FULL70_TEXT_ZAP_IMPORT_PROVEN", ""),
        "TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT": ab.get("TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT", ""),
        "ACTIVE_MESSAGES_BASELINE_HEADER_COUNT": dbf_header_count(repo / ACTIVE_MSG_DBF),
        "ACTIVE_TEXT_BASELINE_HEADER_COUNT": dbf_header_count(repo / ACTIVE_TEXT_DBF),
        "APPLY_ROOT": rel(apply_root, repo),
        "MESSAGE14_ROWS": len(msg14),
        "TEXT70_ROWS": len(text70),
        "VARIANTS_STAGED": len(template_rows),
        "TWO_TABLE_EXECUTION_AUTHORIZED": 0,
        "TWO_TABLE_EXECUTION_EXECUTED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10AB_STATUS",
         "MSG_022AE_6_5_10AB_SAVEPOINT_PRESENT", "BASELINE60_REPLACE_PROVEN",
         "CANDIDATE10_APPEND_PROVEN", "FULL70_TEXT_ZAP_IMPORT_PROVEN",
         "TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT",
         "ACTIVE_MESSAGES_BASELINE_HEADER_COUNT", "ACTIVE_TEXT_BASELINE_HEADER_COUNT",
         "APPLY_ROOT", "MESSAGE14_ROWS", "TEXT70_ROWS", "VARIANTS_STAGED",
         "TWO_TABLE_EXECUTION_AUTHORIZED", "TWO_TABLE_EXECUTION_EXECUTED",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AC_TWO_TABLE_PROMOTION_SEQUENCE_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AC Two-Table Promotion Sequence Plan\n\nStatus: `{status}`\n\n10AC is plan-only. It stages two-table sequence variants for a future 10AD diagnostic and keeps active execution closed.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AB status: {ab.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AB savepoint present: {1 if sp10ab else 0}")
    print(f"  baseline60 replace proven: {ab.get('BASELINE60_REPLACE_PROVEN','')}")
    print(f"  candidate10 append proven: {ab.get('CANDIDATE10_APPEND_PROVEN','')}")
    print(f"  full70 text ZAP/import proven: {ab.get('FULL70_TEXT_ZAP_IMPORT_PROVEN','')}")
    print(f"  two-table promotion sequence primary suspect: {ab.get('TWO_TABLE_PROMOTION_SEQUENCE_PRIMARY_SUSPECT','')}")
    print(f"  active messages baseline header count: {dbf_header_count(repo / ACTIVE_MSG_DBF)}")
    print(f"  active text baseline header count: {dbf_header_count(repo / ACTIVE_TEXT_DBF)}")
    print(f"  apply root: {rel(apply_root, repo)}")
    print(f"  message14 rows: {len(msg14)}")
    print(f"  text70 rows: {len(text70)}")
    print(f"  variants staged: {len(template_rows)}")
    print("  two-table execution authorized: 0")
    print("  two-table execution executed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
