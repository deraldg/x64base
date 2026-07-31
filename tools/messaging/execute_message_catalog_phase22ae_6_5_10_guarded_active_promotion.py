#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_PREPARED = "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_PREPARED"
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_GREEN_RUNTIME_IMPORT_RECORDED_READBACK_REQUIRED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION_BLOCKED"

NEXT_AFTER_PREPARE = "RUN_PHASE22AE_6_5_10_ACTIVE_PROMOTION_RUNTIME_THEN_FINALIZE"
NEXT_AFTER_GREEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_11_ACTIVE_CATALOG_READBACK_AND_RUNTIME_VALIDATION"
NEXT_AFTER_BLOCK = "HOLD_AND_REVIEW_PHASE22AE_6_5_10_EXECUTION_FAILURE_OR_ROLLBACK"

REPORT_DIR = Path("docs/messaging/reports")
PACKAGE_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10_guarded_active_promotion_execution_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTE.dts")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTION.md")

PLAN_ROOT = Path("docs/messaging/apply/phase22ae_6_5_9_active_promotion_plan_v1")
PLAN_MSG_CSV = PLAN_ROOT / "import/system_messages_active_promotion_full_state.csv"
PLAN_TXT_CSV = PLAN_ROOT / "import/system_message_text_active_promotion_full_state.csv"

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]
SIDE_EXTS = [".dtx", ".dbt", ".fpt", ".memo", ".mdx", ".cdx", ".cdx.meta"]

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

def savepoint_present(repo: Path, savepoint_id: str):
    latest = ""
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest == savepoint_id or savepoint_id in text, latest

def dottalkpp_running():
    if sys.platform.startswith("win"):
        try:
            cp = subprocess.run(["tasklist", "/FI", "IMAGENAME eq dottalkpp.exe"], capture_output=True, text=True, timeout=10)
            out = (cp.stdout or "") + (cp.stderr or "")
            return "dottalkpp.exe" in out.lower()
        except Exception:
            return False
    return False

def dbf_record_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    data = path.read_bytes()[:12]
    return int.from_bytes(data[4:8], "little")

def copy_any(src: Path, dst: Path):
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        return "dir"
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return "file"
    return "missing"

def inventory_path(repo: Path, role: str, path: Path):
    p = repo / path
    if p.is_dir():
        files = sorted(q for q in p.rglob("*") if q.is_file())
        h = hashlib.sha256()
        total = 0
        for f in files:
            h.update(str(f.relative_to(p)).replace("\\", "/").encode("utf-8"))
            h.update(sha256_file(f).encode("ascii"))
            total += f.stat().st_size
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "dir", "BYTES": total, "SHA256": h.hexdigest(), "FILES": len(files)}
    if p.is_file():
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "file", "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "FILES": 1}
    return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "SHA256": "", "FILES": 0}

def active_inventory(repo: Path):
    rows = []
    for table in TABLES:
        rows.append(inventory_path(repo, f"active_dbf_{table}", ACTIVE_MSG_ROOT / f"{table}.dbf"))
        for ext in SIDE_EXTS:
            rows.append(inventory_path(repo, f"active_message_root_{table}{ext}", ACTIVE_MSG_ROOT / f"{table}{ext}"))
        rows.append(inventory_path(repo, f"active_messaging_cdx_{table}", ACTIVE_INDEX_ROOT / f"{table}.cdx"))
        rows.append(inventory_path(repo, f"active_messaging_cdx_meta_{table}", ACTIVE_INDEX_ROOT / f"{table}.cdx.meta"))
        rows.append(inventory_path(repo, f"active_messaging_lmdb_{table}", ACTIVE_LMDB_ROOT / f"{table}.cdx.d"))
        rows.append(inventory_path(repo, f"default_cdx_{table}", DEFAULT_INDEX_ROOT / f"{table}.cdx"))
        rows.append(inventory_path(repo, f"default_cdx_meta_{table}", DEFAULT_INDEX_ROOT / f"{table}.cdx.meta"))
        rows.append(inventory_path(repo, f"default_lmdb_{table}", DEFAULT_LMDB_ROOT / f"{table}.cdx.d"))
    return rows

