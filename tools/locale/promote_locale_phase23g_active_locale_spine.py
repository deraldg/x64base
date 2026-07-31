#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_EXECUTED"
STATUS_BLOCKED = "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_BLOCKED"
NEXT_GATE = "RUN_ACTIVE_LOCALE_SPINE_READBACK_THEN_VALIDATE_PHASE23G"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
CANDIDATE_ROOT = Path("docs/locale/candidates/phase23b_shared_locale_spine_candidate")
BACKUP_ROOT_BASE = Path("docs/locale/backups")

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def rel(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)

def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def backup_existing(target: Path, backup_root: Path, repo: Path, rows: list[dict[str, Any]]) -> None:
    if not target.exists():
        return
    backup_target = backup_root / rel(target, repo)
    backup_target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_dir():
        if backup_target.exists():
            shutil.rmtree(backup_target)
        shutil.copytree(target, backup_target)
        file_count = sum(1 for p in backup_target.rglob("*") if p.is_file())
        total_bytes = sum(p.stat().st_size for p in backup_target.rglob("*") if p.is_file())
        rows.append({
            "TARGET_PATH": rel(target, repo),
            "BACKUP_PATH": rel(backup_target, repo),
            "ARTIFACT_TYPE": "DIR",
            "FILES": file_count,
            "BYTES": total_bytes,
            "SHA256": "",
            "ACTION": "BACKUP_EXISTING_DIR",
        })
    else:
        shutil.copy2(target, backup_target)
        rows.append({
            "TARGET_PATH": rel(target, repo),
            "BACKUP_PATH": rel(backup_target, repo),
            "ARTIFACT_TYPE": "FILE",
            "FILES": 1,
            "BYTES": backup_target.stat().st_size,
            "SHA256": sha256_file(backup_target),
            "ACTION": "BACKUP_EXISTING_FILE",
        })

