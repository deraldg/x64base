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
PACKAGE_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10aa_full70_text_zap_import_sequence_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE.dts")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE.md")

PLAN_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10z_full70_text_zap_import_sequence_plan_v1")
FULL70_CSV = PLAN_ROOT / "import/system_message_text_full70_zap_import_sequence.csv"

ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
ACTIVE_INDEX = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx")
ACTIVE_INDEX_META = Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx.meta")
ACTIVE_LMDB = Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d")
DEFAULT_INDEX = Path("dottalkpp/data/indexes/SYSTEM_MESSAGE_TEXT.cdx")
DEFAULT_INDEX_META = Path("dottalkpp/data/indexes/SYSTEM_MESSAGE_TEXT.cdx.meta")
DEFAULT_LMDB = Path("dottalkpp/data/lmdb/SYSTEM_MESSAGE_TEXT.cdx.d")

STATUS_PREPARED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PREPARED"
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_GREEN_RESTORE_REQUIRED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_BLOCKED_RESTORE_REQUIRED"
STATUS_RESTORED_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PROVEN_AND_RESTORED"
STATUS_RESTORED_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_FAILED_BUT_RESTORED"

NEXT_PREPARED = "RUN_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_THEN_FINALIZE"
NEXT_FINALIZED = "RESTORE_PHASE22AE_6_5_10AA_ACTIVE_TEXT_BACKUP_BEFORE_SAVEPOINT"
NEXT_RESTORED_GREEN = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AB_FULL70_TEXT_SEQUENCE_RESULT_CLASSIFICATION"
NEXT_RESTORED_BLOCKED = "HOLD_AND_REVIEW_PHASE22AE_6_5_10AA_FULL70_TEXT_SEQUENCE_FAILURE"

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