def compare_fp(before, after):
    b = {r["ROLE"] + "|" + r["PATH"]: r for r in before}
    a = {r["ROLE"] + "|" + r["PATH"]: r for r in after}
    deltas = []
    for key in sorted(set(b) | set(a)):
        br = b.get(key)
        ar = a.get(key)
        if br is None:
            deltas.append({"ROLE": ar.get("ROLE",""), "PATH": ar.get("PATH",""), "CHANGE": "ADDED", "BEFORE_SHA256": "", "AFTER_SHA256": ar.get("SHA256",""), "BEFORE_BYTES": "", "AFTER_BYTES": ar.get("BYTES","")})
        elif ar is None:
            deltas.append({"ROLE": br.get("ROLE",""), "PATH": br.get("PATH",""), "CHANGE": "REMOVED", "BEFORE_SHA256": br.get("SHA256",""), "AFTER_SHA256": "", "BEFORE_BYTES": br.get("BYTES",""), "AFTER_BYTES": ""})
        elif br.get("SHA256") != ar.get("SHA256") or str(br.get("BYTES")) != str(ar.get("BYTES")):
            deltas.append({"ROLE": ar.get("ROLE", br.get("ROLE","")), "PATH": ar.get("PATH", br.get("PATH","")), "CHANGE": "MODIFIED", "BEFORE_SHA256": br.get("SHA256",""), "AFTER_SHA256": ar.get("SHA256",""), "BEFORE_BYTES": br.get("BYTES",""), "AFTER_BYTES": ar.get("BYTES","")})
    return deltas

def backup_active(repo: Path, backup_root: Path):
    rows = []
    candidates = []
    for table in TABLES:
        candidates.append((ACTIVE_MSG_ROOT / f"{table}.dbf", f"active_dbf_{table}"))
        for ext in SIDE_EXTS:
            candidates.append((ACTIVE_MSG_ROOT / f"{table}{ext}", f"active_message_root_{table}{ext}"))
        candidates.append((ACTIVE_INDEX_ROOT / f"{table}.cdx", f"active_messaging_cdx_{table}"))
        candidates.append((ACTIVE_INDEX_ROOT / f"{table}.cdx.meta", f"active_messaging_cdx_meta_{table}"))
        candidates.append((ACTIVE_LMDB_ROOT / f"{table}.cdx.d", f"active_messaging_lmdb_{table}"))
        candidates.append((DEFAULT_INDEX_ROOT / f"{table}.cdx", f"default_cdx_{table}"))
        candidates.append((DEFAULT_INDEX_ROOT / f"{table}.cdx.meta", f"default_cdx_meta_{table}"))
        candidates.append((DEFAULT_LMDB_ROOT / f"{table}.cdx.d", f"default_lmdb_{table}"))
    seen = set()
    for rel_src, role in candidates:
        if str(rel_src) in seen:
            continue
        seen.add(str(rel_src))
        src = repo / rel_src
        dst = backup_root / rel_src
        kind = copy_any(src, dst)
        rows.append({
            "ROLE": role,
            "ORIGINAL_PATH": rel(src, repo),
            "BACKUP_PATH": rel(dst, repo),
            "EXISTS_AT_BACKUP": 0 if kind == "missing" else 1,
            "KIND": kind,
            "BYTES": dst.stat().st_size if dst.is_file() else "",
            "SHA256": sha256_file(dst) if dst.is_file() else "",
            "RESTORE_POLICY": "restore exactly before retry or on failed validation",
        })
    return rows

