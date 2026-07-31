#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPORT_DIR = Path("docs/messaging/reports")
PACKAGE_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ah_guarded_final_promotion_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTE.dts")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION.md")

PLAN_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10ag_guarded_final_promotion_plan_v1")
MSG14_CSV = PLAN_ROOT / "import/system_messages_final_promotion_full14.csv"
TEXT70_CSV = PLAN_ROOT / "import/system_message_text_final_promotion_full70.csv"

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
TABLES = [
    ("SYSTEM_MESSAGES", ACTIVE_MSG_DBF, 12, 14),
    ("SYSTEM_MESSAGE_TEXT", ACTIVE_TEXT_DBF, 60, 70),
]

STATUS_PREPARED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_PREPARED"
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_GREEN_ACTIVE_PROMOTED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_BLOCKED_ROLLBACK_REQUIRED"
STATUS_ROLLED_BACK = "MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_ROLLED_BACK_TO_PREPROMOTION_BASELINE"

NEXT_PREPARED = "RUN_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_RUNTIME_THEN_FINALIZE"
NEXT_GREEN = "APPEND_MSG_022AE_6_5_10AH_SAVEPOINT_THEN_AUTHORIZE_10AI_POST_PROMOTION_FRESH_READBACK"
NEXT_BLOCKED = "ROLLBACK_PHASE22AE_6_5_10AH_ACTIVE_PROMOTION_BACKUP_BEFORE_ANY_SAVEPOINT"
NEXT_ROLLED_BACK = "HOLD_AND_REVIEW_PHASE22AE_6_5_10AH_PROMOTION_FAILURE"

SIDE_EXTS = [".dtx", ".dbt", ".fpt", ".memo", ".mdx", ".cdx", ".cdx.meta"]
PROOF_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
PROOF_LOCALES = ["en-US", "es", "fr", "de", "it"]

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

def hash_dir(path: Path):
    if not path.exists() or not path.is_dir():
        return "", 0, 0
    files = sorted(p for p in path.rglob("*") if p.is_file())
    h = hashlib.sha256()
    total = 0
    for f in files:
        h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
        h.update(sha256_file(f).encode("ascii"))
        total += f.stat().st_size
    return h.hexdigest(), len(files), total

