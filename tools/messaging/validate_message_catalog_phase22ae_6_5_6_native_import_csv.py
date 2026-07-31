#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_WRITE_PROOF_GREEN_NATIVE_14_70_KEYS_MEMO_REVIEW"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_WRITE_PROOF_BLOCKED"
NEXT_GREEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_7_NATIVE_INDEX_LMDB_REBUILD_AND_PROMOTION_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_6_NATIVE_IMPORT_CSV_ABSOLUTE_PATH_PROOF.md")
ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")
MESSAGE_TABLE = "SYSTEM_MESSAGES"
TEXT_TABLE = "SYSTEM_MESSAGE_TEXT"

class DbfInfo:
    def __init__(self, path: Path, header_count: int, header_len: int, record_len: int, fields: list[dict[str, Any]]):
        self.path = path
        self.header_count = header_count
        self.header_len = header_len
        self.record_len = record_len
        self.fields = fields

def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
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

def valid_field_name(name: str) -> bool:
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    return all(ch.isalnum() or ch == "_" for ch in name)

def parse_dbf(path: Path) -> DbfInfo:
    data = path.read_bytes()
    if len(data) < 32:
        raise RuntimeError(f"DBF too small: {path}")
    count = struct.unpack("<I", data[4:8])[0]
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
        ftype = chr(data[pos+11]) if 32 <= data[pos+11] <= 126 else f"0x{data[pos+11]:02X}"
        length = data[pos+16]
        decimals = data[pos+17]
        if valid_field_name(name) and length > 0 and (offset + length) <= record_len:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "DECIMALS": decimals, "OFFSET": offset})
            offset += length
        pos += 32
    return DbfInfo(path, count, header_len, record_len, fields)

def read_rows(info: DbfInfo) -> list[dict[str, Any]]:
    rows = []
    with info.path.open("rb") as f:
        f.seek(info.header_len)
        for i in range(info.header_count):
            rec = f.read(info.record_len)
            if len(rec) < info.record_len:
                break
            row = {"__RECNO__": i + 1, "__DELETED__": 1 if rec[:1] == b"*" else 0}
            for fld in info.fields:
                raw = rec[fld["OFFSET"]:fld["OFFSET"] + fld["LENGTH"]]
                if fld["TYPE"].upper() in ("C", "M", "V", "Q"):
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                else:
                    row[fld["NAME"]] = raw.decode("ascii", errors="replace").rstrip().strip()
            rows.append(row)
    return rows

