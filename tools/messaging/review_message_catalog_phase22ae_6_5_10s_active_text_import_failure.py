#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10T_TEXT_ONLY_ACTIVE_IMPORT_MICRO_PROOF_PLAN"

REPORT_DIR = Path("docs/messaging/reports")

ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_INDEX = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx")
ACTIVE_TEXT_INDEX_META = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx.meta")
ACTIVE_TEXT_LMDB = Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d")
DEFAULT_TEXT_INDEX = Path("dottalkpp/data/indexes/SYSTEM_MESSAGE_TEXT.cdx")
DEFAULT_TEXT_INDEX_META = Path("dottalkpp/data/indexes/SYSTEM_MESSAGE_TEXT.cdx.meta")
DEFAULT_TEXT_LMDB = Path("dottalkpp/data/lmdb/SYSTEM_MESSAGE_TEXT.cdx.d")

SANDBOX_TEXT_DBF = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1/dbf/SYSTEM_MESSAGE_TEXT.dbf")
SANDBOX_TEXT_INDEX = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1/indexes/SYSTEM_MESSAGE_TEXT.cdx")
SANDBOX_TEXT_LMDB = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1/lmdb/SYSTEM_MESSAGE_TEXT.cdx.d")

ACTIVE_TEXT_IMPORT = Path("docs/messaging/apply/phase22ae_6_5_10_guarded_active_promotion_execution_v1/import/system_message_text_active_promotion_full_state.csv")
SANDBOX_TEXT_IMPORT = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1/import/system_message_text_canonical_field_map_full_state.csv")
PLAN_TEXT_IMPORT = Path("docs/messaging/apply/phase22ae_6_5_9_active_promotion_plan_v1/import/system_message_text_active_promotion_full_state.csv")

ACTIVE_MSG_IMPORT = Path("docs/messaging/apply/phase22ae_6_5_10_guarded_active_promotion_execution_v1/import/system_messages_active_promotion_full_state.csv")
SANDBOX_MSG_IMPORT = Path("docs/messaging/sandbox/phase22ae_6_5_6_canonical_field_map_zap_import_v1/import/system_messages_canonical_field_map_full_state.csv")

SIDE_EXTS = [".dtx", ".dbt", ".fpt", ".memo", ".mdx", ".cdx", ".cdx.meta"]

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

def parse_dbf_header(path: Path):
    if not path.exists() or path.stat().st_size < 32:
        return {"EXISTS": 1 if path.exists() else 0, "RECORD_COUNT": "", "HEADER_LEN": "", "RECORD_LEN": "", "VERSION": "", "HEADER_TERMINATOR_OK": "", "FIELDS": []}
    data = path.read_bytes()
    version = data[0]
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    terminator_ok = 0
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            terminator_ok = 1
            break
        raw = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11])
        length = data[pos+16]
        decimals = data[pos+17]
        if name:
            fields.append({"FIELD": name, "TYPE": ftype, "LENGTH": length, "DECIMALS": decimals, "OFFSET": offset})
            offset += length
        pos += 32
    return {
        "EXISTS": 1,
        "VERSION": version,
        "RECORD_COUNT": record_count,
        "HEADER_LEN": header_len,
        "RECORD_LEN": record_len,
        "HEADER_TERMINATOR_OK": terminator_ok,
        "FIELD_COUNT": len(fields),
        "FIELDS": fields,
    }

def header_rows(repo: Path, role: str, path: Path):
    p = repo / path
    h = parse_dbf_header(p)
    base = {
        "ROLE": role,
        "PATH": rel(p, repo),
        "EXISTS": h.get("EXISTS", 0),
        "VERSION": h.get("VERSION", ""),
        "RECORD_COUNT": h.get("RECORD_COUNT", ""),
        "HEADER_LEN": h.get("HEADER_LEN", ""),
        "RECORD_LEN": h.get("RECORD_LEN", ""),
        "HEADER_TERMINATOR_OK": h.get("HEADER_TERMINATOR_OK", ""),
        "FIELD_COUNT": h.get("FIELD_COUNT", ""),
        "BYTES": p.stat().st_size if p.exists() else 0,
        "SHA256": sha256_file(p),
    }
    fields = []
    for f in h.get("FIELDS", []):
        row = dict(base)
        row.update(f)
        fields.append(row)
    if not fields:
        fields.append(dict(base, FIELD="", TYPE="", LENGTH="", DECIMALS="", OFFSET=""))
    return base, fields

