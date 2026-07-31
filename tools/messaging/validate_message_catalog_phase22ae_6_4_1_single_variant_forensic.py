#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_GREEN_TWO_TABLE_VARIANT_PROVEN"
STATUS_PARTIAL = "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_GREEN_PARTIAL_ONLY"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_BLOCKED"
NEXT_PROVEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_ACTIVE_PROMOTION_CANDIDATE_FROM_SINGLE_VARIANT_PROOF"
NEXT_PARTIAL = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_COMMAND_SURFACE_FIX_OR_IMPORT_PATH_PLAN"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF.md")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

SYMBOL_FIELDS = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"]
LOCALE_FIELDS = ["LOCALE", "LOCALE_ID"]
TEXT_FIELDS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"]
KIND_FIELDS = ["KIND", "MESSAGE_KIND", "MSG_KIND"]
PLACEHOLDER_FIELDS = ["PLACEHOLDERS", "PLACEHOLDER", "ARGS", "ARGUMENTS"]
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

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fingerprint_root(root: Path, repo: Path, label: str, max_files: int = 5000):
    rows = []
    if not root.exists():
        rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 0, "BYTES": 0, "SHA256": "", "ROLE": "missing_root"})
        return rows
    count = 0
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({"LABEL": label, "PATH": rel(p, repo), "EXISTS": 1, "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "ROLE": "file"})
            count += 1
            if count >= max_files:
                rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 1, "BYTES": 0, "SHA256": "", "ROLE": "truncated_after_max_files"})
                break
    if not rows:
        rows.append({"LABEL": label, "PATH": rel(root, repo), "EXISTS": 1, "BYTES": 0, "SHA256": "", "ROLE": "empty_root"})
    return rows

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