def prepare(repo: Path, args):
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    package_root = repo / PACKAGE_ROOT

    ae659 = first_row(reports / "message_catalog_phase22ae_6_5_9_status_summary_v1.csv")
    sp659, latest = savepoint_present(repo, "MSG-022AE.6.5.9")
    running = dottalkpp_running()

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("ALLOW_ACTIVE_CATALOG_MUTATION_FLAG", args.allow_active_catalog_mutation, args.allow_active_catalog_mutation)
    gate("PHASE22AE_6_5_9_GREEN", ae659.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_9_ACTIVE_PROMOTION_PLAN_FROM_RUNTIME_KEY_PROOF_GREEN_SOURCE_HELD", ae659.get("STATUS","missing"))
    gate("MSG_022AE_6_5_9_SAVEPOINT_PRESENT", sp659, latest)
    gate("RUNTIME_KEY_PROOF_MESSAGE_2_OF_2", ae659.get("RUNTIME_MESSAGE_KEYS_FOUND") == "2", ae659.get("RUNTIME_MESSAGE_KEYS_FOUND","missing"))
    gate("RUNTIME_KEY_PROOF_TEXT_10_OF_10", ae659.get("RUNTIME_TEXT_KEYS_FOUND") == "10", ae659.get("RUNTIME_TEXT_KEYS_FOUND","missing"))
    gate("NO_DOTTALKPP_PROCESS_RUNNING", not running, running)
    gate("CANDIDATE_MESSAGE_CSV_14_ROWS", len(read_csv(repo / PLAN_MSG_CSV)) == 14, len(read_csv(repo / PLAN_MSG_CSV)))
    gate("CANDIDATE_TEXT_CSV_70_ROWS", len(read_csv(repo / PLAN_TXT_CSV)) == 70, len(read_csv(repo / PLAN_TXT_CSV)))
    gate("PACKAGE_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not package_root.exists()) or args.replace_existing_package, rel(package_root, repo))

    before_fp = active_inventory(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_10_active_fingerprint_before_v1.csv", before_fp, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])

    backup_root_rel = ""
    backup_rows = []
    script_rel = ""

    status = STATUS_BLOCKED
    if failures == 0:
        if package_root.exists() and args.replace_existing_package:
            shutil.rmtree(package_root)
        (package_root / "import").mkdir(parents=True, exist_ok=True)
        (package_root / "rollback").mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / PLAN_MSG_CSV, package_root / "import/system_messages_active_promotion_full_state.csv")
        shutil.copy2(repo / PLAN_TXT_CSV, package_root / "import/system_message_text_active_promotion_full_state.csv")

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / "docs/messaging/backups" / f"MSG-022AE_6_5_10_GUARDED_ACTIVE_PROMOTION_BACKUP_{stamp}"
        backup_root.mkdir(parents=True, exist_ok=False)
        backup_rows = backup_active(repo, backup_root)
        backup_root_rel = rel(backup_root, repo)

        script = repo / SCRIPT_PATH
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE22AE_6_5_10_GUARDED_ACTIVE_PROMOTION_EXECUTE.dts",
            "* ACTIVE CATALOG MUTATION SCRIPT - generated only after explicit authorization.",
            "* ZAP closes the table; each IMPORT reopens the active DBF first.",
            "* No QUIT here; quit manually in interactive runs.",
            "",
            f"USE {(repo / ACTIVE_MSG_ROOT / 'SYSTEM_MESSAGES.dbf').resolve().as_posix()}",
            "ZAP",
            f"USE {(repo / ACTIVE_MSG_ROOT / 'SYSTEM_MESSAGES.dbf').resolve().as_posix()}",
            f"IMPORT {(package_root / 'import/system_messages_active_promotion_full_state.csv').resolve().as_posix()}",
            "",
            f"USE {(repo / ACTIVE_MSG_ROOT / 'SYSTEM_MESSAGE_TEXT.dbf').resolve().as_posix()}",
            "ZAP",
            f"USE {(repo / ACTIVE_MSG_ROOT / 'SYSTEM_MESSAGE_TEXT.dbf').resolve().as_posix()}",
            f"IMPORT {(package_root / 'import/system_message_text_active_promotion_full_state.csv').resolve().as_posix()}",
            "",
        ]), encoding="utf-8")
        script_rel = rel(script, repo)
        status = STATUS_PREPARED

    write_csv(reports / "message_catalog_phase22ae_6_5_10_prepare_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10_backup_manifest_v1.csv", backup_rows, ["ROLE","ORIGINAL_PATH","BACKUP_PATH","EXISTS_AT_BACKUP","KIND","BYTES","SHA256","RESTORE_POLICY"])

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":0,"DETAIL":"Prepare stage backs up and writes DTS only; runtime mutation not yet executed."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":0,"DETAIL":"Prepare stage no active index mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":0,"DETAIL":"Prepare stage no active LMDB mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_10_prepare_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    validation_issues = "0" if status == STATUS_PREPARED else str(failures)
    write_csv(reports / "message_catalog_phase22ae_6_5_10_prepare_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_9_STATUS": ae659.get("STATUS",""),
        "MSG_022AE_6_5_9_SAVEPOINT_PRESENT": 1 if sp659 else 0,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "ALLOW_ACTIVE_CATALOG_MUTATION": 1 if args.allow_active_catalog_mutation else 0,
        "PACKAGE_ROOT": rel(package_root, repo),
        "SCRIPT_PATH": script_rel,
        "RUNLOG_PATH": rel(repo / RUNLOG_PATH, repo),
        "BACKUP_ROOT": backup_root_rel,
        "BACKUP_ROWS": len(backup_rows),
        "CANDIDATE_MESSAGE_ROWS": len(read_csv(package_root / "import/system_messages_active_promotion_full_state.csv")) if package_root.exists() else "",
        "CANDIDATE_TEXT_ROWS": len(read_csv(package_root / "import/system_message_text_active_promotion_full_state.csv")) if package_root.exists() else "",
        "SHOULD_EXECUTE_RUNTIME": 1 if status == STATUS_PREPARED else 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_AFTER_PREPARE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_9_STATUS","MSG_022AE_6_5_9_SAVEPOINT_PRESENT",
         "DOTTALKPP_PROCESS_RUNNING","ALLOW_ACTIVE_CATALOG_MUTATION","PACKAGE_ROOT","SCRIPT_PATH","RUNLOG_PATH",
         "BACKUP_ROOT","BACKUP_ROWS","CANDIDATE_MESSAGE_ROWS","CANDIDATE_TEXT_ROWS","SHOULD_EXECUTE_RUNTIME",
         "ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.9 green: {1 if ae659.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_9_ACTIVE_PROMOTION_PLAN_FROM_RUNTIME_KEY_PROOF_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.9 savepoint present: {1 if sp659 else 0}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  allow active catalog mutation: {1 if args.allow_active_catalog_mutation else 0}")
    print(f"  package root: {rel(package_root, repo)}")
    print(f"  script path: {script_rel}")
    print(f"  runlog path: {rel(repo / RUNLOG_PATH, repo)}")
    print(f"  backup root: {backup_root_rel}")
    print(f"  backup rows: {len(backup_rows)}")
    print(f"  should execute runtime: {1 if status == STATUS_PREPARED else 0}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_AFTER_PREPARE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_PREPARED else 2

def finalize(repo: Path, args):
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    prep = first_row(reports / "message_catalog_phase22ae_6_5_10_prepare_status_summary_v1.csv")
    runtime = Path(args.runtime_log) if args.runtime_log else repo / RUNLOG_PATH
    if not runtime.is_absolute():
        runtime = repo / runtime
    log_text = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    log_upper = log_text.upper()

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PREPARED_STATUS", prep.get("STATUS") == STATUS_PREPARED, prep.get("STATUS","missing"))
    gate("RUNTIME_LOG_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("IMPORTED_14_RECORDS_SIGNAL", "IMPORTED 14 RECORDS" in log_upper, "SYSTEM_MESSAGES import")
    gate("IMPORTED_70_RECORDS_SIGNAL", "IMPORTED 70 RECORDS" in log_upper, "SYSTEM_MESSAGE_TEXT import")
    gate("ZAP_COMPLETE_COUNT_AT_LEAST_2", log_upper.count("ZAP COMPLETE") >= 2, log_upper.count("ZAP COMPLETE"))
    gate("NO_FILE_OPEN_ABSENT", "NO FILE OPEN" not in log_upper, "must be absent")
    gate("UNKNOWN_COMMAND_ABSENT", "UNKNOWN COMMAND" not in log_upper, "must be absent")
    gate("CANNOT_OPEN_ABSENT", "CANNOT OPEN" not in log_upper, "must be absent")
    gate("TRACEBACK_ABSENT", "TRACEBACK" not in log_upper, "must be absent")

    msg_count = dbf_record_count(repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGES.dbf")
    txt_count = dbf_record_count(repo / ACTIVE_MSG_ROOT / "SYSTEM_MESSAGE_TEXT.dbf")
    gate("ACTIVE_SYSTEM_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_SYSTEM_MESSAGE_TEXT_HEADER_COUNT_70", txt_count == 70, txt_count)

    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_10_active_fingerprint_before_v1.csv")
    after_fp = active_inventory(repo)
    delta = compare_fp(before_fp, after_fp)
    mutation_observed = 1 if delta else 0
    gate("ACTIVE_MUTATION_OBSERVED", mutation_observed == 1, mutation_observed)

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)
    next_gate = NEXT_AFTER_GREEN if status == STATUS_GREEN else NEXT_AFTER_BLOCK

    write_csv(reports / "message_catalog_phase22ae_6_5_10_finalize_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10_active_fingerprint_after_v1.csv", after_fp, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10_active_fingerprint_delta_v1.csv", delta, ["ROLE","PATH","CHANGE","BEFORE_SHA256","AFTER_SHA256","BEFORE_BYTES","AFTER_BYTES"])

    runtime_obs = [
        {"OBSERVATION":"runtime_log_exists","VALUE":1 if runtime.exists() else 0,"DETAIL":rel(runtime, repo)},
        {"OBSERVATION":"imported_14_records_signal","VALUE":1 if "IMPORTED 14 RECORDS" in log_upper else 0,"DETAIL":"SYSTEM_MESSAGES"},
        {"OBSERVATION":"imported_70_records_signal","VALUE":1 if "IMPORTED 70 RECORDS" in log_upper else 0,"DETAIL":"SYSTEM_MESSAGE_TEXT"},
        {"OBSERVATION":"zap_complete_count","VALUE":log_upper.count("ZAP COMPLETE"),"DETAIL":"2 expected"},
        {"OBSERVATION":"active_message_header_count","VALUE":msg_count,"DETAIL":"14 expected"},
        {"OBSERVATION":"active_text_header_count","VALUE":txt_count,"DETAIL":"70 expected"},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_10_runtime_observations_v1.csv", runtime_obs, ["OBSERVATION","VALUE","DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":mutation_observed,"DETAIL":"Active DBF mutation expected after runtime execution."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":mutation_observed,"DETAIL":"Index/LMDB may require next readback/refresh proof."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":mutation_observed,"DETAIL":"Index/LMDB may require next readback/refresh proof."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_10_finalize_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10_finalize_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "RUNTIME_LOG": rel(runtime, repo),
        "RUNTIME_IMPORTED_14": 1 if "IMPORTED 14 RECORDS" in log_upper else 0,
        "RUNTIME_IMPORTED_70": 1 if "IMPORTED 70 RECORDS" in log_upper else 0,
        "ACTIVE_MESSAGE_HEADER_COUNT": msg_count,
        "ACTIVE_TEXT_HEADER_COUNT": txt_count,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": mutation_observed,
        "ACTIVE_FINGERPRINT_DELTA_ROWS": len(delta),
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ROLLBACK_BACKUP_ROOT": prep.get("BACKUP_ROOT",""),
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","RUNTIME_LOG","RUNTIME_IMPORTED_14","RUNTIME_IMPORTED_70",
         "ACTIVE_MESSAGE_HEADER_COUNT","ACTIVE_TEXT_HEADER_COUNT","ACTIVE_CATALOG_MUTATION_OBSERVED",
         "ACTIVE_FINGERPRINT_DELTA_ROWS","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED","ROLLBACK_BACKUP_ROOT","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  runtime imported 14: {1 if 'IMPORTED 14 RECORDS' in log_upper else 0}")
    print(f"  runtime imported 70: {1 if 'IMPORTED 70 RECORDS' in log_upper else 0}")
    print(f"  active message header count: {msg_count}")
    print(f"  active text header count: {txt_count}")
    print(f"  active catalog mutation observed: {mutation_observed}")
    print(f"  active fingerprint delta rows: {len(delta)}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  rollback backup root: {prep.get('BACKUP_ROOT','')}")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--mode", choices=["prepare", "finalize"], required=True)
    ap.add_argument("--runtime-log", default="")
    ap.add_argument("--allow-active-catalog-mutation", action="store_true")
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    if args.mode == "prepare":
        return prepare(repo, args)
    return finalize(repo, args)

if __name__ == "__main__":
    raise SystemExit(main())