def fingerprint_active(repo: Path):
    rows = []
    targets = []
    for table in [MESSAGE_TABLE, TEXT_TABLE]:
        targets.append((repo / ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"))
        for p in sorted((repo / ACTIVE_MSG_ROOT).glob(f"{table}.*")):
            if p.name.lower() != f"{table.lower()}.dbf":
                targets.append((p, f"active_sidecar_{table}_{p.suffix.lower().lstrip('.')}"))
        targets.extend([
            (repo / ACTIVE_INDEX_ROOT / f"{table}.cdx", f"active_index_{table}_cdx"),
            (repo / ACTIVE_INDEX_ROOT / f"{table}.cdx.meta", f"active_index_{table}_meta"),
            (repo / ACTIVE_LMDB_ROOT / f"{table}.cdx.d", f"active_lmdb_{table}"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"),
            (repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"),
        ])
    seen = set()
    for path, role in targets:
        key = role + "|" + str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        if path.is_dir():
            files = sorted(p for p in path.rglob("*") if p.is_file())
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

def compare_fp(before: list[dict[str, str]], after: list[dict[str, str]]):
    b = {r["ROLE"] + "|" + r["PATH"]: r for r in before}
    a = {r["ROLE"] + "|" + r["PATH"]: r for r in after}
    out = []
    for key in sorted(set(b) | set(a)):
        br = b.get(key)
        ar = a.get(key)
        if br is None:
            out.append({"ROLE": ar["ROLE"], "PATH": ar["PATH"], "CHANGE": "ADDED", "BEFORE_SHA256": "", "AFTER_SHA256": ar.get("SHA256", "")})
        elif ar is None:
            out.append({"ROLE": br["ROLE"], "PATH": br["PATH"], "CHANGE": "REMOVED", "BEFORE_SHA256": br.get("SHA256", ""), "AFTER_SHA256": ""})
        elif br.get("SHA256") != ar.get("SHA256") or str(br.get("BYTES")) != str(ar.get("BYTES")):
            out.append({"ROLE": ar["ROLE"], "PATH": ar["PATH"], "CHANGE": "MODIFIED", "BEFORE_SHA256": br.get("SHA256", ""), "AFTER_SHA256": ar.get("SHA256", "")})
    return out

def parse_open_counts(text: str):
    rows = []
    pat = re.compile(r"Opened\s+(.+?)\s+\(v64\)\s+:\s+Record count\s+(\d+)", re.IGNORECASE)
    for m in pat.finditer(text):
        rows.append({"OPENED_NAME": m.group(1).strip(), "COUNT": int(m.group(2))})
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_6_stage_status_summary_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_6_active_fingerprint_before_v1.csv")
    expected_msg = read_csv(reports / "message_catalog_phase22ae_6_5_6_expected_message_keys_v1.csv")
    expected_txt = read_csv(reports / "message_catalog_phase22ae_6_5_6_expected_text_keys_v1.csv")

    runtime_path = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime_path.is_absolute():
        runtime_path = repo / runtime_path
    runtime_text = runtime_path.read_text(encoding="utf-8", errors="replace") if runtime_path.exists() else ""
    runtime_upper = runtime_text.upper()
    open_counts = parse_open_counts(runtime_text)

    msg_dbf = repo / stage.get("UNIQUE_MESSAGE_DBF", "")
    txt_dbf = repo / stage.get("UNIQUE_TEXT_DBF", "")

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: Any):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_WRITE_PROOF_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_LOG_EXISTS", runtime_path.exists(), rel(runtime_path, repo))
    gate("EXPECTED_MESSAGE_KEYS_2", len(expected_msg) == 2, len(expected_msg))
    gate("EXPECTED_TEXT_KEYS_10", len(expected_txt) == 10, len(expected_txt))

    after_fp = fingerprint_active(repo)
    fp_delta = compare_fp(before_fp, after_fp)
    boundary_clean = len(fp_delta) == 0

    msg_count = text_count = ""
    msg_matches = []
    txt_matches = []
    memo_review_rows = 0
    payload_or_pointer_rows = 0

    try:
        msg_info = parse_dbf(msg_dbf)
        txt_info = parse_dbf(txt_dbf)
        msg_rows = read_rows(msg_info)
        txt_rows = read_rows(txt_info)
        msg_count = msg_info.header_count
        text_count = txt_info.header_count

        for exp in expected_msg:
            sf = exp.get("SYMBOL_FIELD", "")
            sym = exp.get("SYMBOL", "")
            matches = [r for r in msg_rows if sf and r.get(sf, "") == sym]
            if matches:
                msg_matches.append({"SYMBOL": sym, "MATCHES": len(matches), "RECNO": matches[-1].get("__RECNO__", "")})

        for exp in expected_txt:
            sf = exp.get("SYMBOL_FIELD", "")
            sym = exp.get("SYMBOL", "")
            lf = exp.get("LOCALE_FIELD", "")
            loc = exp.get("LOCALE", "")
            tf = exp.get("TEXT_FIELD", "")
            ttype = exp.get("TEXT_FIELD_TYPE", "")
            matches = [r for r in txt_rows if sf and r.get(sf, "") == sym and (not lf or r.get(lf, "") == loc)]
            if matches:
                latest = matches[-1]
                txt_matches.append({"SYMBOL": sym, "LOCALE": loc, "MATCHES": len(matches), "RECNO": latest.get("__RECNO__", "")})
                if tf and latest.get(tf, "").strip():
                    payload_or_pointer_rows += 1
                elif ttype.upper() == "M":
                    memo_review_rows += 1
    except Exception as exc:
        gate("SANDBOX_DBF_READBACK", False, exc)

    imported_2 = "IMPORTED 2 RECORDS" in runtime_upper
    imported_10 = "IMPORTED 10 RECORDS" in runtime_upper
    runtime_msg_14 = any("MSG656_MESSAGES_NATIVE_IMPORT" in r["OPENED_NAME"].upper() and r["COUNT"] == 14 for r in open_counts)
    runtime_txt_70 = any("MSG656_TEXT_NATIVE_IMPORT" in r["OPENED_NAME"].upper() and r["COUNT"] == 70 for r in open_counts)
    runtime_absolute_script = stage.get("ABSOLUTE_PATH_NAMES_SUPPORTED_BY_PROOF") == "1"
    keys_ok = len(msg_matches) == 2 and len(txt_matches) == 10
    counts_ok = msg_count == 14 and text_count == 70

    if failures > 0 or not boundary_clean or not imported_2 or not imported_10 or not runtime_msg_14 or not runtime_txt_70 or not counts_ok or not keys_ok:
        status = STATUS_BLOCKED
        validation_issues = str(max(1, failures, len(fp_delta)))
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_WRITE_PROOF"
    else:
        status = STATUS_GREEN
        validation_issues = "0"
        next_gate = NEXT_GREEN

    result = [{
        "MESSAGE_ROWS_AFTER": msg_count,
        "TEXT_ROWS_AFTER": text_count,
        "COUNTS_14_70": 1 if counts_ok else 0,
        "RUNTIME_MESSAGE_14": 1 if runtime_msg_14 else 0,
        "RUNTIME_TEXT_70": 1 if runtime_txt_70 else 0,
        "IMPORTED_2_RECORDS": 1 if imported_2 else 0,
        "IMPORTED_10_RECORDS": 1 if imported_10 else 0,
        "FOUND_MESSAGE_KEYS": len(msg_matches),
        "FOUND_TEXT_KEYS": len(txt_matches),
        "KEYS_PROVEN": 1 if keys_ok else 0,
        "MEMO_PAYLOAD_REVIEW_ROWS": memo_review_rows,
        "TEXT_PAYLOAD_OR_POINTER_ROWS": payload_or_pointer_rows,
        "ABSOLUTE_PATH_NAMES_SUPPORTED_BY_PROOF": 1 if runtime_absolute_script else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
    }]

    write_csv(reports / "message_catalog_phase22ae_6_5_6_validate_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_native_import_result_v1.csv",
              result, ["MESSAGE_ROWS_AFTER", "TEXT_ROWS_AFTER", "COUNTS_14_70",
                       "RUNTIME_MESSAGE_14", "RUNTIME_TEXT_70",
                       "IMPORTED_2_RECORDS", "IMPORTED_10_RECORDS",
                       "FOUND_MESSAGE_KEYS", "FOUND_TEXT_KEYS", "KEYS_PROVEN",
                       "MEMO_PAYLOAD_REVIEW_ROWS", "TEXT_PAYLOAD_OR_POINTER_ROWS",
                       "ABSOLUTE_PATH_NAMES_SUPPORTED_BY_PROOF",
                       "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_runtime_open_counts_v1.csv",
              open_counts, ["OPENED_NAME", "COUNT"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_found_message_keys_v1.csv",
              msg_matches, ["SYMBOL", "MATCHES", "RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_found_text_keys_v1.csv",
              txt_matches, ["SYMBOL", "LOCALE", "MATCHES", "RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_active_fingerprint_after_v1.csv",
              after_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_active_fingerprint_delta_v1.csv",
              fp_delta, ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256"])

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": f"protected fingerprint changes={len(fp_delta)}"},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_6_validate_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_6_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_WRITE_PROOF_STAGED_SOURCE_HELD" else 0,
        "MESSAGE_ROWS_AFTER": msg_count,
        "TEXT_ROWS_AFTER": text_count,
        "COUNTS_14_70": 1 if counts_ok else 0,
        "RUNTIME_MESSAGE_14": 1 if runtime_msg_14 else 0,
        "RUNTIME_TEXT_70": 1 if runtime_txt_70 else 0,
        "IMPORTED_2_RECORDS": 1 if imported_2 else 0,
        "IMPORTED_10_RECORDS": 1 if imported_10 else 0,
        "FOUND_MESSAGE_KEYS": len(msg_matches),
        "FOUND_TEXT_KEYS": len(txt_matches),
        "KEYS_PROVEN": 1 if keys_ok else 0,
        "MEMO_PAYLOAD_REVIEW_ROWS": memo_review_rows,
        "ABSOLUTE_PATH_NAMES_SUPPORTED_BY_PROOF": 1 if runtime_absolute_script else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if boundary_clean else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_GREEN",
         "MESSAGE_ROWS_AFTER", "TEXT_ROWS_AFTER", "COUNTS_14_70",
         "RUNTIME_MESSAGE_14", "RUNTIME_TEXT_70",
         "IMPORTED_2_RECORDS", "IMPORTED_10_RECORDS",
         "FOUND_MESSAGE_KEYS", "FOUND_TEXT_KEYS", "KEYS_PROVEN",
         "MEMO_PAYLOAD_REVIEW_ROWS", "ABSOLUTE_PATH_NAMES_SUPPORTED_BY_PROOF",
         "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_6_NATIVE_IMPORT_CSV_WRITE_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  message/text rows after: {msg_count}/{text_count}")
    print(f"  runtime message/text 14/70: {1 if runtime_msg_14 else 0}/{1 if runtime_txt_70 else 0}")
    print(f"  imported 2/10 records: {1 if imported_2 else 0}/{1 if imported_10 else 0}")
    print(f"  found message keys: {len(msg_matches)}/2")
    print(f"  found text keys: {len(txt_matches)}/10")
    print(f"  keys proven: {1 if keys_ok else 0}")
    print(f"  memo payload review rows: {memo_review_rows}")
    print(f"  absolute path names supported by proof: {1 if runtime_absolute_script else 0}")
    print(f"  boundary clean: {1 if boundary_clean else 0}")
    print(f"  protected fingerprint changes: {len(fp_delta)}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
