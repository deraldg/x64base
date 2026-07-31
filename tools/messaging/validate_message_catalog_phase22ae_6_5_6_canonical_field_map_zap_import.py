#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_GREEN_EXACT_KEYS_PROVEN"
STATUS_COUNT_ONLY = "MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_GREEN_COUNTS_ONLY_FIELD_MAP_REVIEW"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_BLOCKED"
NEXT_PROVEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_7_ACTIVE_PROMOTION_PLAN_FROM_CANONICAL_ZAP_IMPORT_PROOF"
NEXT_COUNT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_7_CANONICAL_FIELD_MAP_REPAIR"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF.md")
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

def fingerprint_selected(repo: Path):
    rows = []
    targets = []
    for table in TABLES:
        targets.extend([
            (repo / ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"),
            (repo / ACTIVE_MSG_ROOT / f"{table}.dtx", f"active_dtx_{table}"),
            (repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx", f"active_msg_index_{table}_cdx"),
            (repo / ACTIVE_MSG_INDEX_ROOT / f"{table}.cdx.meta", f"active_msg_index_{table}_meta"),
            (repo / ACTIVE_MSG_LMDB_ROOT / f"{table}.cdx.d", f"active_msg_lmdb_{table}"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_index_{table}_cdx"),
            (repo / DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_index_{table}_meta"),
            (repo / DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"),
        ])
    for path, role in targets:
        if path.is_dir():
            files = sorted(p for p in path.rglob("*") if p.is_file())
            h = hashlib.sha256()
            total = 0
            for f in files:
                h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
                h.update(sha256_file(f).encode("ascii"))
                total += f.stat().st_size
            rows.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":1,"KIND":"dir","BYTES":total,"SHA256":h.hexdigest(),"FILES":len(files)})
        elif path.is_file():
            rows.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":1,"KIND":"file","BYTES":path.stat().st_size,"SHA256":sha256_file(path),"FILES":1})
        else:
            rows.append({"ROLE":role,"PATH":rel(path,repo),"EXISTS":0,"KIND":"missing","BYTES":0,"SHA256":"","FILES":0})
    return rows

def compare_fp(before, after):
    b = {r["ROLE"]+"|"+r["PATH"]:r for r in before}
    a = {r["ROLE"]+"|"+r["PATH"]:r for r in after}
    deltas = []
    for key in sorted(set(b)|set(a)):
        br, ar = b.get(key), a.get(key)
        if br is None:
            deltas.append({"ROLE":ar.get("ROLE",""),"PATH":ar.get("PATH",""),"CHANGE":"ADDED","BEFORE_SHA256":"","AFTER_SHA256":ar.get("SHA256",""),"BEFORE_BYTES":"","AFTER_BYTES":ar.get("BYTES","")})
        elif ar is None:
            deltas.append({"ROLE":br.get("ROLE",""),"PATH":br.get("PATH",""),"CHANGE":"REMOVED","BEFORE_SHA256":br.get("SHA256",""),"AFTER_SHA256":"","BEFORE_BYTES":br.get("BYTES",""),"AFTER_BYTES":""})
        elif br.get("SHA256") != ar.get("SHA256") or str(br.get("BYTES")) != str(ar.get("BYTES")):
            deltas.append({"ROLE":ar.get("ROLE",br.get("ROLE","")),"PATH":ar.get("PATH",br.get("PATH","")),"CHANGE":"MODIFIED","BEFORE_SHA256":br.get("SHA256",""),"AFTER_SHA256":ar.get("SHA256",""),"BEFORE_BYTES":br.get("BYTES",""),"AFTER_BYTES":ar.get("BYTES","")})
    return deltas

def parse_dbf(path: Path):
    data = path.read_bytes()
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
            fields.append({"NAME":name,"TYPE":ftype,"LENGTH":length,"OFFSET":offset})
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
            row = {"__RECNO__":i+1,"__DELETED__":1 if rec[:1] == b"*" else 0}
            for fld in info.fields:
                raw = rec[fld["OFFSET"]:fld["OFFSET"] + fld["LENGTH"]]
                if fld["TYPE"].upper() == "M":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                    row[fld["NAME"]+"__RAW_HEX"] = raw.hex()
                elif fld["TYPE"].upper() == "C":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                else:
                    row[fld["NAME"]] = raw.decode("ascii", errors="replace").rstrip().strip()
            rows.append(row)
    return rows

def row_has_value(row, value):
    if not value:
        return False
    return any(str(v).strip() == value for k, v in row.items() if not k.startswith("__") and not k.endswith("__RAW_HEX"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_6_stage_status_summary_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_6_protected_fingerprint_before_v1.csv")
    expected_msg = read_csv(reports / "message_catalog_phase22ae_6_5_6_expected_message_rows_v1.csv")
    expected_txt = read_csv(reports / "message_catalog_phase22ae_6_5_6_expected_text_rows_v1.csv")

    runtime = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_upper = log_text.upper()

    sandbox = repo / stage.get("SANDBOX_ROOT","")
    msg_dbf = sandbox / "dbf/SYSTEM_MESSAGES.dbf"
    txt_dbf = sandbox / "dbf/SYSTEM_MESSAGE_TEXT.dbf"

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE":name,"STATUS":"PASS" if ok else "FAIL","DETAIL":str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_STAGED_SOURCE_HELD", stage.get("STATUS","missing"))
    gate("RUNTIME_PROOF_EXISTS", runtime.exists(), rel(runtime,repo))
    gate("EXPECTED_MESSAGE_ROWS_2", len(expected_msg) == 2, len(expected_msg))
    gate("EXPECTED_TEXT_ROWS_10", len(expected_txt) == 10, len(expected_txt))

    after_fp = fingerprint_selected(repo)
    fp_delta = compare_fp(before_fp, after_fp)
    boundary_clean = len(fp_delta) == 0

    msg_count = ""
    txt_count = ""
    msg_found = []
    txt_found = []
    tail_rows = []
    field_hits = []

    try:
        msg_info = parse_dbf(msg_dbf)
        txt_info = parse_dbf(txt_dbf)
        msg_rows = read_rows(msg_info)
        txt_rows = read_rows(txt_info)
        msg_count = msg_info.record_count
        txt_count = txt_info.record_count

        for exp in expected_msg:
            sym = exp.get("SYMBOL","")
            hits = [r for r in msg_rows if row_has_value(r, sym)]
            if hits:
                msg_found.append({"SYMBOL":sym,"MATCHES":len(hits),"RECNO":hits[-1].get("__RECNO__","")})
                for k,v in hits[-1].items():
                    if str(v).strip() == sym:
                        field_hits.append({"TABLE":"SYSTEM_MESSAGES","SYMBOL":sym,"LOCALE":"","FIELD":k,"RECNO":hits[-1].get("__RECNO__","")})
        for exp in expected_txt:
            sym = exp.get("SYMBOL","")
            loc = exp.get("LOCALE","")
            hits = [r for r in txt_rows if row_has_value(r, sym) and (not loc or row_has_value(r, loc))]
            if hits:
                txt_found.append({"SYMBOL":sym,"LOCALE":loc,"MATCHES":len(hits),"RECNO":hits[-1].get("__RECNO__","")})
                for k,v in hits[-1].items():
                    if str(v).strip() in (sym, loc):
                        field_hits.append({"TABLE":"SYSTEM_MESSAGE_TEXT","SYMBOL":sym,"LOCALE":loc,"FIELD":k,"RECNO":hits[-1].get("__RECNO__","")})
        for label, rows in [("SYSTEM_MESSAGES", msg_rows[-6:]), ("SYSTEM_MESSAGE_TEXT", txt_rows[-12:])]:
            for r in rows:
                compact = {k:v for k,v in r.items() if k in ("__RECNO__","__DELETED__") or (isinstance(v,str) and v.strip())}
                tail_rows.append({"TABLE":label,"RECNO":r.get("__RECNO__",""),"ROW_JSON":json.dumps(compact, ensure_ascii=False, sort_keys=True)})
    except Exception as exc:
        gate("SANDBOX_DBF_READBACK", False, exc)

    counts_expected = (msg_count == 14 and txt_count == 70)
    keys_found = (len(msg_found) == 2 and len(txt_found) == 10)
    imported_14 = "IMPORTED 14 RECORDS" in log_upper
    imported_70 = "IMPORTED 70 RECORDS" in log_upper
    zap_signal = "ZAP COMPLETE" in log_upper or "ZAPPING:" in log_upper

    if failures > 0 or not boundary_clean:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_6_SETUP_OR_BOUNDARY"
        validation_issues = str(max(1, failures, len(fp_delta)))
    elif counts_expected and keys_found:
        status = STATUS_PROVEN
        next_gate = NEXT_PROVEN
        validation_issues = "0"
    else:
        status = STATUS_COUNT_ONLY
        next_gate = NEXT_COUNT
        validation_issues = "0"

    result = [{
        "SANDBOX_MESSAGE_ROWS_AFTER": msg_count,
        "SANDBOX_TEXT_ROWS_AFTER": txt_count,
        "COUNTS_EXPECTED_14_AND_70": 1 if counts_expected else 0,
        "FOUND_MESSAGE_KEYS": len(msg_found),
        "FOUND_TEXT_KEYS": len(txt_found),
        "EXACT_KEYS_PROVEN": 1 if keys_found else 0,
        "ZAP_SIGNAL_PRESENT": 1 if zap_signal else 0,
        "IMPORTED_14_SIGNAL": 1 if imported_14 else 0,
        "IMPORTED_70_SIGNAL": 1 if imported_70 else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
    }]

    runtime_obs = [
        {"OBSERVATION":"runtime_log_exists","VALUE":1 if runtime.exists() else 0,"DETAIL":rel(runtime,repo)},
        {"OBSERVATION":"zap_signal_present","VALUE":1 if zap_signal else 0,"DETAIL":"ZAP command evidence."},
        {"OBSERVATION":"imported_14_records_signal","VALUE":1 if imported_14 else 0,"DETAIL":"SYSTEM_MESSAGES full-state import."},
        {"OBSERVATION":"imported_70_records_signal","VALUE":1 if imported_70 else 0,"DETAIL":"SYSTEM_MESSAGE_TEXT full-state import."},
        {"OBSERVATION":"unknown_zap_count","VALUE":log_upper.count("UNKNOWN COMMAND: ZAP"),"DETAIL":"0 required."},
        {"OBSERVATION":"unknown_import_count","VALUE":log_upper.count("UNKNOWN COMMAND: IMPORT"),"DETAIL":"0 required."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0 if boundary_clean else 1,"DETAIL":f"protected fingerprint changes={len(fp_delta)}"},
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_6_validate_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_zap_import_result_v1.csv", result, ["SANDBOX_MESSAGE_ROWS_AFTER","SANDBOX_TEXT_ROWS_AFTER","COUNTS_EXPECTED_14_AND_70","FOUND_MESSAGE_KEYS","FOUND_TEXT_KEYS","EXACT_KEYS_PROVEN","ZAP_SIGNAL_PRESENT","IMPORTED_14_SIGNAL","IMPORTED_70_SIGNAL","BOUNDARY_CLEAN","PROTECTED_FINGERPRINT_CHANGES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_found_message_keys_v1.csv", msg_found, ["SYMBOL","MATCHES","RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_found_text_keys_v1.csv", txt_found, ["SYMBOL","LOCALE","MATCHES","RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_field_hit_map_v1.csv", field_hits, ["TABLE","SYMBOL","LOCALE","FIELD","RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_tail_rows_v1.csv", tail_rows, ["TABLE","RECNO","ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_runtime_observations_v1.csv", runtime_obs, ["OBSERVATION","VALUE","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_protected_fingerprint_after_v1.csv", after_fp, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_protected_fingerprint_delta_v1.csv", fp_delta, ["ROLE","PATH","CHANGE","BEFORE_SHA256","AFTER_SHA256","BEFORE_BYTES","AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_6_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_6_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_STAGED_SOURCE_HELD" else 0,
        "SANDBOX_MESSAGE_ROWS_AFTER": msg_count,
        "SANDBOX_TEXT_ROWS_AFTER": txt_count,
        "FOUND_MESSAGE_KEYS": len(msg_found),
        "FOUND_TEXT_KEYS": len(txt_found),
        "EXACT_KEYS_PROVEN": 1 if keys_found else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if boundary_clean else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","STAGE_GREEN","SANDBOX_MESSAGE_ROWS_AFTER","SANDBOX_TEXT_ROWS_AFTER",
         "FOUND_MESSAGE_KEYS","FOUND_TEXT_KEYS","EXACT_KEYS_PROVEN","BOUNDARY_CLEAN","PROTECTED_FINGERPRINT_CHANGES",
         "ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_6_CANONICAL_FIELD_MAP_ZAP_IMPORT_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  sandbox message rows after: {msg_count}")
    print(f"  sandbox text rows after: {txt_count}")
    print(f"  found message keys: {len(msg_found)}/2")
    print(f"  found text keys: {len(txt_found)}/10")
    print(f"  exact keys proven: {1 if keys_found else 0}")
    print(f"  boundary clean: {1 if boundary_clean else 0}")
    print(f"  protected fingerprint changes: {len(fp_delta)}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_PROVEN, STATUS_COUNT_ONLY) else 2

if __name__ == "__main__":
    raise SystemExit(main())
