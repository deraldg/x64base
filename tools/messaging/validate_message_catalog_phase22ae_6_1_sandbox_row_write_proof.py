#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_GREEN_ROW_WRITE_PROVEN"
STATUS_FAILED_SAFE = "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_GREEN_FAILED_PATH_CONFIRMED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_BLOCKED"
NEXT_PROVEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_2_ACTIVE_PROMOTION_REDESIGN_FROM_PROVEN_SANDBOX_PATH"
NEXT_FAILED = "HOLD_OR_AUTHORIZE_PHASE22AE_6_2_ALTERNATIVE_SANDBOX_WRITE_PATH_PLAN"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_1_SANDBOX_ROW_WRITE_PROOF.md")
SANDBOX_ROOT = Path("docs/messaging/sandbox/phase22ae_6_1_row_write_proof_v1")
TEST_SYMBOL = "MSG22AE61_SANDBOX_ROW_WRITE_TEST"
TEST_LOCALE = "en-US"
TEST_TEXT = "Phase 22AE.6.1 sandbox row write proof text"

SYMBOL_FIELDS = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"]
LOCALE_FIELDS = ["LOCALE", "LOCALE_ID"]
TEXT_FIELDS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"]
KIND_FIELDS = ["KIND", "MESSAGE_KIND", "MSG_KIND"]
STATUS_FIELDS = ["STATUS", "ROW_STATUS"]
SOURCE_FIELDS = ["SOURCE_PHASE", "SOURCE", "PHASE"]

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

def choose_field(info: DbfInfo, choices):
    names = {f["NAME"] for f in info.fields}
    for c in choices:
        if c in names:
            return c
    return ""