def active_inventory(repo: Path):
    paths = [(ACTIVE_TEXT_DBF, "active_text_dbf")]
    for ext in SIDE_EXTS:
        paths.append((ACTIVE_TEXT_DBF.with_suffix(ext), f"active_text_sidecar_{ext}"))
    paths += [
        (ACTIVE_INDEX, "active_text_index"),
        (ACTIVE_INDEX_META, "active_text_index_meta"),
        (ACTIVE_LMDB, "active_text_lmdb"),
        (DEFAULT_INDEX, "default_text_index"),
        (DEFAULT_INDEX_META, "default_text_index_meta"),
        (DEFAULT_LMDB, "default_text_lmdb"),
    ]
    seen = set()
    rows = []
    for path, role in paths:
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
            "RESTORE_POLICY": "restore exact backup after proof regardless of result",
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
    z = first_row(reports / "message_catalog_phase22ae_6_5_10z_status_summary_v1.csv")
    sp, latest = savepoint_present(repo, "MSG-022AE.6.5.10Z")
    running = dottalkpp_running()

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("ALLOW_FULL70_TEXT_SEQUENCE_FLAG", args.allow_full70_text_sequence, args.allow_full70_text_sequence)
    gate("PHASE22AE_6_5_10Z_GREEN", z.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10Z_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PLAN_GREEN_SOURCE_HELD", z.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10Z_SAVEPOINT_PRESENT", sp, latest)
    gate("NO_DOTTALKPP_PROCESS_RUNNING", not running, running)
    gate("FULL70_CSV_EXISTS", (repo / FULL70_CSV).exists(), rel(repo / FULL70_CSV, repo))
    gate("FULL70_CSV_HAS_70_ROWS", len(read_csv(repo / FULL70_CSV)) == 70, len(read_csv(repo / FULL70_CSV)))
    gate("ACTIVE_TEXT_HEADER_COUNT_60_BEFORE", dbf_header_count(repo / ACTIVE_TEXT_DBF) == 60, dbf_header_count(repo / ACTIVE_TEXT_DBF))
    gate("PACKAGE_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not pkg_root.exists()) or args.replace_existing_package, rel(pkg_root, repo))

    before = active_inventory(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_active_text_fingerprint_before_v1.csv", before, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])

    status = "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PREPARE_BLOCKED"
    backup_root_rel = ""
    script_rel = ""
    backup_rows = []

    if failures == 0:
        if pkg_root.exists() and args.replace_existing_package:
            shutil.rmtree(pkg_root)
        (pkg_root / "import").mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / FULL70_CSV, pkg_root / "import/system_message_text_full70_zap_import_sequence.csv")

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / "docs/messaging/backups" / f"MSG-022AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_BACKUP_{stamp}"
        backup_root.mkdir(parents=True, exist_ok=False)
        backup_rows = backup_active(repo, backup_root)
        backup_root_rel = rel(backup_root, repo)

        script = repo / SCRIPT_PATH
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE.dts",
            "* ACTIVE TEXT-ONLY FULL70 ZAP/IMPORT MICRO PROOF - diagnostic only.",
            "* No QUIT here; quit manually in interactive runs.",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "ZAP",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            f"IMPORT {(pkg_root / 'import/system_message_text_full70_zap_import_sequence.csv').resolve().as_posix()}",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            "",
        ]), encoding="utf-8")
        script_rel = rel(script, repo)
        status = STATUS_PREPARED

    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_prepare_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_backup_manifest_v1.csv", backup_rows, ["ROLE","ORIGINAL_PATH","BACKUP_PATH","EXISTS_AT_BACKUP","KIND","BYTES","SHA256","RESTORE_POLICY"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_prepare_boundary_ledger_v1.csv", [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No source mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGE_TEXT","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":0,"DETAIL":"Prepare only; runtime not yet executed."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Message table out of scope."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ], ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    val = "0" if status == STATUS_PREPARED else str(failures)
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_prepare_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": val,
        "PHASE22AE_6_5_10Z_STATUS": z.get("STATUS",""),
        "MSG_022AE_6_5_10Z_SAVEPOINT_PRESENT": 1 if sp else 0,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "ALLOW_FULL70_TEXT_SEQUENCE": 1 if args.allow_full70_text_sequence else 0,
        "PACKAGE_ROOT": rel(pkg_root, repo),
        "SCRIPT_PATH": script_rel,
        "RUNLOG_PATH": rel(repo / RUNLOG_PATH, repo),
        "BACKUP_ROOT": backup_root_rel,
        "BACKUP_ROWS": len(backup_rows),
        "FULL70_ROWS": len(read_csv(pkg_root / "import/system_message_text_full70_zap_import_sequence.csv")) if pkg_root.exists() else "",
        "ACTIVE_TEXT_HEADER_COUNT_BEFORE": dbf_header_count(repo / ACTIVE_TEXT_DBF),
        "SHOULD_EXECUTE_RUNTIME": 1 if status == STATUS_PREPARED else 0,
        "ACTIVE_TEXT_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "NEXT_GATE": NEXT_PREPARED,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","PHASE22AE_6_5_10Z_STATUS","MSG_022AE_6_5_10Z_SAVEPOINT_PRESENT","DOTTALKPP_PROCESS_RUNNING","ALLOW_FULL70_TEXT_SEQUENCE","PACKAGE_ROOT","SCRIPT_PATH","RUNLOG_PATH","BACKUP_ROOT","BACKUP_ROWS","FULL70_ROWS","ACTIVE_TEXT_HEADER_COUNT_BEFORE","SHOULD_EXECUTE_RUNTIME","ACTIVE_TEXT_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {val}")
    print(f"  Phase 22AE.6.5.10Z green: {1 if z.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10Z_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.10Z savepoint present: {1 if sp else 0}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  allow full70 text sequence: {1 if args.allow_full70_text_sequence else 0}")
    print(f"  active text header count before: {dbf_header_count(repo / ACTIVE_TEXT_DBF)}")
    print(f"  script path: {script_rel}")
    print(f"  backup root: {backup_root_rel}")
    print(f"  full70 rows: {len(read_csv(repo / FULL70_CSV))}")
    print(f"  should execute runtime: {1 if status == STATUS_PREPARED else 0}")
    print(f"  next gate: {NEXT_PREPARED}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_PREPARED else 2

def finalize(repo: Path, args):
    reports = repo / REPORT_DIR
    prep = first_row(reports / "message_catalog_phase22ae_6_5_10aa_prepare_status_summary_v1.csv")
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

    imported70 = "IMPORTED 70 RECORDS" in up
    listed70 = "70 RECORD(S) LISTED" in up
    count70 = "\n70\n" in log.replace("\r", "\n") or "COUNT 70" in norm
    symbols_found = sum(1 for s in PROOF_SYMBOLS if s in up)
    locales_found = sum(1 for loc in PROOF_LOCALES if loc.upper() in up)
    zap_complete = "ZAP COMPLETE" in up
    header_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    gate("PREPARED_STATUS", prep.get("STATUS") == STATUS_PREPARED, prep.get("STATUS", "missing"))
    gate("RUNTIME_LOG_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("ZAP_COMPLETE_SIGNAL", zap_complete, "full70 sequence")
    gate("IMPORTED_70_SIGNAL", imported70, "full70 import")
    gate("COUNT_OR_HEADER_70_SIGNAL", count70 or header_count == 70, f"count70={count70}; header={header_count}")
    gate("LIST_70_SIGNAL", listed70, "LIST ALL should list 70")
    gate("PROOF_SYMBOLS_VISIBLE", symbols_found == 2, f"{symbols_found}/2")
    gate("PROOF_LOCALES_VISIBLE", locales_found == 5, f"{locales_found}/5")
    gate("NO_UNKNOWN_COMMAND", "UNKNOWN COMMAND" not in up, "must be absent")
    gate("NO_NO_FILE_OPEN", "NO FILE OPEN" not in up, "must be absent")
    gate("NO_CANNOT_OPEN", "CANNOT OPEN" not in up, "must be absent")

    before = read_csv(reports / "message_catalog_phase22ae_6_5_10aa_active_text_fingerprint_before_v1.csv")
    after = active_inventory(repo)
    delta = compare_fp(before, after)

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    val = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_finalize_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_active_text_fingerprint_after_full70_v1.csv", after, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_active_text_fingerprint_delta_full70_v1.csv", delta, ["ROLE","PATH","CHANGE","BEFORE_SHA256","AFTER_SHA256","BEFORE_BYTES","AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_runtime_observations_v1.csv", [
        {"OBSERVATION":"runtime_log_exists","VALUE":1 if runtime.exists() else 0,"DETAIL":rel(runtime, repo)},
        {"OBSERVATION":"zap_complete_signal","VALUE":1 if zap_complete else 0,"DETAIL":"full70 ZAP"},
        {"OBSERVATION":"imported_70_records_signal","VALUE":1 if imported70 else 0,"DETAIL":"full70 import"},
        {"OBSERVATION":"count70_signal","VALUE":1 if count70 else 0,"DETAIL":"COUNT output"},
        {"OBSERVATION":"list70_signal","VALUE":1 if listed70 else 0,"DETAIL":"LIST ALL"},
        {"OBSERVATION":"proof_symbols_visible","VALUE":symbols_found,"DETAIL":"2 expected"},
        {"OBSERVATION":"proof_locales_visible","VALUE":locales_found,"DETAIL":"5 expected"},
        {"OBSERVATION":"active_text_header_count_after_full70","VALUE":header_count,"DETAIL":"raw header evidence only"},
    ], ["OBSERVATION","VALUE","DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_finalize_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": val,
        "RUNTIME_LOG": rel(runtime, repo),
        "RUNTIME_ZAP_COMPLETE": 1 if zap_complete else 0,
        "RUNTIME_IMPORTED_70": 1 if imported70 else 0,
        "RUNTIME_COUNT_70": 1 if count70 else 0,
        "RUNTIME_LISTED_70": 1 if listed70 else 0,
        "PROOF_SYMBOLS_VISIBLE": symbols_found,
        "PROOF_LOCALES_VISIBLE": locales_found,
        "ACTIVE_TEXT_HEADER_COUNT_AFTER_FULL70": header_count,
        "ACTIVE_TEXT_FINGERPRINT_DELTA_ROWS": len(delta),
        "RESTORE_REQUIRED": 1,
        "SOURCE_FILES_MUTATED": 0,
        "NEXT_GATE": NEXT_FINALIZED,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","RUNTIME_LOG","RUNTIME_ZAP_COMPLETE","RUNTIME_IMPORTED_70","RUNTIME_COUNT_70","RUNTIME_LISTED_70","PROOF_SYMBOLS_VISIBLE","PROOF_LOCALES_VISIBLE","ACTIVE_TEXT_HEADER_COUNT_AFTER_FULL70","ACTIVE_TEXT_FINGERPRINT_DELTA_ROWS","RESTORE_REQUIRED","SOURCE_FILES_MUTATED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {val}")
    print(f"  runtime ZAP complete: {1 if zap_complete else 0}")
    print(f"  runtime imported 70: {1 if imported70 else 0}")
    print(f"  runtime count 70: {1 if count70 else 0}")
    print(f"  runtime listed 70: {1 if listed70 else 0}")
    print(f"  proof symbols visible: {symbols_found}/2")
    print(f"  proof locales visible: {locales_found}/5")
    print(f"  active text header count after full70: {header_count}")
    print(f"  active text fingerprint delta rows: {len(delta)}")
    print("  restore required: 1")
    print(f"  next gate: {NEXT_FINALIZED}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_GREEN, STATUS_BLOCKED) else 2

def restore(repo: Path, args):
    reports = repo / REPORT_DIR
    final = first_row(reports / "message_catalog_phase22ae_6_5_10aa_finalize_status_summary_v1.csv")
    rows = read_csv(reports / "message_catalog_phase22ae_6_5_10aa_backup_manifest_v1.csv")
    restore_rows, fails = restore_from_manifest(repo, rows)

    after_restore = active_inventory(repo)
    before = read_csv(reports / "message_catalog_phase22ae_6_5_10aa_active_text_fingerprint_before_v1.csv")
    delta = compare_fp(before, after_restore)
    restored_exact = 1 if len(delta) == 0 else 0
    header_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    if final.get("STATUS") == STATUS_GREEN and restored_exact:
        status = STATUS_RESTORED_GREEN
        next_gate = NEXT_RESTORED_GREEN
    elif restored_exact:
        status = STATUS_RESTORED_BLOCKED
        next_gate = NEXT_RESTORED_BLOCKED
    else:
        status = "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_RESTORE_BLOCKED"
        next_gate = "HOLD_AND_REPAIR_PHASE22AE_6_5_10AA_RESTORE_FAILURE"
        fails += max(1, len(delta))

    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_restore_rows_v1.csv", restore_rows, ["ROLE","ORIGINAL_PATH","BACKUP_PATH","KIND","ACTION","OK","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_active_text_fingerprint_after_restore_v1.csv", after_restore, ["ROLE","PATH","EXISTS","KIND","BYTES","SHA256","FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_active_text_fingerprint_delta_after_restore_v1.csv", delta, ["ROLE","PATH","CHANGE","BEFORE_SHA256","AFTER_SHA256","BEFORE_BYTES","AFTER_BYTES"])

    val = "0" if status in (STATUS_RESTORED_GREEN, STATUS_RESTORED_BLOCKED) else str(fails)
    write_csv(reports / "message_catalog_phase22ae_6_5_10aa_restore_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": val,
        "FINALIZE_STATUS": final.get("STATUS", ""),
        "RESTORE_ROWS": len(restore_rows),
        "RESTORED_EXACT_BACKUP": restored_exact,
        "POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT": header_count,
        "POST_RESTORE_FINGERPRINT_DELTA_ROWS": len(delta),
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","FINALIZE_STATUS","RESTORE_ROWS","RESTORED_EXACT_BACKUP","POST_RESTORE_ACTIVE_TEXT_HEADER_COUNT","POST_RESTORE_FINGERPRINT_DELTA_ROWS","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {val}")
    print(f"  finalize status: {final.get('STATUS','')}")
    print(f"  restore rows: {len(restore_rows)}")
    print(f"  restored exact backup: {restored_exact}")
    print(f"  post-restore active text header count: {header_count}")
    print(f"  post-restore fingerprint delta rows: {len(delta)}")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_RESTORED_GREEN, STATUS_RESTORED_BLOCKED) else 2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--mode", choices=["prepare","finalize","restore"], required=True)
    ap.add_argument("--runtime-log", default="")
    ap.add_argument("--allow-full70-text-sequence", action="store_true")
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    if args.mode == "prepare":
        return prepare(repo, args)
    if args.mode == "finalize":
        return finalize(repo, args)
    return restore(repo, args)

if __name__ == "__main__":
    raise SystemExit(main())
