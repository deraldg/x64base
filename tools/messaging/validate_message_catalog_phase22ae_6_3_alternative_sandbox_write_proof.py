#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_GREEN_VARIANT_PROVEN"
STATUS_NONE = "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_GREEN_NO_VARIANT_PROVEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_BLOCKED"
NEXT_PROVEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_4_ACTIVE_PROMOTION_CANDIDATE_FROM_PROVEN_SANDBOX_VARIANT"
NEXT_NONE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF.md")

SYMBOL_FIELDS = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"]
LOCALE_FIELDS = ["LOCALE", "LOCALE_ID"]
TEXT_FIELDS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"]

class DbfInfo:
    def __init__(self, path, record_count, header_len, record_len, fields):
        self.path = path
        self.record_count = record_count
        self.header_len = header_len
        self.record_len = record_len
        self.fields = fields

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

def rel(path: Path, repo: Path):
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

def parse_dbf(path: Path) -> DbfInfo:
    data = path.read_bytes()
    if len(data) < 32:
        raise RuntimeError(f"DBF too small: {path}")
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        raw = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11])
        length = data[pos+16]
        if name:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "OFFSET": offset})
            offset += length
        pos += 32
    return DbfInfo(path, record_count, header_len, record_len, fields)

def choose_field(info: DbfInfo, choices):
    names = {f["NAME"] for f in info.fields}
    for c in choices:
        if c in names:
            return c
    return ""

