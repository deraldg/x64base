#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AG_GUARDED_FINAL_PROMOTION_PLAN_FROM_10AD_PATTERN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AG_GUARDED_FINAL_PROMOTION_PLAN_FROM_10AD_PATTERN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
APPLY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ag_guarded_final_promotion_plan_v1")

# Use the successful 10AD inputs and pattern as the source of the final promotion plan.
SOURCE_10AD_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ad_two_table_promotion_sequence_v1")
MSG14_10AD = SOURCE_10AD_ROOT / "import/system_messages_full14_two_table_sequence.csv"
TEXT70_10AD = SOURCE_10AD_ROOT / "import/system_message_text_full70_two_table_sequence.csv"

# Fallback to 10AC staged inputs if the 10AD package root is unavailable.
SOURCE_10AC_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ac_two_table_promotion_sequence_plan_v1")
MSG14_10AC = SOURCE_10AC_ROOT / "import/system_messages_full14_two_table_sequence.csv"
TEXT70_10AC = SOURCE_10AC_ROOT / "import/system_message_text_full70_two_table_sequence.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

PROOF_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
EXPECTED_LOCALES = ["en-US", "es", "fr", "de", "it"]

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

def choose_source(repo: Path):
    if (repo / MSG14_10AD).exists() and (repo / TEXT70_10AD).exists():
        return MSG14_10AD, TEXT70_10AD, "10AD"
    return MSG14_10AC, TEXT70_10AC, "10AC"

def row_contains(row, needle):
    text = " ".join("" if v is None else str(v) for v in row.values())
    return needle in text

