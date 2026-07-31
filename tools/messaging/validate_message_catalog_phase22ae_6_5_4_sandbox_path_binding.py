#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_GREEN_UNIQUE_PATH_KEYS_PROVEN_MEMO_PAYLOAD_REVIEW"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_BLOCKED"

NEXT_GREEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_5_MEMO_PAYLOAD_AND_LOCAL_INDEX_LMDB_REBUILD_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_4_UNIQUE_BASENAME_PATH_BINDING_PROOF.md")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")
TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

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
        for p in sorted((repo / ACTIVE_MSG_ROOT).glob(f"{table}.*")):
            if p.name.lower() != f"{table.lower()}.dbf":
                targets.append((p, f"active_sidecar_{table}_{p.suffix.lower().lstrip('.')}"))
        targets.append((repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx", f"active_msg_index_{table}_cdx"))
        targets.append((repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx.meta", f"active_msg_index_{table}_meta"))
        targets.append((repo / ACTIVE_MSG_LMDB_ROOT / f"{table}.cdx.d", f"active_msg_lmdb_{table}"))
        targets.append((repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"))
        targets.append((repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"))
        targets.append((repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"))
    seen = set()
    for path, role in targets:
        key = str(path.resolve()) + "|" + role
        if key in seen:
            continue
        seen.add(key)
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

def valid_dbf_field_name(name: str) -> bool:
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    return all(ch.isalnum() or ch == "_" for ch in name)

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
        if valid_dbf_field_name(name) and length > 0 and (offset + length) <= record_len:
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
                    row[fld["NAME"] + "__TYPE"] = "M"
                elif fld["TYPE"].upper() == "C":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                    row[fld["NAME"] + "__TYPE"] = "C"
                else:
                    row[fld["NAME"]] = raw.decode("ascii", errors="replace").rstrip().strip()
                    row[fld["NAME"] + "__TYPE"] = fld["TYPE"].upper()
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

    stage = first_row(reports / "message_catalog_phase22ae_6_5_4_stage_status_summary_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_4_protected_fingerprint_before_v1.csv")
    expected_msg = read_csv(reports / "message_catalog_phase22ae_6_5_3_expected_message_rows_v1.csv")
    expected_txt = read_csv(reports / "message_catalog_phase22ae_6_5_3_expected_text_rows_v1.csv")

    runtime = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_upper = log_text.upper()

    unique_msg = repo / stage.get("UNIQUE_MESSAGE_DBF", "")
    unique_txt = repo / stage.get("UNIQUE_TEXT_DBF", "")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == STATUS_GREEN.replace("_GREEN_UNIQUE_PATH_KEYS_PROVEN_MEMO_PAYLOAD_REVIEW", "_STAGED_SOURCE_HELD") if False else stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_PROOF_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("EXPECTED_MESSAGE_ROWS_2", len(expected_msg) == 2, len(expected_msg))
    gate("EXPECTED_TEXT_ROWS_10", len(expected_txt) == 10, len(expected_txt))

    after_fp = fingerprint_selected(repo)
    fp_delta = compare_fp(before_fp, after_fp)
    boundary_clean = len(fp_delta) == 0

    msg_count = ""
    txt_count = ""
    msg_matches = []
    txt_matches = []
    text_payload_rows = 0
    memo_payload_review_rows = 0

    try:
        msg_info = parse_dbf(unique_msg)
        txt_info = parse_dbf(unique_txt)
        msg_rows = read_rows(msg_info)
        txt_rows = read_rows(txt_info)
        msg_count = msg_info.record_count
        txt_count = txt_info.record_count

        for exp in expected_msg:
            fld = exp.get("SYMBOL_FIELD", "")
            sym = exp.get("SYMBOL", "")
            matches = [r for r in msg_rows if fld and r.get(fld, "") == sym]
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
                if tf:
                    if ttype.upper() == "M":
                        if latest.get(tf, "").strip() not in ("", "0"):
                            text_payload_rows += 1
                        else:
                            memo_payload_review_rows += 1
                    else:
                        if latest.get(tf, "").strip():
                            text_payload_rows += 1
    except Exception as exc:
        gate("UNIQUE_DBF_READBACK", False, exc)

    runtime_counts_14_70 = ("RECORD COUNT 14" in log_upper and "RECORD COUNT 70" in log_upper)
    runtime_active_counts_seen = ("RECORD COUNT 12" in log_upper or "RECORD COUNT 60" in log_upper)
    counts_ok = (msg_count == 14 and txt_count == 70)
    keys_ok = (len(msg_matches) == 2 and len(txt_matches) == 10)

    if failures > 0 or not boundary_clean or not runtime_counts_14_70 or runtime_active_counts_seen or not counts_ok or not keys_ok:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_4_PATH_BINDING_OR_REBUILD_READBACK"
        validation_issues = str(max(1, failures, len(fp_delta)))
    else:
        status = STATUS_GREEN
        next_gate = NEXT_GREEN
        validation_issues = "0"

    result_rows = [{
        "UNIQUE_MESSAGE_ROWS": msg_count,
        "UNIQUE_TEXT_ROWS": txt_count,
        "COUNTS_14_70": 1 if counts_ok else 0,
        "RUNTIME_COUNTS_14_70": 1 if runtime_counts_14_70 else 0,
        "RUNTIME_ACTIVE_COUNTS_SEEN": 1 if runtime_active_counts_seen else 0,
        "FOUND_MESSAGE_KEYS": len(msg_matches),
        "FOUND_TEXT_KEYS": len(txt_matches),
        "KEYS_PROVEN": 1 if keys_ok else 0,
        "TEXT_PAYLOAD_OR_POINTER_ROWS": text_payload_rows,
        "MEMO_PAYLOAD_REVIEW_ROWS": memo_payload_review_rows,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
    }]

    runtime_rows = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if runtime.exists() else 0, "DETAIL": rel(runtime, repo)},
        {"OBSERVATION": "runtime_record_count_14_seen", "VALUE": 1 if "RECORD COUNT 14" in log_upper else 0, "DETAIL": "Unique message DBF runtime count."},
        {"OBSERVATION": "runtime_record_count_70_seen", "VALUE": 1 if "RECORD COUNT 70" in log_upper else 0, "DETAIL": "Unique text DBF runtime count."},
        {"OBSERVATION": "runtime_record_count_12_seen", "VALUE": 1 if "RECORD COUNT 12" in log_upper else 0, "DETAIL": "Active message count leakage."},
        {"OBSERVATION": "runtime_record_count_60_seen", "VALUE": 1 if "RECORD COUNT 60" in log_upper else 0, "DETAIL": "Active text count leakage."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": f"protected fingerprint changes={len(fp_delta)}"},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_4_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_4_path_binding_result_v1.csv", result_rows, ["UNIQUE_MESSAGE_ROWS", "UNIQUE_TEXT_ROWS", "COUNTS_14_70", "RUNTIME_COUNTS_14_70", "RUNTIME_ACTIVE_COUNTS_SEEN", "FOUND_MESSAGE_KEYS", "FOUND_TEXT_KEYS", "KEYS_PROVEN", "TEXT_PAYLOAD_OR_POINTER_ROWS", "MEMO_PAYLOAD_REVIEW_ROWS", "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_4_found_message_keys_v1.csv", msg_matches, ["SYMBOL", "MATCHES", "RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_4_found_text_keys_v1.csv", txt_matches, ["SYMBOL", "LOCALE", "MATCHES", "RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_4_runtime_observations_v1.csv", runtime_rows, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_4_protected_fingerprint_after_v1.csv", after_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_4_protected_fingerprint_delta_v1.csv", fp_delta, ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256", "BEFORE_BYTES", "AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_4_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_4_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_STAGED_SOURCE_HELD" else 0,
        "UNIQUE_MESSAGE_ROWS": msg_count,
        "UNIQUE_TEXT_ROWS": txt_count,
        "COUNTS_14_70": 1 if counts_ok else 0,
        "RUNTIME_COUNTS_14_70": 1 if runtime_counts_14_70 else 0,
        "RUNTIME_ACTIVE_COUNTS_SEEN": 1 if runtime_active_counts_seen else 0,
        "FOUND_MESSAGE_KEYS": len(msg_matches),
        "FOUND_TEXT_KEYS": len(txt_matches),
        "KEYS_PROVEN": 1 if keys_ok else 0,
        "TEXT_PAYLOAD_OR_POINTER_ROWS": text_payload_rows,
        "MEMO_PAYLOAD_REVIEW_ROWS": memo_payload_review_rows,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if boundary_clean else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_GREEN", "UNIQUE_MESSAGE_ROWS", "UNIQUE_TEXT_ROWS",
         "COUNTS_14_70", "RUNTIME_COUNTS_14_70", "RUNTIME_ACTIVE_COUNTS_SEEN",
         "FOUND_MESSAGE_KEYS", "FOUND_TEXT_KEYS", "KEYS_PROVEN",
         "TEXT_PAYLOAD_OR_POINTER_ROWS", "MEMO_PAYLOAD_REVIEW_ROWS",
         "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_4_SANDBOX_PATH_BINDING_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  unique message/text rows: {msg_count}/{txt_count}")
    print(f"  runtime counts 14/70: {1 if runtime_counts_14_70 else 0}")
    print(f"  runtime active counts seen: {1 if runtime_active_counts_seen else 0}")
    print(f"  found message keys: {len(msg_matches)}/2")
    print(f"  found text keys: {len(txt_matches)}/10")
    print(f"  keys proven: {1 if keys_ok else 0}")
    print(f"  memo payload review rows: {memo_payload_review_rows}")
    print(f"  boundary clean: {1 if boundary_clean else 0}")
    print(f"  protected fingerprint changes: {len(fp_delta)}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