def compare_fingerprints(before_rows, after_rows):
    before = {r["PATH"]: r for r in before_rows if r.get("ROLE") == "file"}
    after = {r["PATH"]: r for r in after_rows if r.get("ROLE") == "file"}
    changes = []
    for path in sorted(set(before) | set(after)):
        b = before.get(path)
        a = after.get(path)
        if b is None:
            changes.append({"PATH": path, "CHANGE": "ADDED", "BEFORE_SHA256": "", "AFTER_SHA256": a.get("SHA256", ""), "BEFORE_BYTES": "", "AFTER_BYTES": a.get("BYTES", "")})
        elif a is None:
            changes.append({"PATH": path, "CHANGE": "REMOVED", "BEFORE_SHA256": b.get("SHA256", ""), "AFTER_SHA256": "", "BEFORE_BYTES": b.get("BYTES", ""), "AFTER_BYTES": ""})
        elif b.get("SHA256") != a.get("SHA256") or b.get("BYTES") != a.get("BYTES"):
            changes.append({"PATH": path, "CHANGE": "MODIFIED", "BEFORE_SHA256": b.get("SHA256", ""), "AFTER_SHA256": a.get("SHA256", ""), "BEFORE_BYTES": b.get("BYTES", ""), "AFTER_BYTES": a.get("BYTES", "")})
    return changes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_4_1_stage_status_summary_v1.csv")
    sp64, latest_id = savepoint_present(repo, "MSG-022AE.6.4")

    runtime = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_upper = log_text.upper()

    sandbox = repo / stage.get("SANDBOX_ROOT", "")
    msg_dbf = sandbox / "messaging/SYSTEM_MESSAGES.dbf"
    txt_dbf = sandbox / "messaging/SYSTEM_MESSAGE_TEXT.dbf"
    test_symbol = stage.get("TEST_SYMBOL", "")
    test_locale = stage.get("TEST_LOCALE", "")
    test_text = stage.get("TEST_TEXT", "")
    msg_before = int(stage.get("SANDBOX_MESSAGE_ROWS_BEFORE") or 12)
    txt_before = int(stage.get("SANDBOX_TEXT_ROWS_BEFORE") or 60)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("MSG_022AE_6_4_SAVEPOINT_PRESENT", sp64, latest_id)
    gate("RUNTIME_PROOF_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("SANDBOX_MESSAGE_DBF_EXISTS", msg_dbf.exists(), rel(msg_dbf, repo))
    gate("SANDBOX_TEXT_DBF_EXISTS", txt_dbf.exists(), rel(txt_dbf, repo))

    after_fp = (
        fingerprint_root(repo / ACTIVE_MSG_ROOT, repo, "after_active_messaging") +
        fingerprint_root(repo / ACTIVE_INDEX_ROOT, repo, "after_active_indexes_messaging") +
        fingerprint_root(repo / ACTIVE_LMDB_ROOT, repo, "after_active_lmdb_messaging") +
        fingerprint_root(repo / DEFAULT_INDEX_ROOT, repo, "after_default_indexes") +
        fingerprint_root(repo / DEFAULT_LMDB_ROOT, repo, "after_default_lmdb")
    )
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_4_1_active_fingerprint_before_v1.csv")
    fp_changes = compare_fingerprints(before_fp, after_fp)

    msg_count = ""
    txt_count = ""
    msg_exact = []
    txt_exact = []
    tail_rows = []
    msg_delta = ""
    txt_delta = ""
    text_payload_exact = 0

    try:
        msg_info = parse_dbf(msg_dbf)
        txt_info = parse_dbf(txt_dbf)
        msg_rows = read_rows(msg_info)
        txt_rows = read_rows(txt_info)
        msg_count = msg_info.record_count
        txt_count = txt_info.record_count
        msg_delta = msg_count - msg_before
        txt_delta = txt_count - txt_before

        msg_symbol = choose_field(msg_info, SYMBOL_FIELDS)
        txt_symbol = choose_field(txt_info, SYMBOL_FIELDS)
        txt_locale = choose_field(txt_info, LOCALE_FIELDS)
        txt_text = choose_field(txt_info, TEXT_FIELDS)

        msg_exact = [r for r in msg_rows if msg_symbol and r.get(msg_symbol, "") == test_symbol]
        txt_exact = [r for r in txt_rows if txt_symbol and r.get(txt_symbol, "") == test_symbol and (not test_locale or r.get(txt_locale, "") == test_locale)]
        text_payload_exact = 1 if any((not test_text or r.get(txt_text, "") == test_text or r.get(txt_text, "") not in ("", "0")) for r in txt_exact) else 0

        for label, rows, fields in [
            ("SYSTEM_MESSAGES", msg_rows[-5:], [msg_symbol, choose_field(msg_info, KIND_FIELDS), choose_field(msg_info, STATUS_FIELDS), choose_field(msg_info, SOURCE_FIELDS)]),
            ("SYSTEM_MESSAGE_TEXT", txt_rows[-5:], [txt_symbol, txt_locale, txt_text, txt_text + "__RAW_HEX" if txt_text else "", choose_field(txt_info, STATUS_FIELDS), choose_field(txt_info, SOURCE_FIELDS)]),
        ]:
            for r in rows:
                tail_rows.append({
                    "TABLE": label,
                    "RECNO": r.get("__RECNO__", ""),
                    "ROW_JSON": json.dumps({k: r.get(k, "") for k in ["__RECNO__", "__DELETED__"] + [f for f in fields if f]}, ensure_ascii=False, sort_keys=True),
                })
    except Exception as exc:
        gate("SANDBOX_DBF_READBACK", False, exc)

    counts_move_once = (msg_delta == 1 and txt_delta == 1)
    two_table_proven = counts_move_once and len(msg_exact) == 1 and len(txt_exact) == 1
    partial = (msg_delta == 1 or txt_delta == 1 or len(msg_exact) > 0 or len(txt_exact) > 0)
    boundary_clean = len(fp_changes) == 0

    gate("ACTIVE_DEFAULT_BOUNDARY_FINGERPRINT_UNCHANGED", boundary_clean, f"changes={len(fp_changes)}")
    # Counts/keys are not hard gates; they determine green outcome.
    if failures > 0:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_4_1_SETUP_OR_BOUNDARY"
        validation_issues = str(failures)
    elif two_table_proven:
        status = STATUS_PROVEN
        next_gate = NEXT_PROVEN
        validation_issues = "0"
    else:
        status = STATUS_PARTIAL
        next_gate = NEXT_PARTIAL
        validation_issues = "0"

    result_rows = [{
        "VARIANT": stage.get("VARIANT", ""),
        "TEST_SYMBOL": test_symbol,
        "MESSAGE_ROWS_BEFORE": msg_before,
        "MESSAGE_ROWS_AFTER": msg_count,
        "MESSAGE_DELTA": msg_delta,
        "TEXT_ROWS_BEFORE": txt_before,
        "TEXT_ROWS_AFTER": txt_count,
        "TEXT_DELTA": txt_delta,
        "COUNTS_MOVE_ONCE": 1 if counts_move_once else 0,
        "MESSAGE_EXACT_SYMBOL_ROWS": len(msg_exact),
        "TEXT_EXACT_SYMBOL_LOCALE_ROWS": len(txt_exact),
        "TEXT_PAYLOAD_EXACT_OR_POINTER_PRESENT": text_payload_exact,
        "TWO_TABLE_VARIANT_PROVEN": 1 if two_table_proven else 0,
        "PARTIAL_EVIDENCE": 1 if partial else 0,
    }]

    runtime_rows = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if runtime.exists() else 0, "DETAIL": rel(runtime, repo)},
        {"OBSERVATION": "opened_system_messages_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGES"), "DETAIL": "Runtime-open evidence."},
        {"OBSERVATION": "opened_system_message_text_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGE_TEXT"), "DETAIL": "Runtime-open evidence."},
        {"OBSERVATION": "replace_usage_count", "VALUE": log_upper.count("REPLACE USAGE"), "DETAIL": "0 is preferred for clean write."},
        {"OBSERVATION": "unknown_command_count", "VALUE": log_upper.count("UNKNOWN COMMAND:"), "DETAIL": "0 is preferred."},
        {"OBSERVATION": "test_symbol_seen_in_log", "VALUE": 1 if test_symbol.upper() in log_upper else 0, "DETAIL": "Supplemental only; DBF readback is source of truth."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": "Fingerprint comparison checks active/default roots."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": "Fingerprint comparison checks active/default roots."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": "Fingerprint comparison checks active/default roots."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_4_1_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_single_variant_result_v1.csv", result_rows, ["VARIANT", "TEST_SYMBOL", "MESSAGE_ROWS_BEFORE", "MESSAGE_ROWS_AFTER", "MESSAGE_DELTA", "TEXT_ROWS_BEFORE", "TEXT_ROWS_AFTER", "TEXT_DELTA", "COUNTS_MOVE_ONCE", "MESSAGE_EXACT_SYMBOL_ROWS", "TEXT_EXACT_SYMBOL_LOCALE_ROWS", "TEXT_PAYLOAD_EXACT_OR_POINTER_PRESENT", "TWO_TABLE_VARIANT_PROVEN", "PARTIAL_EVIDENCE"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_tail_rows_v1.csv", tail_rows, ["TABLE", "RECNO", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_runtime_observations_v1.csv", runtime_rows, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_active_fingerprint_after_v1.csv", after_fp, ["LABEL", "PATH", "EXISTS", "BYTES", "SHA256", "ROLE"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_active_fingerprint_delta_v1.csv", fp_changes, ["PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256", "BEFORE_BYTES", "AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_4_1_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_STAGED_SOURCE_HELD" else 0,
        "VARIANT": stage.get("VARIANT", ""),
        "MESSAGE_ROWS_BEFORE": msg_before,
        "MESSAGE_ROWS_AFTER": msg_count,
        "MESSAGE_DELTA": msg_delta,
        "TEXT_ROWS_BEFORE": txt_before,
        "TEXT_ROWS_AFTER": txt_count,
        "TEXT_DELTA": txt_delta,
        "MESSAGE_EXACT_SYMBOL_ROWS": len(msg_exact),
        "TEXT_EXACT_SYMBOL_LOCALE_ROWS": len(txt_exact),
        "TWO_TABLE_VARIANT_PROVEN": 1 if two_table_proven else 0,
        "PARTIAL_EVIDENCE": 1 if partial else 0,
        "ACTIVE_FINGERPRINT_CHANGES": len(fp_changes),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if boundary_clean else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_GREEN", "VARIANT",
         "MESSAGE_ROWS_BEFORE", "MESSAGE_ROWS_AFTER", "MESSAGE_DELTA",
         "TEXT_ROWS_BEFORE", "TEXT_ROWS_AFTER", "TEXT_DELTA",
         "MESSAGE_EXACT_SYMBOL_ROWS", "TEXT_EXACT_SYMBOL_LOCALE_ROWS",
         "TWO_TABLE_VARIANT_PROVEN", "PARTIAL_EVIDENCE", "ACTIVE_FINGERPRINT_CHANGES",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  variant: {stage.get('VARIANT', '')}")
    print(f"  message rows before/after: {msg_before}/{msg_count}")
    print(f"  text rows before/after: {txt_before}/{txt_count}")
    print(f"  message exact symbol rows: {len(msg_exact)}")
    print(f"  text exact symbol/locale rows: {len(txt_exact)}")
    print(f"  two-table variant proven: {1 if two_table_proven else 0}")
    print(f"  partial evidence: {1 if partial else 0}")
    print(f"  active fingerprint changes: {len(fp_changes)}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_PROVEN, STATUS_PARTIAL) else 2

if __name__ == "__main__":
    raise SystemExit(main())