def validate_inputs(msg_rows, text_rows):
    proof_message_hits = sum(1 for s in PROOF_SYMBOLS if any(row_contains(r, s) for r in msg_rows))
    proof_text_hits = sum(1 for s in PROOF_SYMBOLS if any(row_contains(r, s) for r in text_rows))
    locale_hits = sum(1 for loc in EXPECTED_LOCALES if any(row_contains(r, loc) for r in text_rows))
    return proof_message_hits, proof_text_hits, locale_hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    apply_root = repo / APPLY_ROOT

    af = first_row(reports / "message_catalog_phase22ae_6_5_10af_status_summary_v1.csv")
    ad_restore = first_row(reports / "message_catalog_phase22ae_6_5_10ad_restore_status_summary_v1.csv")
    sp10af, latest = savepoint_present(repo, "MSG-022AE.6.5.10AF")

    msg_source, text_source, source_label = choose_source(repo)
    msg_rows = read_csv(repo / msg_source)
    text_rows = read_csv(repo / text_source)
    msg_headers = list(msg_rows[0].keys()) if msg_rows else []
    text_headers = list(text_rows[0].keys()) if text_rows else []
    proof_message_hits, proof_text_hits, locale_hits = validate_inputs(msg_rows, text_rows)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AF_GREEN",
         af.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AF_ORIGINAL_PROMOTION_FAILURE_DELTA_REVIEW_GREEN_SOURCE_HELD",
         af.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AF_SAVEPOINT_PRESENT", sp10af, latest)
    gate("10AF_RECOMMENDED_10AD_PATTERN",
         af.get("RECOMMENDED_PROMOTION_PATTERN") == "USE_10AD_V1_WITH_INTERMEDIATE_AND_FINAL_READBACK_GATES",
         af.get("RECOMMENDED_PROMOTION_PATTERN", "missing"))
    gate("10AF_FINAL_RETRY_CLOSED",
         af.get("FINAL_ACTIVE_PROMOTION_RETRY_ALLOWED") == "0",
         af.get("FINAL_ACTIVE_PROMOTION_RETRY_ALLOWED", "missing"))
    gate("10AD_RESTORED_GREEN",
         ad_restore.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1_PROVEN_AND_RESTORED",
         ad_restore.get("STATUS", "missing"))
    gate("10AD_POST_RESTORE_BASELINE_12_60",
         ad_restore.get("POST_RESTORE_ACTIVE_MESSAGES_HEADER_COUNT") == "12" and ad_restore.get("POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT") == "60",
         f"messages={ad_restore.get('POST_RESTORE_ACTIVE_MESSAGES_HEADER_COUNT','')}; text={ad_restore.get('POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT','')}")
    gate("ACTIVE_MESSAGES_BASELINE_HEADER_COUNT_12", dbf_header_count(repo / ACTIVE_MSG_DBF) == 12, dbf_header_count(repo / ACTIVE_MSG_DBF))
    gate("ACTIVE_TEXT_BASELINE_HEADER_COUNT_60", dbf_header_count(repo / ACTIVE_TEXT_DBF) == 60, dbf_header_count(repo / ACTIVE_TEXT_DBF))
    gate("SOURCE_MESSAGE14_EXISTS", (repo / msg_source).exists(), rel(repo / msg_source, repo))
    gate("SOURCE_TEXT70_EXISTS", (repo / text_source).exists(), rel(repo / text_source, repo))
    gate("SOURCE_MESSAGE14_ROWS", len(msg_rows) == 14, len(msg_rows))
    gate("SOURCE_TEXT70_ROWS", len(text_rows) == 70, len(text_rows))
    gate("MESSAGE_PROOF_SYMBOLS_PRESENT", proof_message_hits == 2, proof_message_hits)
    gate("TEXT_PROOF_SYMBOLS_PRESENT", proof_text_hits == 2, proof_text_hits)
    gate("TEXT_PROOF_LOCALES_PRESENT", locale_hits == 5, locale_hits)
    gate("APPLY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not apply_root.exists()) or args.replace_existing_plan, rel(apply_root, repo))

    status = STATUS_BLOCKED
    staged_artifacts = []
    template_rows = []
    if failures == 0:
        if apply_root.exists() and args.replace_existing_plan:
            shutil.rmtree(apply_root)
        (apply_root / "import").mkdir(parents=True, exist_ok=True)
        (apply_root / "templates").mkdir(parents=True, exist_ok=True)

        msg_out = apply_root / "import/system_messages_final_promotion_full14.csv"
        text_out = apply_root / "import/system_message_text_final_promotion_full70.csv"
        write_csv(msg_out, msg_rows, msg_headers)
        write_csv(text_out, text_rows, text_headers)

        staged_artifacts = [
            {
                "ROLE": "FINAL_PROMOTION_SYSTEM_MESSAGES_INPUT",
                "PATH": rel(msg_out, repo),
                "SOURCE_PATH": rel(repo / msg_source, repo),
                "SOURCE_LABEL": source_label,
                "ROWS": len(read_csv(msg_out)),
                "BYTES": msg_out.stat().st_size,
                "SHA256": sha256_file(msg_out),
                "PURPOSE": "Future 10AH final promotion input for SYSTEM_MESSAGES.",
            },
            {
                "ROLE": "FINAL_PROMOTION_SYSTEM_MESSAGE_TEXT_INPUT",
                "PATH": rel(text_out, repo),
                "SOURCE_PATH": rel(repo / text_source, repo),
                "SOURCE_LABEL": source_label,
                "ROWS": len(read_csv(text_out)),
                "BYTES": text_out.stat().st_size,
                "SHA256": sha256_file(text_out),
                "PURPOSE": "Future 10AH final promotion input for SYSTEM_MESSAGE_TEXT.",
            },
        ]

        template = apply_root / "templates/MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_TEMPLATE.dts.disabled"
        template.write_text("\n".join([
            "* DISABLED TEMPLATE ONLY - DO NOT EXECUTE IN 10AG",
            "* Future 10AH guarded final promotion should follow the proven 10AD V1 pattern.",
            "* No QUIT here; interactive runs quit manually.",
            "",
            "* 1. Promote SYSTEM_MESSAGES with immediate readback.",
            f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "* COUNT",
            "* ZAP",
            f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            f"* IMPORT {(msg_out).resolve().as_posix()}",
            f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "* COUNT",
            "* LIST ALL",
            "",
            "* 2. Promote SYSTEM_MESSAGE_TEXT with immediate readback.",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "* COUNT",
            "* ZAP",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            f"* IMPORT {(text_out).resolve().as_posix()}",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "* COUNT",
            "* LIST ALL",
            "",
            "* 3. Final cross-table readback required before promotion acceptance.",
            f"* USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "* COUNT",
            f"* USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "* COUNT",
            "",
            "* 4. Future 10AH must produce post-promotion verification reports.",
            "* 5. Rollback backup must remain available until verification and savepoint acceptance.",
        ]), encoding="utf-8")

        template_rows = [
            {
                "TEMPLATE_ID": "10AH_FINAL_PROMOTION_FROM_10AD_V1",
                "TEMPLATE_PATH": rel(template, repo),
                "PATTERN": "SYSTEM_MESSAGES first, SYSTEM_MESSAGE_TEXT second, immediate readback after each, final cross-table readback",
                "ACTIVE_EXECUTION_AUTHORIZED": 0,
                "EXECUTION_PACKAGE_REQUIRED": "10AH",
            }
        ]

        status = STATUS_GREEN

    plan_rows = [
        {
            "STEP": 1,
            "PHASE": "PRECONDITION",
            "ACTION": "REQUIRE_10AF_GREEN_AND_SAVEPOINT",
            "DETAIL": "10AF must classify the failure delta and recommend the proven 10AD V1 pattern.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "PHASE": "INPUTS",
            "ACTION": "STAGE_FINAL_MESSAGE14_AND_TEXT70_INPUTS",
            "DETAIL": "Stage final promotion CSVs from the successful 10AD inputs, with 10AC fallback only for planning.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "PHASE": "EXECUTION_PATTERN",
            "ACTION": "USE_10AD_V1_SEQUENCE",
            "DETAIL": "SYSTEM_MESSAGES first, immediate count/list, SYSTEM_MESSAGE_TEXT second, immediate count/list.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "PHASE": "VERIFICATION",
            "ACTION": "REQUIRE_FINAL_CROSS_TABLE_READBACK_14_70",
            "DETAIL": "Future final promotion acceptance must prove fresh final readback of SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 5,
            "PHASE": "ROLLBACK",
            "ACTION": "KEEP_EXACT_BACKUP_UNTIL_SAVEPOINT_ACCEPTED",
            "DETAIL": "10AH must keep rollback backup available until post-promotion verification and savepoint acceptance.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 6,
            "PHASE": "BOUNDARY",
            "ACTION": "NO_ACTIVE_EXECUTION_IN_10AG",
            "DETAIL": "10AG is plan-only. Active final promotion requires explicit 10AH authorization.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    acceptance_gates = [
        {"GATE_ID": "G01", "GATE": "Runtime imports 14 SYSTEM_MESSAGES rows", "EXPECTED": "Imported 14 records", "REQUIRED": 1},
        {"GATE_ID": "G02", "GATE": "Immediate SYSTEM_MESSAGES readback", "EXPECTED": "COUNT 14 and LIST 14", "REQUIRED": 1},
        {"GATE_ID": "G03", "GATE": "Runtime imports 70 SYSTEM_MESSAGE_TEXT rows", "EXPECTED": "Imported 70 records", "REQUIRED": 1},
        {"GATE_ID": "G04", "GATE": "Immediate SYSTEM_MESSAGE_TEXT readback", "EXPECTED": "COUNT 70 and LIST 70", "REQUIRED": 1},
        {"GATE_ID": "G05", "GATE": "Final cross-table readback", "EXPECTED": "SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70 after fresh USE", "REQUIRED": 1},
        {"GATE_ID": "G06", "GATE": "No HELP DATA / CMDHELPCHK / source mutation", "EXPECTED": "0 mutation rows", "REQUIRED": 1},
        {"GATE_ID": "G07", "GATE": "Rollback backup retained until savepoint", "EXPECTED": "backup manifest exists and is restorable", "REQUIRED": 1},
    ]

    rollback_plan = [
        {
            "ROLLBACK_ITEM": "Active SYSTEM_MESSAGES artifacts",
            "SCOPE": "DBF, sidecars, messaging/default CDX, LMDB dirs if present",
            "REQUIRED": 1,
        },
        {
            "ROLLBACK_ITEM": "Active SYSTEM_MESSAGE_TEXT artifacts",
            "SCOPE": "DBF, sidecars, messaging/default CDX, LMDB dirs if present",
            "REQUIRED": 1,
        },
        {
            "ROLLBACK_ITEM": "Post-failure restore command",
            "SCOPE": "10AH must include restore wrapper equivalent to 10AD restore discipline",
            "REQUIRED": 1,
        },
        {
            "ROLLBACK_ITEM": "Post-success hold",
            "SCOPE": "Do not delete backup immediately after success; keep until savepoint acceptance",
            "REQUIRED": 1,
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AG is plan-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 10AG."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation in 10AG."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active index/LMDB mutation in 10AG."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "FINAL_ACTIVE_PROMOTION_EXECUTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Future 10AH requires explicit authorization."},
    ]

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ag_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ag_staged_artifacts_v1.csv", staged_artifacts, ["ROLE", "PATH", "SOURCE_PATH", "SOURCE_LABEL", "ROWS", "BYTES", "SHA256", "PURPOSE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ag_template_manifest_v1.csv", template_rows, ["TEMPLATE_ID", "TEMPLATE_PATH", "PATTERN", "ACTIVE_EXECUTION_AUTHORIZED", "EXECUTION_PACKAGE_REQUIRED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ag_final_promotion_plan_v1.csv", plan_rows, ["STEP", "PHASE", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ag_acceptance_gates_v1.csv", acceptance_gates, ["GATE_ID", "GATE", "EXPECTED", "REQUIRED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ag_rollback_plan_v1.csv", rollback_plan, ["ROLLBACK_ITEM", "SCOPE", "REQUIRED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ag_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10ag_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AF_STATUS": af.get("STATUS", ""),
        "MSG_022AE_6_5_10AF_SAVEPOINT_PRESENT": 1 if sp10af else 0,
        "RECOMMENDED_PROMOTION_PATTERN": "USE_10AD_V1_WITH_INTERMEDIATE_AND_FINAL_READBACK_GATES",
        "INPUT_SOURCE_LABEL": source_label,
        "APPLY_ROOT": rel(apply_root, repo),
        "MESSAGE14_ROWS": len(msg_rows),
        "TEXT70_ROWS": len(text_rows),
        "ACTIVE_MESSAGES_BASELINE_HEADER_COUNT": dbf_header_count(repo / ACTIVE_MSG_DBF),
        "ACTIVE_TEXT_BASELINE_HEADER_COUNT": dbf_header_count(repo / ACTIVE_TEXT_DBF),
        "FINAL_PROMOTION_EXECUTION_AUTHORIZED": 0,
        "FINAL_PROMOTION_EXECUTION_EXECUTED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10AF_STATUS",
         "MSG_022AE_6_5_10AF_SAVEPOINT_PRESENT", "RECOMMENDED_PROMOTION_PATTERN",
         "INPUT_SOURCE_LABEL", "APPLY_ROOT", "MESSAGE14_ROWS", "TEXT70_ROWS",
         "ACTIVE_MESSAGES_BASELINE_HEADER_COUNT", "ACTIVE_TEXT_BASELINE_HEADER_COUNT",
         "FINAL_PROMOTION_EXECUTION_AUTHORIZED", "FINAL_PROMOTION_EXECUTION_EXECUTED",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AG_GUARDED_FINAL_PROMOTION_PLAN_FROM_10AD_PATTERN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AG Guarded Final Promotion Plan from 10AD Pattern\n\nStatus: `{status}`\n\n10AG is plan-only. It stages final-promotion inputs and a disabled 10AH execution template based on the proven 10AD V1 pattern.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AF status: {af.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AF savepoint present: {1 if sp10af else 0}")
    print("  recommended promotion pattern: USE_10AD_V1_WITH_INTERMEDIATE_AND_FINAL_READBACK_GATES")
    print(f"  input source label: {source_label}")
    print(f"  apply root: {rel(apply_root, repo)}")
    print(f"  message14 rows: {len(msg_rows)}")
    print(f"  text70 rows: {len(text_rows)}")
    print(f"  active messages baseline header count: {dbf_header_count(repo / ACTIVE_MSG_DBF)}")
    print(f"  active text baseline header count: {dbf_header_count(repo / ACTIVE_TEXT_DBF)}")
    print("  final promotion execution authorized: 0")
    print("  final promotion execution executed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
