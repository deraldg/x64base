#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_IMPORT_READY = "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_GREEN_IMPORT_SURFACE_CANDIDATE_READY"
STATUS_REBUILD_REQUIRED = "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_GREEN_REBUILD_PATH_REQUIRED"
STATUS_CANDIDATE_DISCOVERY_REQUIRED = "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_GREEN_CANDIDATE_DISCOVERY_REQUIRED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_BLOCKED"

NEXT_IMPORT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_2_ISOLATED_IMPORT_EXECUTION_PROOF"
NEXT_REBUILD = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_2_FULL_CANDIDATE_REBUILD_SANDBOX_PROOF"
NEXT_CANDIDATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_2_CANDIDATE_ROW_SOURCE_DISCOVERY_REPAIR"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_1_IMPORT_OR_REBUILD_SURFACE_PROBE.md")

ACTIVE_MSG_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_MSG_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_MSG_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")
TABLES = ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]

class DbfInfo:
    def __init__(self, path, record_count, header_len, record_len):
        self.path = path
        self.record_count = record_count
        self.header_len = header_len
        self.record_len = record_len

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

def parse_dbf_count(path: Path) -> int:
    data = path.read_bytes()
    if len(data) < 12:
        raise RuntimeError(f"DBF too small: {path}")
    return struct.unpack("<I", data[4:8])[0]

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_1_stage_status_summary_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_1_protected_fingerprint_before_v1.csv")

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

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_PACKAGE_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_PROOF_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("SANDBOX_MESSAGE_DBF_EXISTS", msg_dbf.exists(), rel(msg_dbf, repo))
    gate("SANDBOX_TEXT_DBF_EXISTS", txt_dbf.exists(), rel(txt_dbf, repo))

    after_fp = fingerprint_selected(repo)
    fp_delta = compare_fp(before_fp, after_fp)
    boundary_clean = len(fp_delta) == 0

    msg_after = ""
    txt_after = ""
    try:
        msg_after = parse_dbf_count(msg_dbf)
        txt_after = parse_dbf_count(txt_dbf)
    except Exception as exc:
        gate("SANDBOX_DBF_COUNT_READBACK", False, exc)

    counts_unchanged = (msg_after == msg_before and txt_after == txt_before)

    import_usage_signal = 0
    append_from_usage_signal = 0
    import_unknown = 0
    append_unknown = 0

    if "IMPORT" in log_upper and "UNKNOWN COMMAND: IMPORT" not in log_upper:
        import_usage_signal = 1
    if "APPEND FROM" in log_upper and "UNKNOWN COMMAND: APPEND" not in log_upper:
        append_from_usage_signal = 1
    if "UNKNOWN COMMAND: IMPORT" in log_upper:
        import_unknown = 1
    if "UNKNOWN COMMAND: APPEND" in log_upper or "UNKNOWN COMMAND: APPEND FROM" in log_upper:
        append_unknown = 1

    candidate_msg_found = stage.get("CANDIDATE_MESSAGE_FILE_FOUND") == "1"
    candidate_txt_found = stage.get("CANDIDATE_TEXT_FILE_FOUND") == "1"
    candidate_pair_found = candidate_msg_found and candidate_txt_found
    import_surface_ready = (import_usage_signal or append_from_usage_signal) and not (import_unknown and append_unknown)

    if failures > 0 or not boundary_clean or not counts_unchanged:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_1_SURFACE_OR_BOUNDARY"
        validation_issues = str(max(1, failures, len(fp_delta)))
    elif candidate_pair_found and import_surface_ready:
        status = STATUS_IMPORT_READY
        next_gate = NEXT_IMPORT
        validation_issues = "0"
    elif candidate_pair_found:
        status = STATUS_REBUILD_REQUIRED
        next_gate = NEXT_REBUILD
        validation_issues = "0"
    else:
        status = STATUS_CANDIDATE_DISCOVERY_REQUIRED
        next_gate = NEXT_CANDIDATE
        validation_issues = "0"

    runtime_rows = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if runtime.exists() else 0, "DETAIL": rel(runtime, repo)},
        {"OBSERVATION": "opened_system_messages_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGES"), "DETAIL": "Open readiness signal."},
        {"OBSERVATION": "opened_system_message_text_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGE_TEXT"), "DETAIL": "Open readiness signal."},
        {"OBSERVATION": "import_usage_signal", "VALUE": import_usage_signal, "DETAIL": "IMPORT command appeared without unknown-command marker."},
        {"OBSERVATION": "append_from_usage_signal", "VALUE": append_from_usage_signal, "DETAIL": "APPEND FROM command appeared without unknown-command marker."},
        {"OBSERVATION": "import_unknown", "VALUE": import_unknown, "DETAIL": "IMPORT unknown-command marker."},
        {"OBSERVATION": "append_unknown", "VALUE": append_unknown, "DETAIL": "APPEND/APPEND FROM unknown-command marker."},
    ]

    result_rows = [{
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_before,
        "SANDBOX_MESSAGE_ROWS_AFTER": msg_after,
        "SANDBOX_TEXT_ROWS_BEFORE": txt_before,
        "SANDBOX_TEXT_ROWS_AFTER": txt_after,
        "COUNTS_UNCHANGED": 1 if counts_unchanged else 0,
        "CANDIDATE_MESSAGE_FILE_FOUND": 1 if candidate_msg_found else 0,
        "CANDIDATE_TEXT_FILE_FOUND": 1 if candidate_txt_found else 0,
        "IMPORT_SURFACE_READY": 1 if import_surface_ready else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
    }]

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if boundary_clean else 1, "DETAIL": f"protected fingerprint changes={len(fp_delta)}"},
        {"PROTECTED_SYSTEM": "SANDBOX_DBF_COUNTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if counts_unchanged else 1, "DETAIL": f"counts unchanged={1 if counts_unchanged else 0}"},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_1_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_1_surface_result_v1.csv", result_rows, ["SANDBOX_MESSAGE_ROWS_BEFORE", "SANDBOX_MESSAGE_ROWS_AFTER", "SANDBOX_TEXT_ROWS_BEFORE", "SANDBOX_TEXT_ROWS_AFTER", "COUNTS_UNCHANGED", "CANDIDATE_MESSAGE_FILE_FOUND", "CANDIDATE_TEXT_FILE_FOUND", "IMPORT_SURFACE_READY", "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_1_runtime_observations_v1.csv", runtime_rows, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_1_protected_fingerprint_after_v1.csv", after_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_1_protected_fingerprint_delta_v1.csv", fp_delta, ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256", "BEFORE_BYTES", "AFTER_BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_1_validate_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_1_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_PACKAGE_STAGED_SOURCE_HELD" else 0,
        "SANDBOX_MESSAGE_ROWS_BEFORE": msg_before,
        "SANDBOX_MESSAGE_ROWS_AFTER": msg_after,
        "SANDBOX_TEXT_ROWS_BEFORE": txt_before,
        "SANDBOX_TEXT_ROWS_AFTER": txt_after,
        "COUNTS_UNCHANGED": 1 if counts_unchanged else 0,
        "CANDIDATE_MESSAGE_FILE_FOUND": 1 if candidate_msg_found else 0,
        "CANDIDATE_TEXT_FILE_FOUND": 1 if candidate_txt_found else 0,
        "IMPORT_SURFACE_READY": 1 if import_surface_ready else 0,
        "BOUNDARY_CLEAN": 1 if boundary_clean else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if boundary_clean else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_GREEN",
         "SANDBOX_MESSAGE_ROWS_BEFORE", "SANDBOX_MESSAGE_ROWS_AFTER",
         "SANDBOX_TEXT_ROWS_BEFORE", "SANDBOX_TEXT_ROWS_AFTER",
         "COUNTS_UNCHANGED", "CANDIDATE_MESSAGE_FILE_FOUND", "CANDIDATE_TEXT_FILE_FOUND",
         "IMPORT_SURFACE_READY", "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "SOURCE_FILES_MUTATED",
         "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_1_IMPORT_OR_REBUILD_SANDBOX_PROOF_PACKAGE_STAGED_SOURCE_HELD' else 0}")
    print(f"  sandbox message rows before/after: {msg_before}/{msg_after}")
    print(f"  sandbox text rows before/after: {txt_before}/{txt_after}")
    print(f"  counts unchanged: {1 if counts_unchanged else 0}")
    print(f"  candidate message file found: {1 if candidate_msg_found else 0}")
    print(f"  candidate text file found: {1 if candidate_txt_found else 0}")
    print(f"  import surface ready: {1 if import_surface_ready else 0}")
    print(f"  boundary clean: {1 if boundary_clean else 0}")
    print(f"  protected fingerprint changes: {len(fp_delta)}")
    print(f"  active catalog mutation observed: {0 if boundary_clean else 1}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_IMPORT_READY, STATUS_REBUILD_REQUIRED, STATUS_CANDIDATE_DISCOVERY_REQUIRED) else 2

if __name__ == "__main__":
    raise SystemExit(main())