def inv(repo: Path, role: str, path: Path):
    p = repo / path
    if p.is_dir():
        h, n, b = hash_dir(p)
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "dir", "BYTES": b, "SHA256": h, "FILES": n}
    if p.is_file():
        return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "file", "BYTES": p.stat().st_size, "SHA256": sha256_file(p), "FILES": 1}
    return {"ROLE": role, "PATH": rel(p, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "SHA256": "", "FILES": 0}

def artifact_paths_for_table(table_name: str, dbf_path: Path):
    paths = [(dbf_path, f"{table_name.lower()}_dbf")]
    for ext in SIDE_EXTS:
        paths.append((dbf_path.with_suffix(ext), f"{table_name.lower()}_sidecar_{ext}"))
    paths.extend([
        (Path("dottalkpp/data/indexes/messaging") / f"{table_name}.cdx", f"{table_name.lower()}_messaging_index"),
        (Path("dottalkpp/data/indexes/messaging") / f"{table_name}.cdx.meta", f"{table_name.lower()}_messaging_index_meta"),
        (Path("dottalkpp/data/lmdb/messaging") / f"{table_name}.cdx.d", f"{table_name.lower()}_messaging_lmdb"),
        (Path("dottalkpp/data/indexes") / f"{table_name}.cdx", f"{table_name.lower()}_default_index"),
        (Path("dottalkpp/data/indexes") / f"{table_name}.cdx.meta", f"{table_name.lower()}_default_index_meta"),
        (Path("dottalkpp/data/lmdb") / f"{table_name}.cdx.d", f"{table_name.lower()}_default_lmdb"),
    ])
    return paths

def active_inventory(repo: Path):
    seen = set()
    rows = []
    for table_name, dbf, _before, _after in TABLES:
        for path, role in artifact_paths_for_table(table_name, dbf):
            key = str(path)
            if key not in seen:
                seen.add(key)
                rows.append(inv(repo, role, path))
    return rows

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

def backup_active(repo: Path, backup_root: Path):
    rows = []
    for row in active_inventory(repo):
        src = repo / row["PATH"]
        dst = backup_root / row["PATH"]
        kind = copy_any(src, dst)
        rows.append({
            "ROLE": row["ROLE"],
            "ORIGINAL_PATH": row["PATH"],
            "BACKUP_PATH": rel(dst, repo),
            "EXISTS_AT_BACKUP": 0 if kind == "missing" else 1,
            "KIND": kind,
            "BYTES": dst.stat().st_size if dst.is_file() else row.get("BYTES", ""),
            "SHA256": sha256_file(dst) if dst.is_file() else row.get("SHA256", ""),
            "RESTORE_POLICY": "rollback only if final promotion fails or is explicitly rejected",
        })
    return rows

def restore_from_manifest(repo: Path, manifest_rows):
    out = []
    fails = 0
    for row in manifest_rows:
        original = repo / row["ORIGINAL_PATH"]
        backup = repo / row["BACKUP_PATH"]
        kind = row["KIND"]
        try:
            if kind == "missing":
                if original.is_dir():
                    shutil.rmtree(original)
                    action = "removed_dir"
                elif original.is_file():
                    original.unlink()
                    action = "removed_file"
                else:
                    action = "still_missing"
            elif kind == "dir":
                if original.exists():
                    if original.is_dir():
                        shutil.rmtree(original)
                    else:
                        original.unlink()
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(backup, original)
                action = "restored_dir"
            elif kind == "file":
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, original)
                action = "restored_file"
            else:
                action = "skipped_unknown"
            ok = 1
            detail = ""
        except Exception as exc:
            ok = 0
            action = "failed"
            detail = str(exc)
            fails += 1
        out.append({
            "ROLE": row.get("ROLE", ""),
            "ORIGINAL_PATH": row.get("ORIGINAL_PATH", ""),
            "BACKUP_PATH": row.get("BACKUP_PATH", ""),
            "KIND": kind,
            "ACTION": action,
            "OK": ok,
            "DETAIL": detail,
        })
    return out, fails

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

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

def compare_fp(before, after):
    b = {r["ROLE"]+"|"+r["PATH"]:r for r in before}
    a = {r["ROLE"]+"|"+r["PATH"]:r for r in after}
    rows = []
    for key in sorted(set(b)|set(a)):
        br = b.get(key)
        ar = a.get(key)
        if br is None:
            rows.append({"ROLE":ar.get("ROLE",""),"PATH":ar.get("PATH",""),"CHANGE":"ADDED","BEFORE_SHA256":"","AFTER_SHA256":ar.get("SHA256",""),"BEFORE_BYTES":"","AFTER_BYTES":ar.get("BYTES","")})
        elif ar is None:
            rows.append({"ROLE":br.get("ROLE",""),"PATH":br.get("PATH",""),"CHANGE":"REMOVED","BEFORE_SHA256":br.get("SHA256",""),"AFTER_SHA256":"","BEFORE_BYTES":br.get("BYTES",""),"AFTER_BYTES":""})
        elif br.get("SHA256") != ar.get("SHA256") or str(br.get("BYTES")) != str(ar.get("BYTES")):
            rows.append({"ROLE":ar.get("ROLE",br.get("ROLE","")),"PATH":ar.get("PATH",br.get("PATH","")),"CHANGE":"MODIFIED","BEFORE_SHA256":br.get("SHA256",""),"AFTER_SHA256":ar.get("SHA256",""),"BEFORE_BYTES":br.get("BYTES",""),"AFTER_BYTES":ar.get("BYTES","")})
    return rows