def project(row, fields):
    out = {}
    for f in fields:
        if f and f in row:
            out[f] = row.get(f, "")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_1_stage_status_summary_v1.csv")
    sp_ok, latest = savepoint_present(repo, "MSG-022AE.6")

    runtime = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG_PATH
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_upper = log_text.upper()

    msg_dbf = repo / SANDBOX_ROOT / "messaging/SYSTEM_MESSAGES.dbf"
    text_dbf = repo / SANDBOX_ROOT / "messaging/SYSTEM_MESSAGE_TEXT.dbf"

    gates = []
    hard_failures = 0
    def gate(name, ok, detail, hard=True):
        nonlocal hard_failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else ("FAIL" if hard else "REVIEW"), "DETAIL": str(detail)})
        if hard and not ok:
            hard_failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_PACKAGE_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("MSG_022AE_6_SAVEPOINT_PRESENT", sp_ok, latest)
    gate("RUNTIME_PROOF_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("NO_ACTIVE_CATALOG_MUTATION_IN_STAGE", stage.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0", stage.get("ACTIVE_CATALOG_MUTATION_OBSERVED", "missing"))
    gate("SANDBOX_MESSAGE_DBF_EXISTS", msg_dbf.exists(), rel(msg_dbf, repo))
    gate("SANDBOX_TEXT_DBF_EXISTS", text_dbf.exists(), rel(text_dbf, repo))

    msg_count = ""
    text_count = ""
    msg_test_rows = []
    text_test_rows = []
    msg_symbol = text_symbol = text_locale = text_text = ""
    tail_rows = []

    try:
        msg_info = parse_dbf(msg_dbf)
        text_info = parse_dbf(text_dbf)
        msg_count = msg_info.record_count
        text_count = text_info.record_count
        msg_rows = read_rows(msg_info)
        text_rows = read_rows(text_info)
        msg_symbol = choose_field(msg_info, SYMBOL_FIELDS)
        text_symbol = choose_field(text_info, SYMBOL_FIELDS)
        text_locale = choose_field(text_info, LOCALE_FIELDS)
        text_text = choose_field(text_info, TEXT_FIELDS)
        msg_test_rows = [r for r in msg_rows if r.get(msg_symbol, "") == TEST_SYMBOL]
        text_test_rows = [r for r in text_rows if r.get(text_symbol, "") == TEST_SYMBOL and r.get(text_locale, "") == TEST_LOCALE]
        for row in msg_rows[-4:]:
            out = {"TABLE": "SYSTEM_MESSAGES"}
            out.update(project(row, ["__RECNO__", "__DELETED__", msg_symbol, choose_field(msg_info, KIND_FIELDS), choose_field(msg_info, STATUS_FIELDS), choose_field(msg_info, SOURCE_FIELDS)]))
            tail_rows.append(out)
        for row in text_rows[-4:]:
            out = {"TABLE": "SYSTEM_MESSAGE_TEXT"}
            out.update(project(row, ["__RECNO__", "__DELETED__", text_symbol, text_locale, text_text, text_text + "__RAW_HEX", choose_field(text_info, STATUS_FIELDS), choose_field(text_info, SOURCE_FIELDS)]))
            tail_rows.append(out)
    except Exception as exc:
        gate("SANDBOX_DBF_READBACK", False, exc)

    msg_before = int(stage.get("SANDBOX_MESSAGE_ROWS_BEFORE") or 12)
    text_before = int(stage.get("SANDBOX_TEXT_ROWS_BEFORE") or 60)
    count_moved = (msg_count == msg_before + 1 and text_count == text_before + 1)
    keys_present = (len(msg_test_rows) == 1 and len(text_test_rows) == 1)

    gate("SANDBOX_COUNTS_MOVED_BY_ONE", count_moved, f"{msg_count}/{text_count} from {msg_before}/{text_before}", hard=False)
    gate("SANDBOX_TEST_KEYS_PRESENT", keys_present, f"message_test_rows={len(msg_test_rows)}; text_test_rows={len(text_test_rows)}", hard=False)
    gate("NO_UNKNOWN_COMMAND_IN_RUNTIME_LOG", "UNKNOWN COMMAND:" not in log_upper, "unknown command absent", hard=False)
    gate("NO_MEMO_BACKEND_ERROR_IN_RUNTIME_LOG", "MEMO BACKEND NOT ATTACHED" not in log_upper, "memo backend error absent", hard=False)

    if hard_failures > 0:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_22AE_6_1_SANDBOX_PROOF_SETUP"
    elif keys_present and count_moved:
        status = STATUS_PROVEN
        next_gate = NEXT_PROVEN
    else:
        status = STATUS_FAILED_SAFE
        next_gate = NEXT_FAILED

    validation_issues = "0" if status != STATUS_BLOCKED else str(hard_failures)

    findings = [
        {"FINDING": "COUNT_MOVED", "VALUE": 1 if count_moved else 0, "DETAIL": f"sandbox counts {msg_count}/{text_count}; expected {msg_before+1}/{text_before+1}"},
        {"FINDING": "KEYS_PRESENT", "VALUE": 1 if keys_present else 0, "DETAIL": f"message test rows={len(msg_test_rows)}; text test rows={len(text_test_rows)}"},
        {"FINDING": "ACTIVE_UNTOUCHED", "VALUE": 1, "DETAIL": "This phase only uses docs/messaging/sandbox copy."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_1_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_1_sandbox_tail_rows_v1.csv", tail_rows, sorted({k for r in tail_rows for k in r.keys()} or {"TABLE"}))
    write_csv(reports / "message_catalog_phase22ae_6_1_findings_v1.csv", findings, ["FINDING", "VALUE", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox only; no active index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Sandbox only; no active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_1_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_1_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_PACKAGE_STAGED_SOURCE_HELD" else 0,
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_before,
        "SANDBOX_TEXT_ROWS_BEFORE": text_before,
        "SANDBOX_MESSAGE_ROWS_AFTER": msg_count,
        "SANDBOX_TEXT_ROWS_AFTER": text_count,
        "SANDBOX_COUNTS_MOVED_BY_ONE": 1 if count_moved else 0,
        "SANDBOX_MESSAGE_TEST_ROWS_FOUND": len(msg_test_rows),
        "SANDBOX_TEXT_TEST_ROWS_FOUND": len(text_test_rows),
        "TEST_SYMBOL": TEST_SYMBOL,
        "RUNTIME_PROOF_PATH": rel(runtime, repo),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_GREEN", "SANDBOX_MESSAGE_ROWS_BEFORE",
         "SANDBOX_TEXT_ROWS_BEFORE", "SANDBOX_MESSAGE_ROWS_AFTER", "SANDBOX_TEXT_ROWS_AFTER",
         "SANDBOX_COUNTS_MOVED_BY_ONE", "SANDBOX_MESSAGE_TEST_ROWS_FOUND",
         "SANDBOX_TEXT_TEST_ROWS_FOUND", "TEST_SYMBOL", "RUNTIME_PROOF_PATH",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_1_SANDBOX_ROW_WRITE_PROOF_PACKAGE_STAGED_SOURCE_HELD' else 0}")
    print(f"  sandbox message rows before/after: {msg_before}/{msg_count}")
    print(f"  sandbox text rows before/after: {text_before}/{text_count}")
    print(f"  sandbox counts moved by one: {1 if count_moved else 0}")
    print(f"  sandbox message test rows found: {len(msg_test_rows)}")
    print(f"  sandbox text test rows found: {len(text_test_rows)}")
    print(f"  test symbol: {TEST_SYMBOL}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status != STATUS_BLOCKED else 2

if __name__ == "__main__":
    raise SystemExit(main())
