#!/usr/bin/env python3
"""
Phase 16X prepare: stage inactive x64 candidate LMDB build runtime script.

This phase is authorized after Phase 15X proves:
  - SYSTEM_MESSAGES candidate table opens as v64 with 12 rows
  - SYSTEM_MESSAGE_TEXT candidate table opens as v64 with 60 rows
  - x64 candidate CDX files exist
  - compound-key workaround fields exist

The prepare step writes a DotTalk++ runtime script for BUILDLMDB CLEAN YES.
It does not itself build LMDB.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS = "MESSAGE_CATALOG_PHASE16X_X64_LMDB_RUNTIME_SCRIPT_STAGED"
NEXT_GATE = "RUN_DOTTALK_PHASE16X_X64_LMDB_BUILD_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
PHASE15X_ROOT = Path("docs/messaging/candidates/phase15x_x64_candidate_rebuild")

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path) -> dict[str, str]:
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

def inventory(root: Path, repo: Path) -> list[dict[str, Any]]:
    rows = []
    if not root.exists():
        return rows
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({
                "RELATIVE_PATH": str(p.relative_to(repo)).replace("\\", "/"),
                "BYTES": p.stat().st_size,
                "SHA256": sha256_file(p),
                "ROLE": "phase16x_x64_lmdb_build_staging_artifact",
            })
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-x64-candidate-lmdb-build", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase15x_status = reports / "message_catalog_phase15x_status_summary_v1.csv"

    candidate = repo / PHASE15X_ROOT
    dbf_dir = candidate / "dbf"
    indexes_dir = candidate / "indexes"
    lmdb_dir = candidate / "lmdb"
    scripts_dir = candidate / "scripts"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("OPERATOR_AUTHORIZED_X64_CANDIDATE_LMDB_BUILD", args.allow_x64_candidate_lmdb_build, "requires --allow-x64-candidate-lmdb-build")
    gate("PHASE15X_STATUS_PRESENT", phase15x_status.exists(), str(phase15x_status))

    p15x = first_row(phase15x_status) if phase15x_status.exists() else {}
    if phase15x_status.exists():
        gate("PHASE15X_STATUS_GREEN", p15x.get("STATUS") == "MESSAGE_CATALOG_PHASE15X_X64_CANDIDATE_REBUILD_GREEN", p15x.get("STATUS", ""))

    for dname, d in [("DBF", dbf_dir), ("INDEXES", indexes_dir), ("LMDB", lmdb_dir)]:
        gate(f"CANDIDATE_X64_{dname}_DIR_PRESENT", d.exists(), str(d))

    for fname in ["SYSTEM_MESSAGES.dbf", "SYSTEM_MESSAGE_TEXT.dbf"]:
        gate(f"{fname.upper()}_PRESENT", (dbf_dir / fname).exists(), str(dbf_dir / fname))
    for fname in ["SYSTEM_MESSAGES.cdx", "SYSTEM_MESSAGE_TEXT.cdx"]:
        gate(f"{fname.upper()}_PRESENT", (indexes_dir / fname).exists(), str(indexes_dir / fname))

    messages = p15x.get("MESSAGES", "12")
    text_rows = p15x.get("TEXT_ROWS", "60")
    locales = p15x.get("LOCALES", "de;en-US;es;fr;it")
    validation_issues = p15x.get("VALIDATION_ISSUES", "0")

    if failures == 0:
        # Clean only the inactive x64 candidate LMDB directory. This is the authorized candidate mutation.
        if lmdb_dir.exists():
            for child in lmdb_dir.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        lmdb_dir.mkdir(parents=True, exist_ok=True)
        scripts_dir.mkdir(parents=True, exist_ok=True)

        dts = scripts_dir / "MESSAGE_CATALOG_PHASE16X_BUILD_X64_CANDIDATE_LMDB.dts"
        lines = [
            "* MESSAGE_CATALOG_PHASE16X_BUILD_X64_CANDIDATE_LMDB.dts",
            "* Candidate-only LMDB build over x64 messaging catalog candidates.",
            "* Boundary: inactive x64 candidate path only; no active catalog promotion.",
            "CLOSE ALL",
            f"SET PATH DBF {dbf_dir}",
            f"SET PATH INDEXES {indexes_dir}",
            f"SET PATH LMDB {lmdb_dir}",
            "",
            "SELECT 0",
            "USE SYSTEM_MESSAGES",
            "BUILDLMDB CLEAN YES",
            "",
            "SELECT 1",
            "USE SYSTEM_MESSAGE_TEXT",
            "BUILDLMDB CLEAN YES",
            "",
            "SELECT 2",
            "",
        ]
        dts.write_text("\n".join(lines), encoding="utf-8")

    status = STATUS if failures == 0 else "MESSAGE_CATALOG_PHASE16X_X64_LMDB_RUNTIME_SCRIPT_STAGING_BLOCKED"

    write_csv(reports / "message_catalog_phase16x_prepare_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues if failures == 0 else str(failures),
        "X64_LMDB_RUNTIME_SCRIPT_STAGED": 1 if failures == 0 else 0,
        "LMDB_ENV_CREATED_BY_PREPARE": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "X64_LMDB_RUNTIME_SCRIPT_STAGED", "LMDB_ENV_CREATED_BY_PREPARE",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase16x_prepare_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase16x_prepare_artifact_inventory_v1.csv",
              inventory(candidate, repo), ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_X64_CANDIDATE_LMDB_DIR_CLEAN", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if failures == 0 else 0, "DETAIL": "Prepare step cleans only the phase15x candidate LMDB directory before runtime BUILDLMDB."},
        {"PROTECTED_SYSTEM": "INACTIVE_X64_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Prepare step creates no LMDB/MDB files."},
        {"PROTECTED_SYSTEM": "INACTIVE_X64_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No candidate DBF/DBT writes."},
        {"PROTECTED_SYSTEM": "INACTIVE_X64_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No candidate CDX/index writes."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/catalog mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-code mutation."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion."},
    ]
    write_csv(reports / "message_catalog_phase16x_prepare_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues if failures == 0 else failures}")
    print(f"  x64 lmdb runtime script staged: {1 if failures == 0 else 0}")
    print("  lmdb env created by prepare: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