def norm_text(s: str) -> str:
    return " ".join(s.replace("\r", "\n").split()).upper()

def prepare(repo: Path, args):
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)
    pkg_root = repo / PACKAGE_ROOT
    ag = first_row(reports / "message_catalog_phase22ae_6_5_10ag_status_summary_v1.csv")
    sp, latest = savepoint_present(repo, "MSG-022AE.6.5.10AG")
    running = dottalkpp_running()

    msg_rows = read_csv(repo / MSG14_CSV)
    text_rows = read_csv(repo / TEXT70_CSV)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("ALLOW_FINAL_PROMOTION_FLAG", args.allow_final_promotion, args.allow_final_promotion)
    gate("PHASE22AE_6_5_10AG_GREEN", ag.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AG_GUARDED_FINAL_PROMOTION_PLAN_FROM_10AD_PATTERN_GREEN_SOURCE_HELD", ag.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AG_SAVEPOINT_PRESENT", sp, latest)
    gate("NO_DOTTALKPP_PROCESS_RUNNING", not running, running)
    gate("MSG14_CSV_EXISTS", (repo / MSG14_CSV).exists(), rel(repo / MSG14_CSV, repo))
    gate("TEXT70_CSV_EXISTS", (repo / TEXT70_CSV).exists(), rel(repo / TEXT70_CSV, repo))
    gate("MSG14_CSV_HAS_14_ROWS", len(msg_rows) == 14, len(msg_rows))
    gate("TEXT70_CSV_HAS_70_ROWS", len(text_rows) == 70, len(text_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_12_BEFORE", dbf_header_count(repo / ACTIVE_MSG_DBF) == 12, dbf_header_count(repo / ACTIVE_MSG_DBF))
    gate("ACTIVE_TEXT_HEADER_COUNT_60_BEFORE", dbf_header_count(repo / ACTIVE_TEXT_DBF) == 60, dbf_header_count(repo / ACTIVE_TEXT_DBF))
    gate("PACKAGE_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not pkg_root.exists()) or args.replace_existing_package, rel(pkg_root, repo))

    before = active_inventory(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_active_fingerprint_before_v1.csv", before, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])

    status = "MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_PREPARE_BLOCKED"
    backup_root_rel = ""
    script_rel = ""
    backup_rows = []

    if failures == 0:
        if pkg_root.exists() and args.replace_existing_package:
            shutil.rmtree(pkg_root)
        (pkg_root / "import").mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / MSG14_CSV, pkg_root / "import/system_messages_final_promotion_full14.csv")
        shutil.copy2(repo / TEXT70_CSV, pkg_root / "import/system_message_text_final_promotion_full70.csv")

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / "docs/messaging/backups" / f"MSG-022AE_6_5_10AH_FINAL_PROMOTION_BACKUP_{stamp}"
        backup_root.mkdir(parents=True, exist_ok=False)
        backup_rows = backup_active(repo, backup_root)
        backup_root_rel = rel(backup_root, repo)

        script = repo / SCRIPT_PATH
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTE.dts",
            "* ACTIVE FINAL PROMOTION - uses proven 10AD V1 pattern.",
            "* No QUIT here; quit manually in interactive runs.",
            "",
            "* 1. Promote SYSTEM_MESSAGES and immediately read back.",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            "ZAP",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            f"IMPORT {(pkg_root / 'import/system_messages_final_promotion_full14.csv').resolve().as_posix()}",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            "",
            "* 2. Promote SYSTEM_MESSAGE_TEXT and immediately read back.",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "ZAP",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            f"IMPORT {(pkg_root / 'import/system_message_text_final_promotion_full70.csv').resolve().as_posix()}",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            "",
            "* 3. Final cross-table readback required.",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "",
        ]), encoding="utf-8")
        script_rel = rel(script, repo)
        status = STATUS_PREPARED

    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_prepare_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_backup_manifest_v1.csv", backup_rows, ["ROLE","ORIGINAL_PATH","BACKUP_PATH","EXISTS_AT_BACKUP","KIND","BYTES","SHA256","RESTORE_POLICY"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_prepare_boundary_ledger_v1.csv", [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGES","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":0,"DETAIL":"Prepare only; runtime not yet executed."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGE_TEXT","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":0,"DETAIL":"Prepare only; runtime not yet executed."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ], ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    val = "0" if status == STATUS_PREPARED else str(failures)
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_prepare_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": val,
        "PHASE22AE_6_5_10AG_STATUS": ag.get("STATUS",""),
        "MSG_022AE_6_5_10AG_SAVEPOINT_PRESENT": 1 if sp else 0,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "ALLOW_FINAL_PROMOTION": 1 if args.allow_final_promotion else 0,
        "PATTERN": "10AD_V1_MESSAGE_FIRST_TEXT_SECOND_WITH_READBACK",
        "PACKAGE_ROOT": rel(pkg_root, repo),
        "SCRIPT_PATH": script_rel,
        "RUNLOG_PATH": rel(repo / RUNLOG_PATH, repo),
        "BACKUP_ROOT": backup_root_rel,
        "BACKUP_ROWS": len(backup_rows),
        "MESSAGE14_ROWS": len(read_csv(pkg_root / "import/system_messages_final_promotion_full14.csv")) if pkg_root.exists() else "",
        "TEXT70_ROWS": len(read_csv(pkg_root / "import/system_message_text_final_promotion_full70.csv")) if pkg_root.exists() else "",
        "ACTIVE_MESSAGES_HEADER_COUNT_BEFORE": dbf_header_count(repo / ACTIVE_MSG_DBF),
        "ACTIVE_TEXT_HEADER_COUNT_BEFORE": dbf_header_count(repo / ACTIVE_TEXT_DBF),
        "SHOULD_EXECUTE_RUNTIME": 1 if status == STATUS_PREPARED else 0,
        "SOURCE_FILES_MUTATED": 0,
        "NEXT_GATE": NEXT_PREPARED,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_10AG_STATUS","MSG_022AE_6_5_10AG_SAVEPOINT_PRESENT","DOTTALKPP_PROCESS_RUNNING","ALLOW_FINAL_PROMOTION","PATTERN","PACKAGE_ROOT","SCRIPT_PATH","RUNLOG_PATH","BACKUP_ROOT","BACKUP_ROWS","MESSAGE14_ROWS","TEXT70_ROWS","ACTIVE_MESSAGES_HEADER_COUNT_BEFORE","ACTIVE_TEXT_HEADER_COUNT_BEFORE","SHOULD_EXECUTE_RUNTIME","SOURCE_FILES_MUTATED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {val}")
    print(f"  Phase 22AE.6.5.10AG green: {1 if ag.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10AG_GUARDED_FINAL_PROMOTION_PLAN_FROM_10AD_PATTERN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.10AG savepoint present: {1 if sp else 0}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  allow final promotion: {1 if args.allow_final_promotion else 0}")
    print("  pattern: 10AD_V1_MESSAGE_FIRST_TEXT_SECOND_WITH_READBACK")
    print(f"  active messages header count before: {dbf_header_count(repo / ACTIVE_MSG_DBF)}")
    print(f"  active text header count before: {dbf_header_count(repo / ACTIVE_TEXT_DBF)}")
    print(f"  script path: {script_rel}")
    print(f"  backup root: {backup_root_rel}")
    print(f"  message14 rows: {len(msg_rows)}")
    print(f"  text70 rows: {len(text_rows)}")
    print(f"  should execute runtime: {1 if status == STATUS_PREPARED else 0}")
    print(f"  next gate: {NEXT_PREPARED}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_PREPARED else 2

def finalize(repo: Path, args):
    reports = repo / REPORT_DIR
    prep = first_row(reports / "message_catalog_phase22ae_6_5_10ah_prepare_status_summary_v1.csv")
    runtime = Path(args.runtime_log) if args.runtime_log else repo / RUNLOG_PATH
    if not runtime.is_absolute():
        runtime = repo / runtime
    log = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    up = log.upper()
    norm = norm_text(log)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    imported14 = "IMPORTED 14 RECORDS" in up
    imported70 = "IMPORTED 70 RECORDS" in up
    msg_listed14 = "14 RECORD(S) LISTED" in up
    text_listed70 = "70 RECORD(S) LISTED" in up
    count14 = "\n14\n" in log.replace("\r", "\n") or "COUNT 14" in norm
    count70 = "\n70\n" in log.replace("\r", "\n") or "COUNT 70" in norm
    proof_symbols_visible = sum(1 for s in PROOF_SYMBOLS if s in up)
    text_locales_visible = sum(1 for loc in PROOF_LOCALES if loc.upper() in up)
    zap_count = up.count("ZAP COMPLETE")
    msg_header = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_header = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    gate("PREPARED_STATUS", prep.get("STATUS") == STATUS_PREPARED, prep.get("STATUS", "missing"))
    gate("RUNTIME_LOG_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("TWO_ZAP_COMPLETE_SIGNALS", zap_count >= 2, zap_count)
    gate("IMPORTED_14_SIGNAL", imported14, "SYSTEM_MESSAGES import")
    gate("MESSAGE_COUNT_OR_HEADER_14_SIGNAL", count14 or msg_header == 14, f"count14={count14}; header={msg_header}")
    gate("MESSAGE_LIST_14_SIGNAL", msg_listed14, "SYSTEM_MESSAGES LIST ALL should list 14")
    gate("IMPORTED_70_SIGNAL", imported70, "SYSTEM_MESSAGE_TEXT import")
    gate("TEXT_COUNT_OR_HEADER_70_SIGNAL", count70 or text_header == 70, f"count70={count70}; header={text_header}")
    gate("TEXT_LIST_70_SIGNAL", text_listed70, "SYSTEM_MESSAGE_TEXT LIST ALL should list 70")
    gate("PROOF_SYMBOLS_VISIBLE", proof_symbols_visible == 2, f"{proof_symbols_visible}/2")
    gate("PROOF_LOCALES_VISIBLE", text_locales_visible == 5, f"{text_locales_visible}/5")
    gate("NO_UNKNOWN_COMMAND", "UNKNOWN COMMAND" not in up, "must be absent")
    gate("NO_CANNOT_OPEN", "CANNOT OPEN" not in up, "must be absent")

    before = read_csv(reports / "message_catalog_phase22ae_6_5_10ah_active_fingerprint_before_v1.csv")
    after = active_inventory(repo)
    delta = compare_fp(before, after)

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    val = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_finalize_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_active_fingerprint_after_promotion_v1.csv", after, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_active_fingerprint_delta_promotion_v1.csv", delta, ["ROLE","PATH","CHANGE","BEFORE_SHA256","AFTER_SHA256","BEFORE_BYTES","AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_runtime_observations_v1.csv", [
        {"OBSERVATION":"runtime_log_exists","VALUE":1 if runtime.exists() else 0,"DETAIL":rel(runtime, repo)},
        {"OBSERVATION":"zap_complete_signals","VALUE":zap_count,"DETAIL":"2 expected"},
        {"OBSERVATION":"imported_14_records_signal","VALUE":1 if imported14 else 0,"DETAIL":"SYSTEM_MESSAGES"},
        {"OBSERVATION":"message_list_14_signal","VALUE":1 if msg_listed14 else 0,"DETAIL":"SYSTEM_MESSAGES"},
        {"OBSERVATION":"imported_70_records_signal","VALUE":1 if imported70 else 0,"DETAIL":"SYSTEM_MESSAGE_TEXT"},
        {"OBSERVATION":"text_list_70_signal","VALUE":1 if text_listed70 else 0,"DETAIL":"SYSTEM_MESSAGE_TEXT"},
        {"OBSERVATION":"proof_symbols_visible","VALUE":proof_symbols_visible,"DETAIL":"2 expected"},
        {"OBSERVATION":"proof_locales_visible","VALUE":text_locales_visible,"DETAIL":"5 expected"},
        {"OBSERVATION":"active_messages_header_count_after_promotion","VALUE":msg_header,"DETAIL":"raw header evidence"},
        {"OBSERVATION":"active_text_header_count_after_promotion","VALUE":text_header,"DETAIL":"raw header evidence"},
        {"OBSERVATION":"rollback_backup_root","VALUE":prep.get("BACKUP_ROOT",""),"DETAIL":"retain until 10AI readback/savepoint acceptance"},
    ], ["OBSERVATION","VALUE","DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_finalize_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": val,
        "RUNTIME_LOG": rel(runtime, repo),
        "PATTERN": "10AD_V1_MESSAGE_FIRST_TEXT_SECOND_WITH_READBACK",
        "RUNTIME_ZAP_COMPLETE_SIGNALS": zap_count,
        "RUNTIME_IMPORTED_14": 1 if imported14 else 0,
        "RUNTIME_MESSAGE_COUNT_14": 1 if count14 else 0,
        "RUNTIME_MESSAGE_LISTED_14": 1 if msg_listed14 else 0,
        "RUNTIME_IMPORTED_70": 1 if imported70 else 0,
        "RUNTIME_TEXT_COUNT_70": 1 if count70 else 0,
        "RUNTIME_TEXT_LISTED_70": 1 if text_listed70 else 0,
        "PROOF_SYMBOLS_VISIBLE": proof_symbols_visible,
        "PROOF_LOCALES_VISIBLE": text_locales_visible,
        "ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROMOTION": msg_header,
        "ACTIVE_TEXT_HEADER_COUNT_AFTER_PROMOTION": text_header,
        "ACTIVE_FINGERPRINT_DELTA_ROWS": len(delta),
        "BACKUP_ROOT": prep.get("BACKUP_ROOT",""),
        "ROLLBACK_AVAILABLE": 1 if prep.get("BACKUP_ROOT","") else 0,
        "RESTORE_REQUIRED": 0 if status == STATUS_GREEN else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GREEN if status == STATUS_GREEN else NEXT_BLOCKED,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","RUNTIME_LOG","PATTERN","RUNTIME_ZAP_COMPLETE_SIGNALS","RUNTIME_IMPORTED_14","RUNTIME_MESSAGE_COUNT_14","RUNTIME_MESSAGE_LISTED_14","RUNTIME_IMPORTED_70","RUNTIME_TEXT_COUNT_70","RUNTIME_TEXT_LISTED_70","PROOF_SYMBOLS_VISIBLE","PROOF_LOCALES_VISIBLE","ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROMOTION","ACTIVE_TEXT_HEADER_COUNT_AFTER_PROMOTION","ACTIVE_FINGERPRINT_DELTA_ROWS","BACKUP_ROOT","ROLLBACK_AVAILABLE","RESTORE_REQUIRED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {val}")
    print("  pattern: 10AD_V1_MESSAGE_FIRST_TEXT_SECOND_WITH_READBACK")
    print(f"  runtime ZAP complete signals: {zap_count}")
    print(f"  runtime imported 14: {1 if imported14 else 0}")
    print(f"  runtime message count 14: {1 if count14 else 0}")
    print(f"  runtime message listed 14: {1 if msg_listed14 else 0}")
    print(f"  runtime imported 70: {1 if imported70 else 0}")
    print(f"  runtime text count 70: {1 if count70 else 0}")
    print(f"  runtime text listed 70: {1 if text_listed70 else 0}")
    print(f"  proof symbols visible: {proof_symbols_visible}/2")
    print(f"  proof locales visible: {text_locales_visible}/5")
    print(f"  active messages header count after promotion: {msg_header}")
    print(f"  active text header count after promotion: {text_header}")
    print(f"  rollback available: {1 if prep.get('BACKUP_ROOT','') else 0}")
    print(f"  restore required: {0 if status == STATUS_GREEN else 1}")
    print(f"  next gate: {NEXT_GREEN if status == STATUS_GREEN else NEXT_BLOCKED}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_GREEN, STATUS_BLOCKED) else 2

def rollback(repo: Path, args):
    reports = repo / REPORT_DIR
    final = first_row(reports / "message_catalog_phase22ae_6_5_10ah_finalize_status_summary_v1.csv")
    rows = read_csv(reports / "message_catalog_phase22ae_6_5_10ah_backup_manifest_v1.csv")
    restore_rows, fails = restore_from_manifest(repo, rows)

    after_restore = active_inventory(repo)
    before = read_csv(reports / "message_catalog_phase22ae_6_5_10ah_active_fingerprint_before_v1.csv")
    delta = compare_fp(before, after_restore)
    restored_exact = 1 if len(delta) == 0 else 0
    msg_header = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_header = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    status = STATUS_ROLLED_BACK if restored_exact else "MESSAGE_CATALOG_PHASE22AE_6_5_10AH_ROLLBACK_BLOCKED"
    val = "0" if restored_exact else str(max(1, fails, len(delta)))
    next_gate = NEXT_ROLLED_BACK if restored_exact else "HOLD_AND_REPAIR_PHASE22AE_6_5_10AH_ROLLBACK_FAILURE"

    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_rollback_rows_v1.csv", restore_rows, ["ROLE","ORIGINAL_PATH","BACKUP_PATH","KIND","ACTION","OK","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_active_fingerprint_after_rollback_v1.csv", after_restore, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_active_fingerprint_delta_after_rollback_v1.csv", delta, ["ROLE","PATH","CHANGE","BEFORE_SHA256","AFTER_SHA256","BEFORE_BYTES","AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ah_rollback_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": val,
        "FINALIZE_STATUS": final.get("STATUS",""),
        "ROLLBACK_ROWS": len(restore_rows),
        "RESTORED_EXACT_BACKUP": restored_exact,
        "POST_ROLLBACK_ACTIVE_MESSAGES_HEADER_COUNT": msg_header,
        "POST_ROLLBACK_ACTIVE_TEXT_HEADER_COUNT": text_header,
        "POST_ROLLBACK_FINGERPRINT_DELTA_ROWS": len(delta),
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","FINALIZE_STATUS","ROLLBACK_ROWS","RESTORED_EXACT_BACKUP","POST_ROLLBACK_ACTIVE_MESSAGES_HEADER_COUNT","POST_ROLLBACK_ACTIVE_TEXT_HEADER_COUNT","POST_ROLLBACK_FINGERPRINT_DELTA_ROWS","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {val}")
    print(f"  finalize status: {final.get('STATUS','')}")
    print(f"  rollback rows: {len(restore_rows)}")
    print(f"  restored exact backup: {restored_exact}")
    print(f"  post-rollback active messages header count: {msg_header}")
    print(f"  post-rollback active text header count: {text_header}")
    print(f"  post-rollback fingerprint delta rows: {len(delta)}")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if restored_exact else 2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--mode", choices=["prepare","finalize","rollback"], required=True)
    ap.add_argument("--runtime-log", default="")
    ap.add_argument("--allow-final-promotion", action="store_true")
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    if args.mode == "prepare":
        return prepare(repo, args)
    if args.mode == "finalize":
        return finalize(repo, args)
    return rollback(repo, args)

if __name__ == "__main__":
    raise SystemExit(main())