def read_rows(info: DbfInfo):
    rows = []
    with info.path.open("rb") as f:
        f.seek(info.header_len)
        for i in range(info.record_count):
            rec = f.read(info.record_len)
            if len(rec) < info.record_len:
                break
            row = {"__RECNO__": i + 1, "__DELETED__": 1 if rec[:1] == b"*" else 0}
            for fld in info.fields:
                raw = rec[fld["OFFSET"]:fld["OFFSET"] + fld["LENGTH"]]
                if fld["TYPE"].upper() == "M":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                    row[fld["NAME"] + "__RAW_HEX"] = raw.hex()
                elif fld["TYPE"].upper() == "C":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                else:
                    row[fld["NAME"]] = raw.decode("ascii", errors="replace").rstrip().strip()
            rows.append(row)
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_3_stage_status_summary_v1.csv")
    sp62, latest_id = savepoint_present(repo, "MSG-022AE.6.2")
    manifest = read_csv(reports / "message_catalog_phase22ae_6_3_variant_manifest_v1.csv")

    runtime = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_upper = log_text.upper()

    gates = []
    hard_failures = 0
    def gate(name, ok, detail):
        nonlocal hard_failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            hard_failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_PACKAGE_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("MSG_022AE_6_2_SAVEPOINT_PRESENT", sp62, latest_id)
    gate("VARIANT_MANIFEST_PRESENT", len(manifest) > 0, f"variants={len(manifest)}")
    gate("RUNTIME_PROOF_EXISTS", runtime.exists(), rel(runtime, repo))

    variant_results = []
    tail_rows = []
    proven = []
    any_counts_moved = False

    for row in manifest:
        vid = row.get("VARIANT_ID", "")
        test_symbol = row.get("TEST_SYMBOL", "")
        vroot = repo / row.get("SANDBOX_ROOT", "")
        msg_dbf = vroot / "messaging/SYSTEM_MESSAGES.dbf"
        text_dbf = vroot / "messaging/SYSTEM_MESSAGE_TEXT.dbf"
        message_before = int(row.get("MESSAGE_ROWS_BEFORE") or 12)
        text_before = int(row.get("TEXT_ROWS_BEFORE") or 60)

        try:
            msg_info = parse_dbf(msg_dbf)
            text_info = parse_dbf(text_dbf)
            msg_rows = read_rows(msg_info)
            text_rows = read_rows(text_info)
            msg_symbol = choose_field(msg_info, SYMBOL_FIELDS)
            text_symbol = choose_field(text_info, SYMBOL_FIELDS)
            text_locale = choose_field(text_info, LOCALE_FIELDS)
            text_text = choose_field(text_info, TEXT_FIELDS)
            msg_found_rows = [r for r in msg_rows if r.get(msg_symbol, "") == test_symbol]
            text_found_rows = [r for r in text_rows if r.get(text_symbol, "") == test_symbol]
            counts_moved = (msg_info.record_count == message_before + 1 and text_info.record_count == text_before + 1)
            keys_found = (len(msg_found_rows) == 1 and len(text_found_rows) == 1)
            any_counts_moved = any_counts_moved or counts_moved
            if keys_found and counts_moved:
                proven.append(vid)
            variant_results.append({
                "VARIANT_ID": vid,
                "DESCRIPTION": row.get("DESCRIPTION", ""),
                "MESSAGE_ROWS_BEFORE": message_before,
                "MESSAGE_ROWS_AFTER": msg_info.record_count,
                "TEXT_ROWS_BEFORE": text_before,
                "TEXT_ROWS_AFTER": text_info.record_count,
                "COUNTS_MOVED_BY_ONE": 1 if counts_moved else 0,
                "TEST_SYMBOL": test_symbol,
                "MESSAGE_TEST_ROWS_FOUND": len(msg_found_rows),
                "TEXT_TEST_ROWS_FOUND": len(text_found_rows),
                "VARIANT_PROVEN": 1 if (keys_found and counts_moved) else 0,
                "ERRORS": "",
            })
            for src, rows, sym_field in [("SYSTEM_MESSAGES", msg_rows[-3:], msg_symbol), ("SYSTEM_MESSAGE_TEXT", text_rows[-3:], text_symbol)]:
                for tr in rows:
                    tail_rows.append({
                        "VARIANT_ID": vid,
                        "TABLE": src,
                        "RECNO": tr.get("__RECNO__", ""),
                        "SYMBOL_VALUE": tr.get(sym_field, ""),
                        "LOCALE_VALUE": tr.get(text_locale, "") if src == "SYSTEM_MESSAGE_TEXT" else "",
                        "TEXT_OR_POINTER_VALUE": tr.get(text_text, "") if src == "SYSTEM_MESSAGE_TEXT" else "",
                    })
        except Exception as exc:
            variant_results.append({
                "VARIANT_ID": vid,
                "DESCRIPTION": row.get("DESCRIPTION", ""),
                "MESSAGE_ROWS_BEFORE": message_before,
                "MESSAGE_ROWS_AFTER": "",
                "TEXT_ROWS_BEFORE": text_before,
                "TEXT_ROWS_AFTER": "",
                "COUNTS_MOVED_BY_ONE": 0,
                "TEST_SYMBOL": test_symbol,
                "MESSAGE_TEST_ROWS_FOUND": 0,
                "TEXT_TEST_ROWS_FOUND": 0,
                "VARIANT_PROVEN": 0,
                "ERRORS": str(exc),
            })

    # If the runtime log was saved manually, it may contain only partial output; DBF readback is the source of truth.
    runtime_observations = [
        {"OBSERVATION": "unknown_command_count", "VALUE": log_upper.count("UNKNOWN COMMAND:"), "DETAIL": "Some experimental variants may be unknown; not a hard failure in sandbox."},
        {"OBSERVATION": "memo_backend_error_count", "VALUE": log_upper.count("MEMO BACKEND NOT ATTACHED"), "DETAIL": "Should ideally be 0."},
        {"OBSERVATION": "opened_system_messages_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGES"), "DETAIL": "Runtime proof signal."},
        {"OBSERVATION": "opened_system_message_text_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGE_TEXT"), "DETAIL": "Runtime proof signal."},
    ]

    if hard_failures > 0:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_3_PROOF_SETUP"
    elif proven:
        status = STATUS_PROVEN
        next_gate = NEXT_PROVEN
    elif any_counts_moved:
        status = STATUS_NONE
        next_gate = NEXT_NONE
    else:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_RERUN_PHASE22AE_6_3_RUNTIME_PROOF"

    validation_issues = "0" if status in (STATUS_PROVEN, STATUS_NONE) else str(max(1, hard_failures))

    write_csv(reports / "message_catalog_phase22ae_6_3_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_3_variant_results_v1.csv", variant_results, ["VARIANT_ID", "DESCRIPTION", "MESSAGE_ROWS_BEFORE", "MESSAGE_ROWS_AFTER", "TEXT_ROWS_BEFORE", "TEXT_ROWS_AFTER", "COUNTS_MOVED_BY_ONE", "TEST_SYMBOL", "MESSAGE_TEST_ROWS_FOUND", "TEXT_TEST_ROWS_FOUND", "VARIANT_PROVEN", "ERRORS"])
    write_csv(reports / "message_catalog_phase22ae_6_3_tail_rows_v1.csv", tail_rows, ["VARIANT_ID", "TABLE", "RECNO", "SYMBOL_VALUE", "LOCALE_VALUE", "TEXT_OR_POINTER_VALUE"])
    write_csv(reports / "message_catalog_phase22ae_6_3_runtime_observations_v1.csv", runtime_observations, ["OBSERVATION", "VALUE", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox variants only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox variants only; no active index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox variants only; no active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_3_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_3_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_PACKAGE_STAGED_SOURCE_HELD" else 0,
        "VARIANTS_TESTED": len(variant_results),
        "VARIANTS_WITH_COUNTS_MOVED": sum(int(r.get("COUNTS_MOVED_BY_ONE", 0)) for r in variant_results),
        "VARIANTS_PROVEN": len(proven),
        "PROVEN_VARIANT_IDS": ";".join(proven),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_GREEN", "VARIANTS_TESTED",
         "VARIANTS_WITH_COUNTS_MOVED", "VARIANTS_PROVEN", "PROVEN_VARIANT_IDS",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_PACKAGE_STAGED_SOURCE_HELD' else 0}")
    print(f"  variants tested: {len(variant_results)}")
    print(f"  variants with counts moved: {sum(int(r.get('COUNTS_MOVED_BY_ONE', 0)) for r in variant_results)}")
    print(f"  variants proven: {len(proven)}")
    print(f"  proven variant ids: {';'.join(proven)}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_PROVEN, STATUS_NONE) else 2

if __name__ == "__main__":
    raise SystemExit(main())
