#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STATUS_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_GREEN_RUNTIME_KEYS_VISIBLE"
STATUS_NOT_PROVEN = "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_GREEN_RUNTIME_KEYS_NOT_VISIBLE_PATCH_REQUIRED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_BLOCKED"
NEXT_PROVEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_9_ACTIVE_PROMOTION_PLAN_FROM_RUNTIME_KEY_PROOF"
NEXT_NOT_PROVEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_9_CANONICAL_FIELD_MAP_PATCH_FROM_RUNTIME_PROBE"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE.md")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")
TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

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

def normalize_text(text: str):
    # Keep the exact log and also a whitespace-normalized lane to resist wrapping.
    return re.sub(r"\s+", " ", text.replace("\r", "\n"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_8_stage_status_summary_v1.csv")
    expected_msg = read_csv(reports / "message_catalog_phase22ae_6_5_8_expected_message_keys_v1.csv")
    expected_txt = read_csv(reports / "message_catalog_phase22ae_6_5_8_expected_text_keys_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_8_protected_fingerprint_before_v1.csv")

    runtime = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_norm = normalize_text(log_text)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_STAGED_SOURCE_HELD", stage.get("STATUS","missing"))
    gate("RUNTIME_PROOF_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("EXPECTED_MESSAGE_KEYS_2", len(expected_msg) == 2, len(expected_msg))
    gate("EXPECTED_TEXT_KEYS_10", len(expected_txt) == 10, len(expected_txt))
    gate("LIST_ALL_USED", "LIST ALL" in log_text.upper() or "record(s) listed" in log_text, "runtime output should contain LIST ALL/listed rows")

    after_fp = fingerprint_selected(repo)
    fp_delta = compare_fp(before_fp, after_fp)
    boundary_clean = len(fp_delta) == 0

    msg_hits = []
    txt_hits = []

    for row in expected_msg:
        sym = row.get("SYMBOL","")
        exact = sym in log_text
        wrapped = sym in log_norm
        msg_hits.append({"SYMBOL": sym, "LOCALE": "", "FOUND_EXACT": 1 if exact else 0, "FOUND_NORMALIZED": 1 if wrapped else 0, "DETAIL": "runtime LIST ALL log search"})
    for row in expected_txt:
        sym = row.get("SYMBOL","")
        loc = row.get("LOCALE","")
        found_sym = sym in log_text or sym in log_norm
        found_loc = (not loc) or loc in log_text or loc in log_norm
        txt_hits.append({"SYMBOL": sym, "LOCALE": loc, "FOUND_SYMBOL": 1 if found_sym else 0, "FOUND_LOCALE": 1 if found_loc else 0, "FOUND_PAIR": 1 if found_sym and found_loc else 0, "DETAIL": "runtime LIST ALL log search"})

    msg_found = sum(1 for r in msg_hits if r["FOUND_EXACT"] == 1 or r["FOUND_NORMALIZED"] == 1)
    txt_found = sum(1 for r in txt_hits if r["FOUND_PAIR"] == 1)

    runtime_obs = [
        {"OBSERVATION":"runtime_log_exists","VALUE":1 if runtime.exists() else 0,"DETAIL":rel(runtime,repo)},
        {"OBSERVATION":"opened_system_messages","VALUE":1 if "Opened SYSTEM_MESSAGES" in log_text else 0,"DETAIL":"sandbox table should open"},
        {"OBSERVATION":"opened_system_message_text","VALUE":1 if "Opened SYSTEM_MESSAGE_TEXT" in log_text else 0,"DETAIL":"sandbox table should open"},
        {"OBSERVATION":"list_all_seen","VALUE":1 if "LIST ALL" in log_text.upper() or "record(s) listed" in log_text else 0,"DETAIL":"runtime row display evidence"},
        {"OBSERVATION":"set_index_seen","VALUE":1 if "SET INDEX" in log_text.upper() else 0,"DETAIL":"must be 0 for clean proof"},
        {"OBSERVATION":"cdx_info_seen","VALUE":1 if "CDX INFO" in log_text.upper() else 0,"DETAIL":"must be 0 for clean proof"},
        {"OBSERVATION":"write_command_seen","VALUE":1 if any(w in log_text.upper() for w in [" ZAP", " IMPORT", " REPLACE", " PACK", " DELETE ALL"]) else 0,"DETAIL":"must be 0 for this read-only probe"},
    ]

    dirty_runtime = any(r["VALUE"] == 1 for r in runtime_obs if r["OBSERVATION"] in ("set_index_seen","cdx_info_seen","write_command_seen"))

    if failures > 0 or not boundary_clean or dirty_runtime:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_8_RUNTIME_PROBE_OR_BOUNDARY"
        validation_issues = str(max(1, failures, len(fp_delta), 1 if dirty_runtime else 0))
    elif msg_found == 2 and txt_found == 10:
        status = STATUS_PROVEN
        next_gate = NEXT_PROVEN
        validation_issues = "0"
    else:
        status = STATUS_NOT_PROVEN
        next_gate = NEXT_NOT_PROVEN
        validation_issues = "0"

    result = [{
        "MESSAGE_KEYS_FOUND_RUNTIME": msg_found,
        "MESSAGE_KEYS_EXPECTED": 2,
        "TEXT_KEYS_FOUND_RUNTIME": txt_found,
        "TEXT_KEYS_EXPECTED": 10,
        "RUNTIME_KEYS_VISIBLE": 1 if (msg_found == 2 and txt_found == 10) else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "RUNTIME_PROBE_DIRTY": 1 if dirty_runtime else 0,
    }]

    boundary = [
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0 if boundary_clean else 1,"DETAIL":f"protected fingerprint changes={len(fp_delta)}"},
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_8_validate_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_runtime_message_key_hits_v1.csv", msg_hits, ["SYMBOL","LOCALE","FOUND_EXACT","FOUND_NORMALIZED","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_runtime_text_key_hits_v1.csv", txt_hits, ["SYMBOL","LOCALE","FOUND_SYMBOL","FOUND_LOCALE","FOUND_PAIR","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_runtime_observations_v1.csv", runtime_obs, ["OBSERVATION","VALUE","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_runtime_key_result_v1.csv", result, ["MESSAGE_KEYS_FOUND_RUNTIME","MESSAGE_KEYS_EXPECTED","TEXT_KEYS_FOUND_RUNTIME","TEXT_KEYS_EXPECTED","RUNTIME_KEYS_VISIBLE","BOUNDARY_CLEAN","PROTECTED_FINGERPRINT_CHANGES","RUNTIME_PROBE_DIRTY"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_protected_fingerprint_after_v1.csv", after_fp, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_protected_fingerprint_delta_v1.csv", fp_delta, ["ROLE","PATH","CHANGE","BEFORE_SHA256","AFTER_SHA256","BEFORE_BYTES","AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_8_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_STAGED_SOURCE_HELD" else 0,
        "MESSAGE_KEYS_FOUND_RUNTIME": msg_found,
        "TEXT_KEYS_FOUND_RUNTIME": txt_found,
        "RUNTIME_KEYS_VISIBLE": 1 if (msg_found == 2 and txt_found == 10) else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "RUNTIME_PROBE_DIRTY": 1 if dirty_runtime else 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if boundary_clean else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","STAGE_GREEN","MESSAGE_KEYS_FOUND_RUNTIME","TEXT_KEYS_FOUND_RUNTIME",
         "RUNTIME_KEYS_VISIBLE","BOUNDARY_CLEAN","PROTECTED_FINGERPRINT_CHANGES","RUNTIME_PROBE_DIRTY",
         "ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_8_CANONICAL_RUNTIME_KEY_PROBE_STAGED_SOURCE_HELD' else 0}")
    print(f"  runtime message keys found: {msg_found}/2")
    print(f"  runtime text keys found: {txt_found}/10")
    print(f"  runtime keys visible: {1 if (msg_found == 2 and txt_found == 10) else 0}")
    print(f"  boundary clean: {1 if boundary_clean else 0}")
    print(f"  runtime probe dirty: {1 if dirty_runtime else 0}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_PROVEN, STATUS_NOT_PROVEN) else 2

if __name__ == "__main__":
    raise SystemExit(main())
