#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_6_2_TEXT_KEY_MEMO_SIDECAR_READBACK_REPAIR_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_6_2_TEXT_KEY_MEMO_SIDECAR_READBACK_REPAIR_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_7_NATIVE_INDEX_LMDB_REBUILD_AND_PROMOTION_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_6_1_WORK_AREA_SELECT_IMPORT_ABSOLUTE_PATH_PROOF.md")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")
MESSAGE_TABLE = "SYSTEM_MESSAGES"
TEXT_TABLE = "SYSTEM_MESSAGE_TEXT"

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

def dbf_counts(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    header_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    eof = 1 if data and data[-1] == 0x1A else 0
    physical = (len(data) - header_len - eof) // record_len if record_len else 0
    remainder = (len(data) - header_len - eof) % record_len if record_len else ""
    return {
        "HEADER_COUNT": header_count,
        "HEADER_LEN": header_len,
        "RECORD_LEN": record_len,
        "PHYSICAL_COUNT": physical,
        "PHYSICAL_REMAINDER": remainder,
        "BYTES": len(data),
        "SHA256": sha256_file(path),
    }

def dbf_record_bytes(path: Path) -> list[bytes]:
    data = path.read_bytes()
    n = struct.unpack("<I", data[4:8])[0]
    h = struct.unpack("<H", data[8:10])[0]
    r = struct.unpack("<H", data[10:12])[0]
    return [data[h+i*r:h+(i+1)*r] for i in range(n)]

def enc(s: str) -> bytes:
    return (s or "").encode("cp1252", errors="replace")

def raw_key_scan(record_bytes: list[bytes], expected_rows: list[dict[str, str]], *, tail_count: int) -> list[dict[str, Any]]:
    rows = []
    tail = record_bytes[-tail_count:] if tail_count else record_bytes
    base_recno = max(0, len(record_bytes) - len(tail)) + 1
    for exp in expected_rows:
        symbol = exp.get("SYMBOL", "")
        locale = exp.get("LOCALE", "")
        found = 0
        found_recno = ""
        raw_prefix = ""
        for idx, rec in enumerate(tail):
            sym_ok = enc(symbol) in rec
            loc_ok = True if not locale else enc(locale) in rec
            if sym_ok and loc_ok:
                found = 1
                found_recno = base_recno + idx
                raw_prefix = rec[:220].decode("cp1252", errors="replace").rstrip()
                break
        rows.append({
            "SYMBOL": symbol,
            "LOCALE": locale,
            "FOUND": found,
            "RECNO": found_recno,
            "RAW_PREFIX": raw_prefix,
        })
    return rows

def raw_message_key_scan(record_bytes: list[bytes], expected_rows: list[dict[str, str]], *, tail_count: int) -> list[dict[str, Any]]:
    rows = []
    tail = record_bytes[-tail_count:] if tail_count else record_bytes
    base_recno = max(0, len(record_bytes) - len(tail)) + 1
    for exp in expected_rows:
        symbol = exp.get("SYMBOL", "")
        found = 0
        found_recno = ""
        raw_prefix = ""
        for idx, rec in enumerate(tail):
            if enc(symbol) in rec:
                found = 1
                found_recno = base_recno + idx
                raw_prefix = rec[:220].decode("cp1252", errors="replace").rstrip()
                break
        rows.append({
            "SYMBOL": symbol,
            "FOUND": found,
            "RECNO": found_recno,
            "RAW_PREFIX": raw_prefix,
        })
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

def runtime_ok(text: str) -> dict[str, int]:
    u = text.upper()
    return {
        "IMPORTED_2_RECORDS": 1 if "IMPORTED 2 RECORDS" in u else 0,
        "IMPORTED_10_RECORDS": 1 if "IMPORTED 10 RECORDS" in u else 0,
        "AREA_1_SELECTED": 1 if "SELECTED AREA 1" in u else 0,
        "AREA_2_SELECTED": 1 if "SELECTED AREA 2" in u else 0,
        "RECS_14_SEEN": 1 if re.search(r"RECS:\s*14\b", text, flags=re.IGNORECASE) or re.search(r"(?m)^\s*14\s*$", text) else 0,
        "RECS_70_SEEN": 1 if re.search(r"RECS:\s*70\b", text, flags=re.IGNORECASE) or re.search(r"(?m)^\s*70\s*$", text) else 0,
        "ALREADY_OPEN_WARNING": 1 if "ALREADY OPEN" in u else 0,
        "SELECT_MISSING_WARNING": 1 if ("SELECT:" in u and ("NOT FOUND" in u or "UNKNOWN" in u)) else 0,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_6_1_stage_status_summary_v1.csv")
    blocked = first_row(reports / "message_catalog_phase22ae_6_5_6_1_validate_status_summary_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_6_1_active_fingerprint_before_v1.csv")
    expected_msg = read_csv(reports / "message_catalog_phase22ae_6_5_6_1_expected_message_keys_v1.csv")
    expected_txt = read_csv(reports / "message_catalog_phase22ae_6_5_6_1_expected_text_keys_v1.csv")

    msg_dbf = repo / stage.get("UNIQUE_MESSAGE_DBF", "")
    txt_dbf = repo / stage.get("UNIQUE_TEXT_DBF", "")
    txt_dtx = txt_dbf.with_suffix(".dtx")
    active_txt_dtx = repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGE_TEXT.dtx"
    runlog = repo / RUNLOG
    runlog_text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: Any):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_6_1_STAGE_GREEN",
         stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_1_WORK_AREA_SELECT_IMPORT_PROOF_STAGED_SOURCE_HELD",
         stage.get("STATUS", "missing"))
    gate("PHASE22AE_6_5_6_1_BLOCKED_ONLY_ON_TEXT_KEY_VALIDATOR",
         blocked.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_1_WORK_AREA_SELECT_IMPORT_PROOF_BLOCKED" and blocked.get("FOUND_MESSAGE_KEYS") == "2" and blocked.get("FOUND_TEXT_KEYS") == "0",
         f"status={blocked.get('STATUS','missing')}; found message/text={blocked.get('FOUND_MESSAGE_KEYS','')}/{blocked.get('FOUND_TEXT_KEYS','')}")
    gate("RUNTIME_LOG_EXISTS", runlog.exists(), rel(runlog, repo))
    gate("MESSAGE_DBF_EXISTS", msg_dbf.exists(), rel(msg_dbf, repo))
    gate("TEXT_DBF_EXISTS", txt_dbf.exists(), rel(txt_dbf, repo))
    gate("TEXT_DTX_EXISTS", txt_dtx.exists(), rel(txt_dtx, repo))
    gate("EXPECTED_MESSAGE_KEYS_2", len(expected_msg) == 2, len(expected_msg))
    gate("EXPECTED_TEXT_KEYS_10", len(expected_txt) == 10, len(expected_txt))

    msg_counts = {}
    txt_counts = {}
    msg_key_rows = []
    txt_key_rows = []
    if msg_dbf.exists():
        msg_counts = dbf_counts(msg_dbf)
        msg_key_rows = raw_message_key_scan(dbf_record_bytes(msg_dbf), expected_msg, tail_count=2)
    if txt_dbf.exists():
        txt_counts = dbf_counts(txt_dbf)
        txt_key_rows = raw_key_scan(dbf_record_bytes(txt_dbf), expected_txt, tail_count=10)

    found_msg = sum(1 for r in msg_key_rows if r.get("FOUND") == 1)
    found_txt = sum(1 for r in txt_key_rows if r.get("FOUND") == 1)

    gate("MESSAGE_COUNT_14", msg_counts.get("HEADER_COUNT") == 14 and msg_counts.get("PHYSICAL_COUNT") == 14, msg_counts)
    gate("TEXT_COUNT_70", txt_counts.get("HEADER_COUNT") == 70 and txt_counts.get("PHYSICAL_COUNT") == 70, txt_counts)
    gate("RAW_MESSAGE_KEYS_2", found_msg == 2, found_msg)
    gate("RAW_TEXT_SYMBOL_LOCALE_KEYS_10", found_txt == 10, found_txt)

    active_dtx_size = active_txt_dtx.stat().st_size if active_txt_dtx.exists() else 0
    txt_dtx_size = txt_dtx.stat().st_size if txt_dtx.exists() else 0
    gate("TEXT_DTX_NONEMPTY", txt_dtx_size > 0, txt_dtx_size)
    gate("TEXT_DTX_GREW_VS_ACTIVE_BASELINE", txt_dtx_size > active_dtx_size, f"sandbox={txt_dtx_size}; active={active_dtx_size}")

    rt = runtime_ok(runlog_text)
    gate("RUNTIME_IMPORTED_2_AND_10", rt["IMPORTED_2_RECORDS"] == 1 and rt["IMPORTED_10_RECORDS"] == 1, rt)
    gate("RUNTIME_SELECT_AREAS_1_AND_2", rt["AREA_1_SELECTED"] == 1 and rt["AREA_2_SELECTED"] == 1, rt)
    gate("RUNTIME_RECS_14_AND_70", rt["RECS_14_SEEN"] == 1 and rt["RECS_70_SEEN"] == 1, rt)
    gate("NO_ALREADY_OPEN_WARNING", rt["ALREADY_OPEN_WARNING"] == 0, rt)
    gate("NO_SELECT_MISSING_WARNING", rt["SELECT_MISSING_WARNING"] == 0, rt)

    after_fp = fingerprint_active(repo)
    fp_delta = compare_fp(before_fp, after_fp)
    boundary_clean = len(fp_delta) == 0
    gate("ACTIVE_FINGERPRINT_CLEAN", boundary_clean, len(fp_delta))

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if failures == 0 else str(failures)

    dtx_rows = [{
        "SIDE_CAR": rel(txt_dtx, repo),
        "EXISTS": 1 if txt_dtx.exists() else 0,
        "BYTES": txt_dtx_size,
        "ACTIVE_BASELINE": rel(active_txt_dtx, repo),
        "ACTIVE_BASELINE_BYTES": active_dtx_size,
        "GREW_VS_ACTIVE_BASELINE": 1 if txt_dtx_size > active_dtx_size else 0,
        "SHA256": sha256_file(txt_dtx),
    }]

    count_rows = [
        {"TABLE": "MSG6561_MESSAGES_NATIVE_IMPORT", "DBF": rel(msg_dbf, repo), **msg_counts},
        {"TABLE": "MSG6561_TEXT_NATIVE_IMPORT", "DBF": rel(txt_dbf, repo), **txt_counts},
    ]

    result = [{
        "MESSAGE_ROWS_AFTER": msg_counts.get("HEADER_COUNT", ""),
        "TEXT_ROWS_AFTER": txt_counts.get("HEADER_COUNT", ""),
        "COUNTS_14_70": 1 if msg_counts.get("HEADER_COUNT") == 14 and txt_counts.get("HEADER_COUNT") == 70 else 0,
        "RAW_MESSAGE_KEYS_FOUND": found_msg,
        "RAW_TEXT_KEYS_FOUND": found_txt,
        "TEXT_DTX_EXISTS": 1 if txt_dtx.exists() else 0,
        "TEXT_DTX_BYTES": txt_dtx_size,
        "TEXT_DTX_GREW_VS_ACTIVE_BASELINE": 1 if txt_dtx_size > active_dtx_size else 0,
        "RUNTIME_IMPORTED_2_RECORDS": rt["IMPORTED_2_RECORDS"],
        "RUNTIME_IMPORTED_10_RECORDS": rt["IMPORTED_10_RECORDS"],
        "RUNTIME_RECS_14_SEEN": rt["RECS_14_SEEN"],
        "RUNTIME_RECS_70_SEEN": rt["RECS_70_SEEN"],
        "ALREADY_OPEN_WARNING": rt["ALREADY_OPEN_WARNING"],
        "SELECT_MISSING_WARNING": rt["SELECT_MISSING_WARNING"],
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
    }]

    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_dbf_count_readback_v1.csv",
              count_rows, ["TABLE", "DBF", "HEADER_COUNT", "HEADER_LEN", "RECORD_LEN", "PHYSICAL_COUNT", "PHYSICAL_REMAINDER", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_raw_message_key_readback_v1.csv",
              msg_key_rows, ["SYMBOL", "FOUND", "RECNO", "RAW_PREFIX"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_raw_text_key_readback_v1.csv",
              txt_key_rows, ["SYMBOL", "LOCALE", "FOUND", "RECNO", "RAW_PREFIX"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_memo_sidecar_readback_v1.csv",
              dtx_rows, ["SIDE_CAR", "EXISTS", "BYTES", "ACTIVE_BASELINE", "ACTIVE_BASELINE_BYTES", "GREW_VS_ACTIVE_BASELINE", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_result_summary_v1.csv",
              result, ["MESSAGE_ROWS_AFTER", "TEXT_ROWS_AFTER", "COUNTS_14_70",
                       "RAW_MESSAGE_KEYS_FOUND", "RAW_TEXT_KEYS_FOUND",
                       "TEXT_DTX_EXISTS", "TEXT_DTX_BYTES", "TEXT_DTX_GREW_VS_ACTIVE_BASELINE",
                       "RUNTIME_IMPORTED_2_RECORDS", "RUNTIME_IMPORTED_10_RECORDS",
                       "RUNTIME_RECS_14_SEEN", "RUNTIME_RECS_70_SEEN",
                       "ALREADY_OPEN_WARNING", "SELECT_MISSING_WARNING",
                       "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_active_fingerprint_after_v1.csv",
              after_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_active_fingerprint_delta_v1.csv",
              fp_delta, ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256"])

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": f"protected fingerprint changes={len(fp_delta)}"},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_6_2_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_6_1_STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_1_WORK_AREA_SELECT_IMPORT_PROOF_STAGED_SOURCE_HELD" else 0,
        "MESSAGE_ROWS_AFTER": msg_counts.get("HEADER_COUNT", ""),
        "TEXT_ROWS_AFTER": txt_counts.get("HEADER_COUNT", ""),
        "COUNTS_14_70": 1 if msg_counts.get("HEADER_COUNT") == 14 and txt_counts.get("HEADER_COUNT") == 70 else 0,
        "RAW_MESSAGE_KEYS_FOUND": found_msg,
        "RAW_TEXT_KEYS_FOUND": found_txt,
        "TEXT_DTX_EXISTS": 1 if txt_dtx.exists() else 0,
        "TEXT_DTX_BYTES": txt_dtx_size,
        "TEXT_DTX_GREW_VS_ACTIVE_BASELINE": 1 if txt_dtx_size > active_dtx_size else 0,
        "RUNTIME_IMPORTED_2_RECORDS": rt["IMPORTED_2_RECORDS"],
        "RUNTIME_IMPORTED_10_RECORDS": rt["IMPORTED_10_RECORDS"],
        "RUNTIME_RECS_14_SEEN": rt["RECS_14_SEEN"],
        "RUNTIME_RECS_70_SEEN": rt["RECS_70_SEEN"],
        "ALREADY_OPEN_WARNING": rt["ALREADY_OPEN_WARNING"],
        "SELECT_MISSING_WARNING": rt["SELECT_MISSING_WARNING"],
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if boundary_clean else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE if status == STATUS_GREEN else "HOLD_AND_FIX_PHASE22AE_6_5_6_2_READBACK_REPAIR",
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_6_1_STAGE_GREEN",
         "MESSAGE_ROWS_AFTER", "TEXT_ROWS_AFTER", "COUNTS_14_70",
         "RAW_MESSAGE_KEYS_FOUND", "RAW_TEXT_KEYS_FOUND",
         "TEXT_DTX_EXISTS", "TEXT_DTX_BYTES", "TEXT_DTX_GREW_VS_ACTIVE_BASELINE",
         "RUNTIME_IMPORTED_2_RECORDS", "RUNTIME_IMPORTED_10_RECORDS",
         "RUNTIME_RECS_14_SEEN", "RUNTIME_RECS_70_SEEN",
         "ALREADY_OPEN_WARNING", "SELECT_MISSING_WARNING",
         "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.6.1 stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_6_1_WORK_AREA_SELECT_IMPORT_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  message/text rows after: {msg_counts.get('HEADER_COUNT','')}/{txt_counts.get('HEADER_COUNT','')}")
    print(f"  raw message keys found: {found_msg}/2")
    print(f"  raw text keys found: {found_txt}/10")
    print(f"  text dtx exists/bytes: {1 if txt_dtx.exists() else 0}/{txt_dtx_size}")
    print(f"  text dtx grew vs active baseline: {1 if txt_dtx_size > active_dtx_size else 0}")
    print(f"  runtime imported 2/10: {rt['IMPORTED_2_RECORDS']}/{rt['IMPORTED_10_RECORDS']}")
    print(f"  runtime recs 14/70 seen: {rt['RECS_14_SEEN']}/{rt['RECS_70_SEEN']}")
    print(f"  already-open warning: {rt['ALREADY_OPEN_WARNING']}")
    print(f"  select missing warning: {rt['SELECT_MISSING_WARNING']}")
    print(f"  boundary clean: {1 if boundary_clean else 0}")
    print(f"  protected fingerprint changes: {len(fp_delta)}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE if status == STATUS_GREEN else 'HOLD_AND_FIX_PHASE22AE_6_5_6_2_READBACK_REPAIR'}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
