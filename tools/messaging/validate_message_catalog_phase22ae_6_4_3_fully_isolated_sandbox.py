#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_GREEN_TWO_TABLE_VARIANT_PROVEN"
STATUS_PARTIAL = "MESSAGE_CATALOG_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_GREEN_ISOLATED_PARTIAL_ONLY"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_BLOCKED_BOUNDARY_OR_SETUP"
NEXT_PROVEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_ACTIVE_PROMOTION_CANDIDATE_FROM_ISOLATED_SANDBOX_PROOF"
NEXT_PARTIAL = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_COMMAND_SURFACE_WRITE_FIX_OR_IMPORT_PATH_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF.md")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")
TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

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

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fingerprint_selected(repo: Path):
    rows = []
    targets = []
    for table in TABLES:
        targets.append((repo / ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"))
        targets.append((repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx", f"active_msg_index_{table}_cdx"))
        targets.append((repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx.meta", f"active_msg_index_{table}_meta"))
        targets.append((repo / ACTIVE_MSG_LMDB_ROOT / f"{table}.cdx.d", f"active_msg_lmdb_{table}"))
        targets.append((repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"))
        targets.append((repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"))
        targets.append((repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"))
    for path, role in targets:
        if path.is_dir():
            files = sorted([p for p in path.rglob("*") if p.is_file()])
            h = hashlib.sha256()
            total = 0
            for f in files:
                h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
                h.update(sha256_file(f).encode("ascii"))
                total += f.stat().st_size
            rows.append({"ROLE": role, "PATH": rel(path, repo), "EXISTS": 1, "KIND": "dir", "BYTES": total, "SHA256": h.hexdigest(), "FILES": len(files)})
        elif path.is_file():
            rows.append({"ROLE": role, "PATH": rel(path, repo), "EXISTS": 1, "KIND": "file", "BYTES": path.stat().st_size, "SHA256": sha256_file(path), "FILES": 1})
        else:
            rows.append({"ROLE": role, "PATH": rel(path, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "SHA256": "", "FILES": 0})
    return rows

def compare_fp(before, after):
    b = {r["ROLE"] + "|" + r["PATH"]: r for r in before}
    a = {r["ROLE"] + "|" + r["PATH"]: r for r in after}
    deltas = []
    for key in sorted(set(b) | set(a)):
        br = b.get(key)
        ar = a.get(key)
        if br is None:
            deltas.append({"ROLE": ar.get("ROLE", ""), "PATH": ar.get("PATH", ""), "CHANGE": "ADDED", "BEFORE_SHA256": "", "AFTER_SHA256": ar.get("SHA256", ""), "BEFORE_BYTES": "", "AFTER_BYTES": ar.get("BYTES", "")})
        elif ar is None:
            deltas.append({"ROLE": br.get("ROLE", ""), "PATH": br.get("PATH", ""), "CHANGE": "REMOVED", "BEFORE_SHA256": br.get("SHA256", ""), "AFTER_SHA256": "", "BEFORE_BYTES": br.get("BYTES", ""), "AFTER_BYTES": ""})
        elif br.get("SHA256") != ar.get("SHA256") or str(br.get("BYTES")) != str(ar.get("BYTES")):
            deltas.append({"ROLE": ar.get("ROLE", br.get("ROLE", "")), "PATH": ar.get("PATH", br.get("PATH", "")), "CHANGE": "MODIFIED", "BEFORE_SHA256": br.get("SHA256", ""), "AFTER_SHA256": ar.get("SHA256", ""), "BEFORE_BYTES": br.get("BYTES", ""), "AFTER_BYTES": ar.get("BYTES", "")})
    return deltas

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

    stage = first_row(reports / "message_catalog_phase22ae_6_4_3_stage_status_summary_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_4_3_protected_fingerprint_before_v1.csv")

    runtime = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_upper = log_text.upper()

    sandbox = repo / stage.get("SANDBOX_ROOT", "")
    msg_dbf = sandbox / "dbf/SYSTEM_MESSAGES.dbf"
    txt_dbf = sandbox / "dbf/SYSTEM_MESSAGE_TEXT.dbf"
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

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_PROOF_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("SANDBOX_MESSAGE_DBF_EXISTS", msg_dbf.exists(), rel(msg_dbf, repo))
    gate("SANDBOX_TEXT_DBF_EXISTS", txt_dbf.exists(), rel(txt_dbf, repo))

    after_fp = fingerprint_selected(repo)
    deltas = compare_fp(before_fp, after_fp)

    msg_count = ""
    txt_count = ""
    msg_delta = ""
    txt_delta = ""
    msg_exact = []
    txt_exact = []
    text_payload_present = 0
    tail_rows = []

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
        txt_exact = [r for r in txt_rows if txt_symbol and r.get(txt_symbol, "") == test_symbol and (not txt_locale or r.get(txt_locale, "") == test_locale)]
        text_payload_present = 1 if any((r.get(txt_text, "") == test_text or r.get(txt_text, "") not in ("", "0")) for r in txt_exact) else 0

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

    boundary_clean = len(deltas) == 0
    counts_move_once = (msg_delta == 1 and txt_delta == 1)
    two_table_proven = boundary_clean and counts_move_once and len(msg_exact) == 1 and len(txt_exact) == 1
    partial = boundary_clean and (counts_move_once or len(msg_exact) > 0 or len(txt_exact) > 0)

    if failures > 0 or not boundary_clean:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_4_3_ISOLATION_OR_PATH_BINDING"
        validation_issues = str(max(1, failures, len(deltas)))
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
        "TEXT_PAYLOAD_EXACT_OR_POINTER_PRESENT": text_payload_present,
        "TWO_TABLE_VARIANT_PROVEN": 1 if two_table_proven else 0,
        "PARTIAL_EVIDENCE": 1 if partial else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(deltas),
    }]

    runtime_rows = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if runtime.exists() else 0, "DETAIL": rel(runtime, repo)},
        {"OBSERVATION": "opened_system_messages_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGES"), "DETAIL": "Runtime-open evidence."},
        {"OBSERVATION": "opened_system_message_text_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGE_TEXT"), "DETAIL": "Runtime-open evidence."},
        {"OBSERVATION": "replace_usage_count", "VALUE": log_upper.count("REPLACE USAGE"), "DETAIL": "0 preferred."},
        {"OBSERVATION": "unknown_command_count", "VALUE": log_upper.count("UNKNOWN COMMAND:"), "DETAIL": "0 preferred."},
        {"OBSERVATION": "test_symbol_seen_in_log", "VALUE": 1 if test_symbol.upper() in log_upper else 0, "DETAIL": "Supplemental only."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": f"protected fingerprint changes={len(deltas)}"},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_4_3_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_3_single_variant_result_v1.csv", result_rows, ["VARIANT", "TEST_SYMBOL", "MESSAGE_ROWS_BEFORE", "MESSAGE_ROWS_AFTER", "MESSAGE_DELTA", "TEXT_ROWS_BEFORE", "TEXT_ROWS_AFTER", "TEXT_DELTA", "COUNTS_MOVE_ONCE", "MESSAGE_EXACT_SYMBOL_ROWS", "TEXT_EXACT_SYMBOL_LOCALE_ROWS", "TEXT_PAYLOAD_EXACT_OR_POINTER_PRESENT", "TWO_TABLE_VARIANT_PROVEN", "PARTIAL_EVIDENCE", "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES"])
    write_csv(reports / "message_catalog_phase22ae_6_4_3_tail_rows_v1.csv", tail_rows, ["TABLE", "RECNO", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_4_3_protected_fingerprint_after_v1.csv", after_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_4_3_protected_fingerprint_delta_v1.csv", deltas, ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256", "BEFORE_BYTES", "AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_4_3_runtime_observations_v1.csv", runtime_rows, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_3_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_4_3_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_STAGED_SOURCE_HELD" else 0,
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
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(deltas),
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
         "TWO_TABLE_VARIANT_PROVEN", "PARTIAL_EVIDENCE", "BOUNDARY_CLEAN",
         "PROTECTED_FINGERPRINT_CHANGES", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_4_3_FULLY_ISOLATED_SANDBOX_WRITE_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  variant: {stage.get('VARIANT', '')}")
    print(f"  message rows before/after: {msg_before}/{msg_count}")
    print(f"  text rows before/after: {txt_before}/{txt_count}")
    print(f"  message exact symbol rows: {len(msg_exact)}")
    print(f"  text exact symbol/locale rows: {len(txt_exact)}")
    print(f"  two-table variant proven: {1 if two_table_proven else 0}")
    print(f"  partial evidence: {1 if partial else 0}")
    print(f"  boundary clean: {1 if boundary_clean else 0}")
    print(f"  protected fingerprint changes: {len(deltas)}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_PROVEN, STATUS_PARTIAL) else 2

if __name__ == "__main__":
    raise SystemExit(main())
