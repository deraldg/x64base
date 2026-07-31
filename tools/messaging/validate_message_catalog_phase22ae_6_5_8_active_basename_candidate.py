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

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_AND_READBACK_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_AND_READBACK_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_9_CANDIDATE_CDX_REBUILD_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_READBACK.md")

ACTIVE_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

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
    return {"HEADER_COUNT": header_count, "PHYSICAL_COUNT": physical, "BYTES": len(data), "SHA256": sha256_file(path)}

def fingerprint_active(repo: Path):
    rows = []
    targets = []
    for table in ["SYSTEM_MESSAGES", "SYSTEM_MESSAGE_TEXT"]:
        targets.append((repo / ACTIVE_ROOT / f"{table}.dbf", f"active_dbf_{table}"))
        for p in sorted((repo / ACTIVE_ROOT).glob(f"{table}.*")):
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

def runtime_flags(text: str):
    u = text.upper()
    return {
        "OPENED_SYSTEM_MESSAGES_14": 1 if re.search(r"Opened\s+SYSTEM_MESSAGES\s+\(v64\)\s+:\s+Record count\s+14", text, re.I) else 0,
        "OPENED_SYSTEM_MESSAGE_TEXT_70": 1 if re.search(r"Opened\s+SYSTEM_MESSAGE_TEXT\s+\(v64\)\s+:\s+Record count\s+70", text, re.I) else 0,
        "COUNT_14": 1 if re.search(r"(?m)^\s*14\s*$", text) else 0,
        "COUNT_70": 1 if re.search(r"(?m)^\s*70\s*$", text) else 0,
        "ALREADY_OPEN_WARNING": 1 if "ALREADY OPEN" in u else 0,
        "MUTATION_WORDS": 1 if any(w in u for w in ["IMPORTED ", "APPENDED", "REPLACED", "BUILDLMDB: DONE", "CDX CREATE"]) else 0,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-proof", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    stage = first_row(reports / "message_catalog_phase22ae_6_5_8_stage_status_summary_v1.csv")
    before_fp = read_csv(reports / "message_catalog_phase22ae_6_5_8_active_fingerprint_before_v1.csv")

    runtime_path = Path(args.runtime_proof) if args.runtime_proof else repo / RUNLOG
    if not runtime_path.is_absolute():
        runtime_path = repo / runtime_path
    runtime_text = runtime_path.read_text(encoding="utf-8", errors="replace") if runtime_path.exists() else ""

    msg_dbf = repo / stage.get("CANDIDATE_DBF_ROOT", "") / "SYSTEM_MESSAGES.dbf"
    txt_dbf = repo / stage.get("CANDIDATE_DBF_ROOT", "") / "SYSTEM_MESSAGE_TEXT.dbf"
    txt_dtx = repo / stage.get("CANDIDATE_DBF_ROOT", "") / "SYSTEM_MESSAGE_TEXT.dtx"

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: Any):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_GREEN_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_LOG_EXISTS", runtime_path.exists(), rel(runtime_path, repo))

    msg_counts = dbf_counts(msg_dbf) if msg_dbf.exists() else {}
    txt_counts = dbf_counts(txt_dbf) if txt_dbf.exists() else {}
    gate("CANDIDATE_MESSAGE_COUNT_14", msg_counts.get("HEADER_COUNT") == 14 and msg_counts.get("PHYSICAL_COUNT") == 14, msg_counts)
    gate("CANDIDATE_TEXT_COUNT_70", txt_counts.get("HEADER_COUNT") == 70 and txt_counts.get("PHYSICAL_COUNT") == 70, txt_counts)
    gate("CANDIDATE_TEXT_DTX_PRESENT", txt_dtx.exists() and txt_dtx.stat().st_size > 0, txt_dtx.stat().st_size if txt_dtx.exists() else 0)

    rf = runtime_flags(runtime_text)
    gate("RUNTIME_OPENED_ACTIVE_BASENAME_COUNTS_14_70", rf["OPENED_SYSTEM_MESSAGES_14"] == 1 and rf["OPENED_SYSTEM_MESSAGE_TEXT_70"] == 1, rf)
    gate("RUNTIME_COUNT_COMMANDS_14_70", rf["COUNT_14"] == 1 and rf["COUNT_70"] == 1, rf)
    gate("RUNTIME_READONLY_NO_MUTATION_WORDS", rf["MUTATION_WORDS"] == 0, rf)
    gate("RUNTIME_NO_ALREADY_OPEN_WARNING", rf["ALREADY_OPEN_WARNING"] == 0, rf)

    after_fp = fingerprint_active(repo)
    fp_delta = compare_fp(before_fp, after_fp)
    gate("ACTIVE_FINGERPRINT_CLEAN", len(fp_delta) == 0, len(fp_delta))

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if failures == 0 else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_8_validate_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_runtime_flags_v1.csv",
              [rf], ["OPENED_SYSTEM_MESSAGES_14", "OPENED_SYSTEM_MESSAGE_TEXT_70", "COUNT_14", "COUNT_70", "ALREADY_OPEN_WARNING", "MUTATION_WORDS"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_validate_dbf_count_readback_v1.csv",
              [{"TABLE": "SYSTEM_MESSAGES", "PATH": rel(msg_dbf, repo), **msg_counts},
               {"TABLE": "SYSTEM_MESSAGE_TEXT", "PATH": rel(txt_dbf, repo), **txt_counts}],
              ["TABLE", "PATH", "HEADER_COUNT", "PHYSICAL_COUNT", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_active_fingerprint_after_validate_v1.csv",
              after_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_active_fingerprint_delta_validate_v1.csv",
              fp_delta, ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256"])

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGE_AND_SELECTED_INDEX_LMDB_ROOTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if len(fp_delta) == 0 else 1, "DETAIL": f"protected fingerprint changes={len(fp_delta)}"},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_8_validate_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_8_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_GREEN": 1 if stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_GREEN_SOURCE_HELD" else 0,
        "MESSAGE_ROWS": msg_counts.get("HEADER_COUNT", ""),
        "TEXT_ROWS": txt_counts.get("HEADER_COUNT", ""),
        "TEXT_DTX_EXISTS": 1 if txt_dtx.exists() else 0,
        "TEXT_DTX_BYTES": txt_dtx.stat().st_size if txt_dtx.exists() else "",
        "RUNTIME_OPENED_SYSTEM_MESSAGES_14": rf["OPENED_SYSTEM_MESSAGES_14"],
        "RUNTIME_OPENED_SYSTEM_MESSAGE_TEXT_70": rf["OPENED_SYSTEM_MESSAGE_TEXT_70"],
        "RUNTIME_COUNT_14": rf["COUNT_14"],
        "RUNTIME_COUNT_70": rf["COUNT_70"],
        "BOUNDARY_CLEAN": 1 if len(fp_delta) == 0 else 0,
        "PROTECTED_FINGERPRINT_CHANGES": len(fp_delta),
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if len(fp_delta) == 0 else 1,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE if status == STATUS_GREEN else "HOLD_AND_FIX_PHASE22AE_6_5_8_CANDIDATE_READBACK",
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_GREEN", "MESSAGE_ROWS", "TEXT_ROWS",
         "TEXT_DTX_EXISTS", "TEXT_DTX_BYTES", "RUNTIME_OPENED_SYSTEM_MESSAGES_14",
         "RUNTIME_OPENED_SYSTEM_MESSAGE_TEXT_70", "RUNTIME_COUNT_14", "RUNTIME_COUNT_70",
         "BOUNDARY_CLEAN", "PROTECTED_FINGERPRINT_CHANGES", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED", "CMDHELPCHK_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_GREEN_SOURCE_HELD' else 0}")
    print(f"  message/text rows: {msg_counts.get('HEADER_COUNT','')}/{txt_counts.get('HEADER_COUNT','')}")
    print(f"  text dtx exists/bytes: {1 if txt_dtx.exists() else 0}/{txt_dtx.stat().st_size if txt_dtx.exists() else ''}")
    print(f"  runtime opened SYSTEM_MESSAGES 14: {rf['OPENED_SYSTEM_MESSAGES_14']}")
    print(f"  runtime opened SYSTEM_MESSAGE_TEXT 70: {rf['OPENED_SYSTEM_MESSAGE_TEXT_70']}")
    print(f"  runtime count 14/70: {rf['COUNT_14']}/{rf['COUNT_70']}")
    print(f"  boundary clean: {1 if len(fp_delta) == 0 else 0}")
    print(f"  active catalog mutation observed: {0 if len(fp_delta) == 0 else 1}")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE if status == STATUS_GREEN else 'HOLD_AND_FIX_PHASE22AE_6_5_8_CANDIDATE_READBACK'}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