def copy_dir_replace(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-active-locale-promotion", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23f = first_row(reports / "locale_phase23f_status_summary_v1.csv")

    candidate = repo / CANDIDATE_ROOT
    candidate_dbf = candidate / "dbf"
    candidate_indexes = candidate / "indexes"
    candidate_lmdb = candidate / "lmdb"

    active_dbf = repo / "dottalkpp/data/locale"
    active_indexes = repo / "dottalkpp/data/indexes/locale"
    active_lmdb = repo / "dottalkpp/data/lmdb/locale"

    required_pairs = [
        (candidate_dbf / "SYSTEM_LOCALES.dbf", active_dbf / "SYSTEM_LOCALES.dbf", "DBF"),
        (candidate_dbf / "SYSTEM_LOCALE_FALLBACK.dbf", active_dbf / "SYSTEM_LOCALE_FALLBACK.dbf", "DBF"),
        (candidate_indexes / "SYSTEM_LOCALES.cdx", active_indexes / "SYSTEM_LOCALES.cdx", "CDX"),
        (candidate_indexes / "SYSTEM_LOCALE_FALLBACK.cdx", active_indexes / "SYSTEM_LOCALE_FALLBACK.cdx", "CDX"),
        (candidate_lmdb / "SYSTEM_LOCALES.cdx.d", active_lmdb / "SYSTEM_LOCALES.cdx.d", "LMDB_DIR"),
        (candidate_lmdb / "SYSTEM_LOCALE_FALLBACK.cdx.d", active_lmdb / "SYSTEM_LOCALE_FALLBACK.cdx.d", "LMDB_DIR"),
    ]

    optional_pairs = [
        (candidate_dbf / "SYSTEM_LOCALES.dbt", active_dbf / "SYSTEM_LOCALES.dbt", "DBT"),
        (candidate_dbf / "SYSTEM_LOCALE_FALLBACK.dbt", active_dbf / "SYSTEM_LOCALE_FALLBACK.dbt", "DBT"),
    ]

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_ALLOWED_ACTIVE_LOCALE_PROMOTION",
         args.allow_active_locale_promotion,
         "requires --allow-active-locale-promotion")
    gate("PHASE23F_PROMOTION_PLAN_GREEN",
         phase23f.get("STATUS") == "LOCALE_PHASE23F_CANDIDATE_LOCALE_SPINE_PROMOTION_PLAN_GREEN_REPORT_ONLY",
         phase23f.get("STATUS", ""))
    gate("PHASE23F_VALIDATION_ZERO",
         phase23f.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23f.get('VALIDATION_ISSUES', '')}")
    gate("PHASE23F_ACTIVE_PROMOTION_NOT_EXECUTED",
         phase23f.get("ACTIVE_PROMOTION_EXECUTED", "") == "0",
         f"active_promotion_executed={phase23f.get('ACTIVE_PROMOTION_EXECUTED', '')}")

    for src, _dst, label in required_pairs:
        gate(f"REQUIRED_{label}_{src.name}_PRESENT", src.exists(), rel(src, repo))

    status = STATUS_BLOCKED
    mutation_rows: list[dict[str, Any]] = []
    backup_rows: list[dict[str, Any]] = []
    runtime_script_rows: list[dict[str, Any]] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = repo / BACKUP_ROOT_BASE / f"LOC-023G_ACTIVE_LOCALE_PROMOTION_BACKUP_{timestamp}"

    if failures == 0:
        for d in [active_dbf, active_indexes, active_lmdb]:
            d.mkdir(parents=True, exist_ok=True)

        for _src, dst, _label in required_pairs + optional_pairs:
            backup_existing(dst, backup_root, repo, backup_rows)

        for src, dst, label in required_pairs + optional_pairs:
            if not src.exists():
                continue
            if src.is_dir():
                copy_dir_replace(src, dst)
                file_count = sum(1 for p in dst.rglob("*") if p.is_file())
                total_bytes = sum(p.stat().st_size for p in dst.rglob("*") if p.is_file())
                mutation_rows.append({
                    "ARTIFACT_TYPE": label,
                    "SOURCE_PATH": rel(src, repo),
                    "TARGET_PATH": rel(dst, repo),
                    "FILES": file_count,
                    "BYTES": total_bytes,
                    "SHA256": "",
                    "ACTION": "COPY_DIR_REPLACE",
                })
            else:
                copy_file(src, dst)
                mutation_rows.append({
                    "ARTIFACT_TYPE": label,
                    "SOURCE_PATH": rel(src, repo),
                    "TARGET_PATH": rel(dst, repo),
                    "FILES": 1,
                    "BYTES": dst.stat().st_size,
                    "SHA256": sha256_file(dst),
                    "ACTION": "COPY_FILE",
                })

        scripts_dir = repo / "docs/locale/scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        readback_script = scripts_dir / "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_READBACK.dts"
        readback_text = "\n".join([
            "* LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_READBACK.dts",
            "* Active shared-locale spine readback proof.",
            "* Boundary: read-only active locale spine validation; no source/HELP/manualgen mutation.",
            "CLOSE ALL",
            f"SET PATH DBF {active_dbf}",
            f"SET PATH INDEXES {active_indexes}",
            f"SET PATH LMDB {active_lmdb}",
            "",
            "SELECT 0",
            "USE SYSTEM_LOCALES",
            "SET INDEX TO SYSTEM_LOCALES",
            "SET ORDER TO LOCALE_ID",
            "",
            "SELECT 1",
            "USE SYSTEM_LOCALE_FALLBACK",
            "SET INDEX TO SYSTEM_LOCALE_FALLBACK",
            "SET ORDER TO FBID",
            "",
            "SELECT 2",
            "* Phase 23G active locale spine readback complete.",
            "",
        ])
        readback_script.write_text(readback_text, encoding="utf-8")
        runtime_script_rows.append({
            "ARTIFACT": rel(readback_script, repo),
            "ROLE": "active locale spine readback script",
            "BYTES": readback_script.stat().st_size,
            "SHA256": sha256_file(readback_script),
        })

        status = STATUS_GREEN

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    dbf_copied = sum(1 for r in mutation_rows if r["ARTIFACT_TYPE"] == "DBF")
    cdx_copied = sum(1 for r in mutation_rows if r["ARTIFACT_TYPE"] == "CDX")
    lmdb_file_rows = sum(int(r["FILES"]) for r in mutation_rows if r["ARTIFACT_TYPE"] == "LMDB_DIR")

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": len(mutation_rows), "DETAIL": "Authorized Phase 23G active locale artifact copy to neutral locale roots."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_DBF", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": dbf_copied, "DETAIL": "SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK DBFs copied if green."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_CDX", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": cdx_copied, "DETAIL": "SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK CDXs copied if green."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_LMDB", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": lmdb_file_rows, "DETAIL": "LMDB env files copied if green."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
    ]

    write_csv(reports / "locale_phase23g_promotion_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_PROMOTION_AUTHORIZED": 1 if args.allow_active_locale_promotion else 0,
        "ACTIVE_PROMOTION_EXECUTED": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_LOCALE_DBF_FILES_COPIED": dbf_copied,
        "ACTIVE_LOCALE_CDX_FILES_COPIED": cdx_copied,
        "ACTIVE_LOCALE_LMDB_FILE_ROWS_COPIED": lmdb_file_rows,
        "BACKUP_ROWS": len(backup_rows),
        "READBACK_SCRIPT_STAGED": 1 if runtime_script_rows else 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "ACTIVE_PROMOTION_AUTHORIZED",
         "ACTIVE_PROMOTION_EXECUTED", "ACTIVE_LOCALE_DBF_FILES_COPIED",
         "ACTIVE_LOCALE_CDX_FILES_COPIED", "ACTIVE_LOCALE_LMDB_FILE_ROWS_COPIED",
         "BACKUP_ROWS", "READBACK_SCRIPT_STAGED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23g_promotion_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23g_active_promotion_inventory_v1.csv", mutation_rows,
              ["ARTIFACT_TYPE", "SOURCE_PATH", "TARGET_PATH", "FILES", "BYTES", "SHA256", "ACTION"])
    write_csv(reports / "locale_phase23g_active_backup_inventory_v1.csv", backup_rows,
              ["TARGET_PATH", "BACKUP_PATH", "ARTIFACT_TYPE", "FILES", "BYTES", "SHA256", "ACTION"])
    write_csv(reports / "locale_phase23g_runtime_script_inventory_v1.csv", runtime_script_rows,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23g_promotion_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  active promotion authorized: {1 if args.allow_active_locale_promotion else 0}")
    print(f"  active promotion executed: {1 if status == STATUS_GREEN else 0}")
    print(f"  active locale dbf files copied: {dbf_copied}")
    print(f"  active locale cdx files copied: {cdx_copied}")
    print(f"  active locale lmdb file rows copied: {lmdb_file_rows}")
    print(f"  backup rows: {len(backup_rows)}")
    print(f"  readback script staged: {1 if runtime_script_rows else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
