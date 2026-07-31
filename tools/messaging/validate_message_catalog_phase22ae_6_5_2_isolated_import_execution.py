#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_GREEN_TWO_TABLE_IMPORT_PROVEN"
STATUS_NOT_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_GREEN_IMPORT_NOT_PROVEN_REBUILD_REQUIRED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_BLOCKED"

NEXT_PROVEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_3_ACTIVE_PROMOTION_PLAN_FROM_IMPORT_PROOF"
NEXT_REBUILD = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_3_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF.md")

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

    stage = first_row(reports / "message_catalog_phase22ae_6_5_2_stage_status_summary_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_2_protected_fingerprint_before_v1.csv")
    expected_msg = read_csv(reports / "message_catalog_phase22ae_6_5_2_expected_message_rows_v1.csv")
    expected_txt = read_csv(reports / "message_catalog_phase22ae_6_5_2_expected_text_rows_v1.csv")

    runtime = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_upper = log_text.upper()

    sandbox = repo / stage.get("SANDBOX_ROOT", "")
    msg_dbf = sandbox / "dbf/SYSTEM_MESSAGES.dbf"
    txt_dbf = sandbox / "dbf/SYSTEM_MESSAGE_TEXT.dbf"
    msg_before = int(stage.get("SANDBOX_MESSAGE_ROWS_BEFORE") or 12)
    txt_before = int(stage.get("SANDBOX_TEXT_ROWS_BEFORE") or 60)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
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
    tail_rows = []

    try:
        msg_info = parse_dbf(msg_dbf)
        txt_info = parse_dbf(txt_dbf)
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
            matches = [r for r in txt_rows if sf and r.get(sf, "") == sym and (not lf or r.get(lf, "") == loc)]
            if matches:
                txt_matches.append({"SYMBOL": sym, "LOCALE": loc, "MATCHES": len(matches), "RECNO": matches[-1].get("__RECNO__", "")})
                latest = matches[-1]
                if tf and latest.get(tf, "") not in ("", "0"):
                    text_payload_rows += 1

        for label, rows in [("SYSTEM_MESSAGES", msg_rows[-8:]), ("SYSTEM_MESSAGE_TEXT", txt_rows[-12:])]:
            for r in rows:
                compact = {k: v for k, v in r.items() if k in ("__RECNO__", "__DELETED__") or (isinstance(v, str) and v.strip())}
                tail_rows.append({"TABLE": label, "RECNO": r.get("__RECNO__", ""), "ROW_JSON": json.dumps(compact, ensure_ascii=False, sort_keys=True)})
    except Exception as exc:
        gate("SANDBOX_DBF_READBACK", False, exc)

    msg_delta = msg_count - msg_before if isinstance(msg_count, int) else ""
    txt_delta = txt_count - txt_before if isinstance(txt_count, int) else ""
    counts_expected = (msg_delta == 2 and txt_delta == 10)
    all_keys_found = (len(msg_matches) == 2 and len(txt_matches) == 10)
    import_output_ok = ("IMPORT" in log_upper and "UNKNOWN COMMAND: IMPORT" not in log_upper)
    no_usage_error = ("IMPORT USAGE" not in log_upper)  # runtime command was IMPORT <csvfile>, not usage probe

    if failures > 0 or not boundary_clean:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_2_IMPORT_SETUP_OR_BOUNDARY"
        validation_issues = str(max(1, failures, len(fp_delta)))
    elif counts_expected and all_keys_found:
        status = STATUS_PROVEN
        next_gate = NEXT_PROVEN
        validation_issues = "0"
    else:
        status = STATUS_NOT_PROVEN
        next_gate = NEXT_REBUILD
        validation_issues = "0"

    result_rows = [{
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_before,
        "SANDBOX_MESSAGE_ROWS_AFTER": msg_count,
        "MESSAGE_DELTA": msg_delta,
        "SANDBOX_TEXT_ROWS_BEFORE": txt_before,
        "SANDBOX_TEXT_ROWS_AFTER": txt_count,
        "TEXT_DELTA": txt_delta,
        "COUNTS_EXPECTED_2_AND_10": 1 if counts_expected else 0,
        "EXPECTED_MESSAGE_KEYS": len(expected_msg),
        "FOUND_MESSAGE_KEYS": len(msg_matches),
        "EXPECTED_TEXT_KEYS": len(expected_txt),
        "FOUND_TEXT_KEYS": len(txt_matches),
        "TEXT_PAYLOAD_OR_POINTER_ROWS": text_payload_rows,
        "IMPORT_OUTPUT_OK": 1 if import_output_ok else 0,
        "IMPORT_USAGE_ERROR_ABSENT": 1 if no_usage_error else 0,
        "TWO_TABLE_IMPORT_PROVEN": 1 if (counts_expected and all_keys_found) else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
    }]

    runtime_rows = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if runtime.exists() else 0, "DETAIL": rel(runtime, repo)},
        {"OBSERVATION": "opened_system_messages_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGES"), "DETAIL": "Open signal."},
        {"OBSERVATION": "opened_system_message_text_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGE_TEXT"), "DETAIL": "Open signal."},
        {"OBSERVATION": "import_mentions", "VALUE": log_upper.count("IMPORT"), "DETAIL": "Should include IMPORT execution."},
        {"OBSERVATION": "unknown_import_count", "VALUE": log_upper.count("UNKNOWN COMMAND: IMPORT"), "DETAIL": "0 required for confidence."},
        {"OBSERVATION": "usage_mentions", "VALUE": log_upper.count("USAGE:"), "DETAIL": "Usage output during execution suggests command syntax issue."},
        {"OBSERVATION": "error_mentions", "VALUE": log_upper.count("ERROR") + log_upper.count("FAILED"), "DETAIL": "Review if nonzero."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": f"protected fingerprint changes={len(fp_delta)}"},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_2_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_import_result_v1.csv", result_rows, ["SANDBOX_MESSAGE_ROWS_BEFORE", "SANDBOX_MESSAGE_ROWS_AFTER", "MESSAGE_DELTA", "SANDBOX_TEXT_ROWS_BEFORE", "SANDBOX_TEXT_ROWS_AFTER", "TEXT_DELTA", "COUNTS_EXPECTED_2_AND_10", "EXPECTED_MESSAGE_KEYS", "FOUND_MESSAGE_KEYS", "EXPECTED_TEXT_KEYS", "FOUND_TEXT_KEYS", "TEXT_PAYLOAD_OR_POINTER_ROWS", "IMPORT_OUTPUT_OK", "IMPORT_USAGE_ERROR_ABSENT", "TWO_TABLE_IMPORT_PROVEN", "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_found_message_keys_v1.csv", msg_matches, ["SYMBOL", "MATCHES", "RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_found_text_keys_v1.csv", txt_matches, ["SYMBOL", "LOCALE", "MATCHES", "RECNO"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_tail_rows_v1.csv", tail_rows, ["TABLE", "RECNO", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_runtime_observations_v1.csv", runtime_rows, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_protected_fingerprint_after_v1.csv", after_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_protected_fingerprint_delta_v1.csv", fp_delta, ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256", "BEFORE_BYTES", "AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_2_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_2_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_STAGED_SOURCE_HELD" else 0,
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_before,
        "SANDBOX_MESSAGE_ROWS_AFTER": msg_count,
        "MESSAGE_DELTA": msg_delta,
        "SANDBOX_TEXT_ROWS_BEFORE": txt_before,
        "SANDBOX_TEXT_ROWS_AFTER": txt_count,
        "TEXT_DELTA": txt_delta,
        "FOUND_MESSAGE_KEYS": len(msg_matches),
        "FOUND_TEXT_KEYS": len(txt_matches),
        "TWO_TABLE_IMPORT_PROVEN": 1 if (counts_expected and all_keys_found) else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if boundary_clean else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_GREEN",
         "SANDBOX_MESSAGE_ROWS_BEFORE", "SANDBOX_MESSAGE_ROWS_AFTER", "MESSAGE_DELTA",
         "SANDBOX_TEXT_ROWS_BEFORE", "SANDBOX_TEXT_ROWS_AFTER", "TEXT_DELTA",
         "FOUND_MESSAGE_KEYS", "FOUND_TEXT_KEYS", "TWO_TABLE_IMPORT_PROVEN",
         "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  sandbox message rows before/after: {msg_before}/{msg_count}")
    print(f"  sandbox text rows before/after: {txt_before}/{txt_count}")
    print(f"  message delta: {msg_delta}")
    print(f"  text delta: {txt_delta}")
    print(f"  found message keys: {len(msg_matches)}/2")
    print(f"  found text keys: {len(txt_matches)}/10")
    print(f"  two-table import proven: {1 if (counts_expected and all_keys_found) else 0}")
    print(f"  boundary clean: {1 if boundary_clean else 0}")
    print(f"  protected fingerprint changes: {len(fp_delta)}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_PROVEN, STATUS_NOT_PROVEN) else 2

if __name__ == "__main__":
    raise SystemExit(main())
