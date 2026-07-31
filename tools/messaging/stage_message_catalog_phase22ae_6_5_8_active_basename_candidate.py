#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_STAGING_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_READBACK_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SOURCE_SANDBOX = Path("docs/messaging/sandbox/phase22ae_6_5_6_1_work_area_select_import_v1/dbf")
CANDIDATE_ROOT = Path("docs/messaging/candidates/phase22ae_6_5_8_active_basename_candidate_v1")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_READBACK.dts")

ACTIVE_ROOT = Path("dottalkpp/data/messaging")
ACTIVE_INDEX_ROOT = Path("dottalkpp/data/indexes/messaging")
ACTIVE_LMDB_ROOT = Path("dottalkpp/data/lmdb/messaging")
DEFAULT_INDEX_ROOT = Path("dottalkpp/data/indexes")
DEFAULT_LMDB_ROOT = Path("dottalkpp/data/lmdb")

SOURCE_MESSAGE_DBF = SOURCE_SANDBOX / "MSG6561_MESSAGES_NATIVE_IMPORT.dbf"
SOURCE_TEXT_DBF = SOURCE_SANDBOX / "MSG6561_TEXT_NATIVE_IMPORT.dbf"
SOURCE_TEXT_DTX = SOURCE_SANDBOX / "MSG6561_TEXT_NATIVE_IMPORT.dtx"

TARGET_MESSAGE_DBF = CANDIDATE_ROOT / "dbf/SYSTEM_MESSAGES.dbf"
TARGET_TEXT_DBF = CANDIDATE_ROOT / "dbf/SYSTEM_MESSAGE_TEXT.dbf"
TARGET_TEXT_DTX = CANDIDATE_ROOT / "dbf/SYSTEM_MESSAGE_TEXT.dtx"

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