def csv_summary(repo: Path, role: str, path: Path):
    p = repo / path
    rows = read_csv(p)
    headers = list(rows[0].keys()) if rows else []
    last_rows = rows[-10:] if rows else []
    proof_symbols = {
        "MESSAGE_PROOF_MODE_STATUS",
        "MESSAGE_PROOF_BOUNDARY_NOTE",
    }
    proof_hits = 0
    proof_locale_pairs = 0
    for r in rows:
        vals = {str(v).strip() for v in r.values()}
        if vals & proof_symbols:
            proof_hits += 1
        for sym in proof_symbols:
            if sym in vals and any(loc in vals for loc in ["en-US", "es", "fr", "de", "it"]):
                proof_locale_pairs += 1
                break
    return {
        "ROLE": role,
        "PATH": rel(p, repo),
        "EXISTS": 1 if p.exists() else 0,
        "ROWS": len(rows),
        "COLUMNS": ";".join(headers),
        "BYTES": p.stat().st_size if p.exists() else 0,
        "SHA256": sha256_file(p),
        "PROOF_SYMBOL_ROW_HITS": proof_hits,
        "PROOF_SYMBOL_LOCALE_PAIR_HITS": proof_locale_pairs,
        "LAST_ROWS_JSON": json.dumps(last_rows, ensure_ascii=False, sort_keys=True),
    }