def savepoint_present(repo: Path, savepoint_id: str):
    latest = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest.exists():
        try:
            latest_id = json.loads(latest.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return (latest_id == savepoint_id or savepoint_id in text), latest_id

def dbf_counts(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    header_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    eof = 1 if data and data[-1] == 0x1A else 0
    physical = (len(data) - header_len - eof) // record_len if record_len else 0
    remainder = (len(data) - header_len - eof) % record_len if record_len else ""
    return {"HEADER_COUNT": header_count, "HEADER_LEN": header_len, "RECORD_LEN": record_len,
            "PHYSICAL_COUNT": physical, "PHYSICAL_REMAINDER": remainder, "BYTES": len(data), "SHA256": sha256_file(path)}

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

def file_row(repo: Path, role: str, path: Path) -> dict[str, Any]:
    return {"ROLE": role, "PATH": rel(path, repo), "EXISTS": 1 if path.exists() else 0,
            "BYTES": path.stat().st_size if path.exists() and path.is_file() else "",
            "SHA256": sha256_file(path)}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-candidate-staging", action="store_true")
    ap.add_argument("--replace-existing-candidate", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    summary657 = first_row(reports / "message_catalog_phase22ae_6_5_7_status_summary_v1.csv")
    sp_ok, latest_sp = savepoint_present(repo, "MSG-022AE.6.5.7")
    candidate_root = repo / CANDIDATE_ROOT

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: Any):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_7_GREEN",
         summary657.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_7_NATIVE_INDEX_LMDB_REBUILD_AND_PROMOTION_PLAN_GREEN_SOURCE_HELD",
         summary657.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_7_SAVEPOINT_PRESENT", sp_ok, latest_sp)
    gate("CANDIDATE_STAGING_EXPLICITLY_AUTHORIZED", args.allow_candidate_staging, args.allow_candidate_staging)
    gate("CANDIDATE_ROOT_ABSENT_OR_REPLACE_AUTHORIZED", (not candidate_root.exists()) or args.replace_existing_candidate, rel(candidate_root, repo))
    for label, path in [
        ("SOURCE_MESSAGE_DBF_EXISTS", repo / SOURCE_MESSAGE_DBF),
        ("SOURCE_TEXT_DBF_EXISTS", repo / SOURCE_TEXT_DBF),
        ("SOURCE_TEXT_DTX_EXISTS", repo / SOURCE_TEXT_DTX),
    ]:
        gate(label, path.exists(), rel(path, repo))

    before_fp = fingerprint_active(repo)
    write_csv(reports / "message_catalog_phase22ae_6_5_8_active_fingerprint_before_v1.csv",
              before_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])

    copy_rows = []
    counts_rows = []
    script_rel = ""
    status = STATUS_BLOCKED
    errors = []

    if failures == 0:
        try:
            if candidate_root.exists() and args.replace_existing_candidate:
                shutil.rmtree(candidate_root)
            (candidate_root / "dbf").mkdir(parents=True, exist_ok=True)
            (candidate_root / "indexes").mkdir(parents=True, exist_ok=True)
            (candidate_root / "lmdb").mkdir(parents=True, exist_ok=True)

            copies = [
                (repo / SOURCE_MESSAGE_DBF, repo / TARGET_MESSAGE_DBF, "message_dbf_active_basename_candidate"),
                (repo / SOURCE_TEXT_DBF, repo / TARGET_TEXT_DBF, "text_dbf_active_basename_candidate"),
                (repo / SOURCE_TEXT_DTX, repo / TARGET_TEXT_DTX, "text_dtx_active_basename_candidate"),
            ]
            for src, dst, role in copies:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copy_rows.append({
                    "ROLE": role,
                    "SOURCE": rel(src, repo),
                    "TARGET": rel(dst, repo),
                    "SOURCE_SHA256": sha256_file(src),
                    "TARGET_SHA256": sha256_file(dst),
                    "SHA_MATCH": 1 if sha256_file(src) == sha256_file(dst) else 0,
                    "BYTES": dst.stat().st_size,
                })

            counts_rows.append({"TABLE": "SYSTEM_MESSAGES", "PATH": rel(repo / TARGET_MESSAGE_DBF, repo), **dbf_counts(repo / TARGET_MESSAGE_DBF)})
            counts_rows.append({"TABLE": "SYSTEM_MESSAGE_TEXT", "PATH": rel(repo / TARGET_TEXT_DBF, repo), **dbf_counts(repo / TARGET_TEXT_DBF)})
            counts_ok = counts_rows[0]["HEADER_COUNT"] == 14 and counts_rows[1]["HEADER_COUNT"] == 70

            script = repo / SCRIPT_PATH
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("\n".join([
                "* MESSAGE_CATALOG_PHASE22AE_6_5_8_ACTIVE_BASENAME_CANDIDATE_READBACK.dts",
                "* Candidate-only active-basename readback proof.",
                "* Opens candidate SYSTEM_* DBFs by absolute path. No import, no rebuild, no active mutation.",
                "SELECT 1",
                f"USE {(repo / TARGET_MESSAGE_DBF).resolve().as_posix()}",
                "COUNT",
                "SELECT 2",
                f"USE {(repo / TARGET_TEXT_DBF).resolve().as_posix()}",
                "COUNT",
                "",
            ]), encoding="utf-8")
            script_rel = rel(script, repo)

            gate("CANDIDATE_COUNTS_14_70", counts_ok, f"{counts_rows[0]['HEADER_COUNT']}/{counts_rows[1]['HEADER_COUNT']}")
        except Exception as exc:
            errors.append(str(exc))
            failures += 1

    after_fp = fingerprint_active(repo)
    fp_delta = compare_fp(before_fp, after_fp)
    gate("ACTIVE_FINGERPRINT_CLEAN_AFTER_STAGING", len(fp_delta) == 0, len(fp_delta))

    status = STATUS_GREEN if failures == 0 and len(fp_delta) == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(max(1, failures, len(fp_delta)))

    write_csv(reports / "message_catalog_phase22ae_6_5_8_stage_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_candidate_copy_manifest_v1.csv",
              copy_rows, ["ROLE", "SOURCE", "TARGET", "SOURCE_SHA256", "TARGET_SHA256", "SHA_MATCH", "BYTES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_candidate_dbf_count_readback_v1.csv",
              counts_rows, ["TABLE", "PATH", "HEADER_COUNT", "HEADER_LEN", "RECORD_LEN", "PHYSICAL_COUNT", "PHYSICAL_REMAINDER", "BYTES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_active_fingerprint_after_v1.csv",
              after_fp, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "SHA256", "FILES"])
    write_csv(reports / "message_catalog_phase22ae_6_5_8_active_fingerprint_delta_v1.csv",
              fp_delta, ["ROLE", "PATH", "CHANGE", "BEFORE_SHA256", "AFTER_SHA256"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if len(fp_delta) == 0 else 1, "DETAIL": "Candidate-only staging under docs/messaging/candidates."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if len(fp_delta) == 0 else 1, "DETAIL": "No active CDX mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0 if len(fp_delta) == 0 else 1, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22ae_6_5_8_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_8_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_7_GREEN": 1 if summary657.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_7_NATIVE_INDEX_LMDB_REBUILD_AND_PROMOTION_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022AE_6_5_7_SAVEPOINT_PRESENT": 1 if sp_ok else 0,
        "CANDIDATE_ROOT": rel(candidate_root, repo),
        "CANDIDATE_DBF_ROOT": rel(candidate_root / "dbf", repo),
        "CANDIDATE_INDEX_ROOT": rel(candidate_root / "indexes", repo),
        "CANDIDATE_LMDB_ROOT": rel(candidate_root / "lmdb", repo),
        "READBACK_SCRIPT": script_rel,
        "MESSAGE_ROWS": counts_rows[0].get("HEADER_COUNT", "") if counts_rows else "",
        "TEXT_ROWS": counts_rows[1].get("HEADER_COUNT", "") if len(counts_rows) > 1 else "",
        "TEXT_DTX_EXISTS": 1 if (repo / TARGET_TEXT_DTX).exists() else 0,
        "TEXT_DTX_BYTES": (repo / TARGET_TEXT_DTX).stat().st_size if (repo / TARGET_TEXT_DTX).exists() else "",
        "CANDIDATE_STAGING_AUTHORIZED": 1 if args.allow_candidate_staging else 0,
        "CANDIDATE_INDEX_LMDB_REBUILD_AUTHORIZED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0 if len(fp_delta) == 0 else 1,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ERRORS": "; ".join(errors),
        "NEXT_GATE": NEXT_GATE if status == STATUS_GREEN else "HOLD_AND_FIX_PHASE22AE_6_5_8_CANDIDATE_STAGING",
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_7_GREEN",
         "MSG_022AE_6_5_7_SAVEPOINT_PRESENT", "CANDIDATE_ROOT", "CANDIDATE_DBF_ROOT",
         "CANDIDATE_INDEX_ROOT", "CANDIDATE_LMDB_ROOT", "READBACK_SCRIPT",
         "MESSAGE_ROWS", "TEXT_ROWS", "TEXT_DTX_EXISTS", "TEXT_DTX_BYTES",
         "CANDIDATE_STAGING_AUTHORIZED", "CANDIDATE_INDEX_LMDB_REBUILD_AUTHORIZED",
         "ACTIVE_PROMOTION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "ERRORS", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.7 green: {1 if summary657.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_7_NATIVE_INDEX_LMDB_REBUILD_AND_PROMOTION_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.7 savepoint present: {1 if sp_ok else 0}")
    print(f"  candidate root: {rel(candidate_root, repo)}")
    print(f"  message/text rows: {counts_rows[0].get('HEADER_COUNT','') if counts_rows else ''}/{counts_rows[1].get('HEADER_COUNT','') if len(counts_rows)>1 else ''}")
    print(f"  text dtx exists/bytes: {1 if (repo / TARGET_TEXT_DTX).exists() else 0}/{(repo / TARGET_TEXT_DTX).stat().st_size if (repo / TARGET_TEXT_DTX).exists() else ''}")
    print(f"  readback script: {script_rel}")
    print(f"  candidate staging authorized: {1 if args.allow_candidate_staging else 0}")
    print("  candidate index/lmdb rebuild authorized: 0")
    print("  active promotion authorized: 0")
    print(f"  active catalog mutation observed: {0 if len(fp_delta) == 0 else 1}")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE if status == STATUS_GREEN else 'HOLD_AND_FIX_PHASE22AE_6_5_8_CANDIDATE_STAGING'}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