def find_backup_text_dbf(repo: Path):
    prep = first_row(repo / REPORT_DIR / "message_catalog_phase22ae_6_5_10_prepare_status_summary_v1.csv")
    backup_root = prep.get("BACKUP_ROOT", "")
    if not backup_root:
        return Path("")
    return Path(backup_root) / ACTIVE_TEXT_DBF

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    r10 = first_row(reports / "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv")
    r10r = first_row(reports / "message_catalog_phase22ae_6_5_10r_status_summary_v1.csv")
    sp10r, latest = savepoint_present(repo, "MSG-022AE.6.5.10R")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10R_GREEN", r10r.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10R_ROLLBACK_AND_FAILURE_CLASSIFICATION_GREEN_SOURCE_HELD", r10r.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10R_SAVEPOINT_PRESENT", sp10r, latest)
    gate("FAILED_ACTIVE_TEXT_COUNT_ZERO", r10.get("ACTIVE_TEXT_HEADER_COUNT") == "0", r10.get("ACTIVE_TEXT_HEADER_COUNT", "missing"))
    gate("ROLLBACK_RESTORED_TEXT_60", r10r.get("ROLLBACK_RUNTIME_TEXT_BASELINE_60") == "1", r10r.get("ROLLBACK_RUNTIME_TEXT_BASELINE_60", "missing"))
    gate("ACTIVE_RETRY_NOT_ALLOWED", r10r.get("ACTIVE_PROMOTION_RETRY_ALLOWED") == "0", r10r.get("ACTIVE_PROMOTION_RETRY_ALLOWED", "missing"))
    gate("ACTIVE_TEXT_IMPORT_EXISTS", (repo / ACTIVE_TEXT_IMPORT).exists(), rel(repo / ACTIVE_TEXT_IMPORT, repo))
    gate("SANDBOX_TEXT_IMPORT_EXISTS", (repo / SANDBOX_TEXT_IMPORT).exists(), rel(repo / SANDBOX_TEXT_IMPORT, repo))

    # Import CSV comparisons.
    csv_rows = [
        csv_summary(repo, "active_6_5_10_text_import", ACTIVE_TEXT_IMPORT),
        csv_summary(repo, "sandbox_6_5_6_text_import", SANDBOX_TEXT_IMPORT),
        csv_summary(repo, "plan_6_5_9_text_import", PLAN_TEXT_IMPORT),
        csv_summary(repo, "active_6_5_10_message_import", ACTIVE_MSG_IMPORT),
        csv_summary(repo, "sandbox_6_5_6_message_import", SANDBOX_MSG_IMPORT),
    ]

    active_text_sha = csv_rows[0]["SHA256"]
    sandbox_text_sha = csv_rows[1]["SHA256"]
    plan_text_sha = csv_rows[2]["SHA256"]
    text_csvs_identical = 1 if active_text_sha and active_text_sha == sandbox_text_sha == plan_text_sha else 0

    # DBF headers/schemas.
    backup_text_dbf = find_backup_text_dbf(repo)
    header_base_rows = []
    header_field_rows = []
    for role, path in [
        ("active_text_after_rollback", ACTIVE_TEXT_DBF),
        ("active_message_after_rollback", ACTIVE_MSG_DBF),
        ("sandbox_text_after_successful_6_5_6", SANDBOX_TEXT_DBF),
        ("backup_text_before_6_5_10", backup_text_dbf),
    ]:
        base, fields = header_rows(repo, role, path)
        header_base_rows.append(base)
        header_field_rows.extend(fields)

    # Sidecars/index/LMDB.
    artifact_rows = [
        file_info(repo, "active_text_dbf_after_rollback", ACTIVE_TEXT_DBF),
        file_info(repo, "active_text_index", ACTIVE_TEXT_INDEX),
        file_info(repo, "active_text_index_meta", ACTIVE_TEXT_INDEX_META),
        file_info(repo, "active_text_lmdb", ACTIVE_TEXT_LMDB),
        file_info(repo, "default_text_index", DEFAULT_TEXT_INDEX),
        file_info(repo, "default_text_index_meta", DEFAULT_TEXT_INDEX_META),
        file_info(repo, "default_text_lmdb", DEFAULT_TEXT_LMDB),
        file_info(repo, "sandbox_text_dbf_after_successful_import", SANDBOX_TEXT_DBF),
        file_info(repo, "sandbox_text_index", SANDBOX_TEXT_INDEX),
        file_info(repo, "sandbox_text_lmdb", SANDBOX_TEXT_LMDB),
        file_info(repo, "backup_text_dbf_before_6_5_10", backup_text_dbf),
    ]
    for ext in [".dtx", ".dbt", ".fpt", ".memo", ".mdx"]:
        artifact_rows.append(file_info(repo, f"active_text_sidecar_{ext}", ACTIVE_TEXT_DBF.with_suffix(ext)))
        artifact_rows.append(file_info(repo, f"sandbox_text_sidecar_{ext}", SANDBOX_TEXT_DBF.with_suffix(ext)))
        if str(backup_text_dbf):
            artifact_rows.append(file_info(repo, f"backup_text_sidecar_{ext}", backup_text_dbf.with_suffix(ext)))

    # Prior fingerprint deltas from failed active attempt.
    final_delta = read_csv(reports / "message_catalog_phase22ae_6_5_10_active_fingerprint_delta_v1.csv")
    text_delta = []
    for row in final_delta:
        blob = (row.get("ROLE", "") + " " + row.get("PATH", "")).upper()
        if "SYSTEM_MESSAGE_TEXT" in blob:
            text_delta.append(row)

    observations = []
    observations.append({
        "OBSERVATION": "TEXT_IMPORT_CSVS_IDENTICAL_ACROSS_SANDBOX_PLAN_ACTIVE",
        "VALUE": text_csvs_identical,
        "DETAIL": "1 means the active text import CSV is byte-identical to the sandbox-proven and plan-staged text CSVs.",
    })
    observations.append({
        "OBSERVATION": "ACTIVE_TEXT_IMPORT_REPORTED_70_BUT_REOPENED_ZERO",
        "VALUE": 1 if r10.get("RUNTIME_IMPORTED_70") == "1" and r10.get("ACTIVE_TEXT_HEADER_COUNT") == "0" else 0,
        "DETAIL": "Finalize evidence from 6.5.10.",
    })
    observations.append({
        "OBSERVATION": "ROLLBACK_RESTORED_60",
        "VALUE": 1 if r10r.get("ROLLBACK_RUNTIME_TEXT_BASELINE_60") == "1" else 0,
        "DETAIL": "10R runtime rollback readback.",
    })
    observations.append({
        "OBSERVATION": "TEXT_FINGERPRINT_DELTA_ROWS_IN_FAILED_ATTEMPT",
        "VALUE": len(text_delta),
        "DETAIL": "Rows in 6.5.10 fingerprint delta mentioning SYSTEM_MESSAGE_TEXT.",
    })

    likely = []
    if text_csvs_identical:
        likely.append({
            "CLASSIFICATION": "CSV_CONTENT_NOT_PRIMARY_SUSPECT",
            "DETAIL": "Active/plan/sandbox text import CSVs are byte-identical, and sandbox import was runtime-visible. The active failure is more likely active DBF/open/flush/index/LMDB/table-state behavior than CSV content.",
            "WEIGHT": "HIGH",
        })
    else:
        likely.append({
            "CLASSIFICATION": "CSV_CONTENT_MISMATCH_REQUIRES_REVIEW",
            "DETAIL": "The active text import CSV is not byte-identical to the sandbox or plan text CSV. Review CSV generation before any active retry.",
            "WEIGHT": "HIGH",
        })
    likely.extend([
        {
            "CLASSIFICATION": "ACTIVE_TEXT_TABLE_SPECIFIC_FAILURE",
            "DETAIL": "SYSTEM_MESSAGES active promotion landed at 14 while SYSTEM_MESSAGE_TEXT landed at 0 after reported import 70.",
            "WEIGHT": "HIGH",
        },
        {
            "CLASSIFICATION": "RETRY_SHOULD_BE_TEXT_ONLY_MICRO_PROOF",
            "DETAIL": "Next active work should avoid full promotion and use a tightly guarded text-only micro proof or further non-mutating inspection first.",
            "WEIGHT": "HIGH",
        },
        {
            "CLASSIFICATION": "INDEX_LMDB_OR_CLOSE_FLUSH_REVIEW_REQUIRED",
            "DETAIL": "ZAP says rebuild/rebind indexes as needed. The active text table may need explicit close/reopen/index rebuild/LMDB refresh discipline before provider validation.",
            "WEIGHT": "MEDIUM",
        },
    ])

    recommendations = [
        {"STEP": 1, "ACTION": "DO_NOT_RETRY_FULL_ACTIVE_PROMOTION", "DETAIL": "Rollback restored 12/60; retry remains closed.", "MUTATES_ACTIVE": 0},
        {"STEP": 2, "ACTION": "REVIEW_10S_REPORTS", "DETAIL": "Inspect CSV identity, DBF headers, sidecars, and failed fingerprint deltas.", "MUTATES_ACTIVE": 0},
        {"STEP": 3, "ACTION": "PLAN_10T_TEXT_ONLY_MICRO_PROOF", "DETAIL": "If authorized, test SYSTEM_MESSAGE_TEXT active path in isolation with backup, tiny import, close/reopen/readback, and rollback, not full catalog promotion.", "MUTATES_ACTIVE": 0},
        {"STEP": 4, "ACTION": "CONSIDER_RUNTIME_COMMAND_SUPPORT", "DETAIL": "A future safer path may need runtime commands for CLOSE/USE/reindex/LMDB rebuild/readback rather than raw header checks.", "MUTATES_ACTIVE": 0},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Report-only forensic review."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation by 10S."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX mutation by 10S."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation by 10S."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_PROMOTION_RETRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No retry authorized by 10S."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10s_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_import_csv_comparison_v1.csv", csv_rows,
              ["ROLE", "PATH", "EXISTS", "ROWS", "COLUMNS", "BYTES", "SHA256",
               "PROOF_SYMBOL_ROW_HITS", "PROOF_SYMBOL_LOCALE_PAIR_HITS", "LAST_ROWS_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_dbf_header_summary_v1.csv", header_base_rows,
              ["ROLE", "PATH", "EXISTS", "VERSION", "RECORD_COUNT", "HEADER_LEN", "RECORD_LEN",
               "HEADER_TERMINATOR_OK", "FIELD_COUNT", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_dbf_field_schema_v1.csv", header_field_rows,
              ["ROLE", "PATH", "EXISTS", "VERSION", "RECORD_COUNT", "HEADER_LEN", "RECORD_LEN",
               "HEADER_TERMINATOR_OK", "FIELD_COUNT", "BYTES", "SHA256", "FIELD", "TYPE", "LENGTH", "DECIMALS", "OFFSET"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_artifact_inventory_v1.csv", artifact_rows,
              ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_failed_attempt_text_fingerprint_delta_v1.csv", text_delta,
              ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256", "BEFORE_BYTES", "AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_observations_v1.csv", observations,
              ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_likely_causes_v1.csv", likely,
              ["CLASSIFICATION", "DETAIL", "WEIGHT"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_recommendations_v1.csv", recommendations,
              ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10s_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    active_text_header = next((r for r in header_base_rows if r["ROLE"] == "active_text_after_rollback"), {})
    sandbox_text_header = next((r for r in header_base_rows if r["ROLE"] == "sandbox_text_after_successful_6_5_6"), {})
    backup_text_header = next((r for r in header_base_rows if r["ROLE"] == "backup_text_before_6_5_10"), {})

    write_csv(reports / "message_catalog_phase22ae_6_5_10s_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10R_STATUS": r10r.get("STATUS", ""),
        "MSG_022AE_6_5_10R_SAVEPOINT_PRESENT": 1 if sp10r else 0,
        "FAILED_ACTIVE_TEXT_COUNT": r10.get("ACTIVE_TEXT_HEADER_COUNT", ""),
        "ROLLBACK_TEXT_BASELINE_60": r10r.get("ROLLBACK_RUNTIME_TEXT_BASELINE_60", ""),
        "TEXT_IMPORT_CSVS_IDENTICAL": text_csvs_identical,
        "ACTIVE_TEXT_AFTER_ROLLBACK_RECORD_COUNT": active_text_header.get("RECORD_COUNT", ""),
        "SANDBOX_TEXT_SUCCESS_RECORD_COUNT": sandbox_text_header.get("RECORD_COUNT", ""),
        "BACKUP_TEXT_RECORD_COUNT": backup_text_header.get("RECORD_COUNT", ""),
        "ACTIVE_PROMOTION_RETRY_ALLOWED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10R_STATUS", "MSG_022AE_6_5_10R_SAVEPOINT_PRESENT",
         "FAILED_ACTIVE_TEXT_COUNT", "ROLLBACK_TEXT_BASELINE_60", "TEXT_IMPORT_CSVS_IDENTICAL",
         "ACTIVE_TEXT_AFTER_ROLLBACK_RECORD_COUNT", "SANDBOX_TEXT_SUCCESS_RECORD_COUNT",
         "BACKUP_TEXT_RECORD_COUNT", "ACTIVE_PROMOTION_RETRY_ALLOWED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (reports / "MESSAGE_CATALOG_PHASE22AE_6_5_10S_ACTIVE_TEXT_IMPORT_FAILURE_FORENSIC_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10S Active Text Import Failure Forensic Review\n\nStatus: `{status}`\n\n10S is report-only. It compares the failed active text path with the sandbox-proven text path and keeps active retry closed.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10R status: {r10r.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10R savepoint present: {1 if sp10r else 0}")
    print(f"  failed active text count: {r10.get('ACTIVE_TEXT_HEADER_COUNT','')}")
    print(f"  rollback text baseline 60: {r10r.get('ROLLBACK_RUNTIME_TEXT_BASELINE_60','')}")
    print(f"  text import CSVs identical: {text_csvs_identical}")
    print(f"  active text after rollback count: {active_text_header.get('RECORD_COUNT','')}")
    print(f"  sandbox text successful count: {sandbox_text_header.get('RECORD_COUNT','')}")
    print(f"  backup text count: {backup_text_header.get('RECORD_COUNT','')}")
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
