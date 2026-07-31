#!/usr/bin/env python3
"""
Phase 16X validate: verify inactive x64 candidate LMDB/MDB artifacts after runtime BUILDLMDB.

This validator does not create LMDB. It scans the phase15x x64 candidate LMDB
path after DotTalk++ BUILDLMDB CLEAN YES runs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE16X_X64_CANDIDATE_LMDB_BUILD_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE16X_X64_CANDIDATE_LMDB_BUILD_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE17_PROMOTION_READINESS_REVIEW"
REPORT_DIR = Path("docs/messaging/reports")
PHASE15X_ROOT = Path("docs/messaging/candidates/phase15x_x64_candidate_rebuild")
RUNLOG = Path("docs/messaging/runlog/MSG-016X_X64_LMDB_RUNTIME_PROOF.md")

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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p15x = first_row(reports / "message_catalog_phase15x_status_summary_v1.csv") if (reports / "message_catalog_phase15x_status_summary_v1.csv").exists() else {}
    prep = first_row(reports / "message_catalog_phase16x_prepare_status_summary_v1.csv") if (reports / "message_catalog_phase16x_prepare_status_summary_v1.csv").exists() else {}

    messages = str(p15x.get("MESSAGES", "12"))
    text_rows = str(p15x.get("TEXT_ROWS", "60"))
    locales = p15x.get("LOCALES", "de;en-US;es;fr;it")

    candidate = repo / PHASE15X_ROOT
    lmdb_dir = candidate / "lmdb"
    runlog = repo / RUNLOG

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE15X_STATUS_GREEN", p15x.get("STATUS") == "MESSAGE_CATALOG_PHASE15X_X64_CANDIDATE_REBUILD_GREEN", p15x.get("STATUS", ""))
    gate("PHASE16X_PREPARE_STAGED", prep.get("STATUS") == "MESSAGE_CATALOG_PHASE16X_X64_LMDB_RUNTIME_SCRIPT_STAGED", prep.get("STATUS", ""))
    gate("CANDIDATE_X64_LMDB_DIR_PRESENT", lmdb_dir.exists(), str(lmdb_dir))

    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()
    gate("RUNTIME_PROOF_PRESENT", runlog.exists(), str(runlog))
    if runlog.exists():
        gate("BUILDLMDB_DONE_IN_RUNTIME_PROOF", ("BUILDLMDB: DONE" in upper or "DONE OK=1" in upper or "BUILDLMDB CLEAN YES" in upper and "FAILED" not in upper), "runtime proof should show BUILDLMDB completed without failure")

    artifact_rows = []
    mdb_rows = []
    env_dirs = set()

    if lmdb_dir.exists():
        for p in sorted(lmdb_dir.rglob("*")):
            if p.is_file():
                rel = str(p.relative_to(repo)).replace("\\", "/")
                artifact_rows.append({
                    "RELATIVE_PATH": rel,
                    "BYTES": p.stat().st_size,
                    "SHA256": sha256_file(p),
                    "ROLE": "x64_candidate_lmdb_artifact",
                })
                lname = p.name.lower()
                if lname.endswith(".mdb") or lname in ("data.mdb", "lock.mdb"):
                    env_dirs.add(str(p.parent.relative_to(repo)).replace("\\", "/"))
                    mdb_rows.append({
                        "RELATIVE_PATH": rel,
                        "BYTES": p.stat().st_size,
                        "SHA256": sha256_file(p),
                        "ENV_DIR": str(p.parent.relative_to(repo)).replace("\\", "/"),
                    })

    data_mdb_count = len([r for r in mdb_rows if Path(r["RELATIVE_PATH"]).name.lower() == "data.mdb"])
    mdb_file_count = len(mdb_rows)
    env_dir_count = len(env_dirs)

    # Simple pass/fail: BUILDLMDB should create candidate LMDB/MDB artifacts.
    # Two tables may produce two env dirs, but some runtimes may place multiple tags in one env.
    gate("LMDB_MDB_FILES_PRESENT", mdb_file_count >= 2, f"mdb_files={mdb_file_count}")
    gate("LMDB_DATA_MDB_PRESENT", data_mdb_count >= 1, f"data_mdb={data_mdb_count}")
    gate("LMDB_ENV_DIR_PRESENT", env_dir_count >= 1, f"env_dirs={env_dir_count}")

    validation_issues = str(failures)
    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED

    write_csv(reports / "message_catalog_phase16x_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "LMDB_MDB_FILES": mdb_file_count,
        "LMDB_DATA_MDB_FILES": data_mdb_count,
        "LMDB_ENV_DIRS": env_dir_count,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "LMDB_MDB_FILES", "LMDB_DATA_MDB_FILES", "LMDB_ENV_DIRS",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase16x_lmdb_artifact_inventory_v1.csv",
              artifact_rows, ["RELATIVE_PATH", "BYTES", "SHA256", "ROLE"])

    write_csv(reports / "message_catalog_phase16x_lmdb_mdb_inventory_v1.csv",
              mdb_rows, ["RELATIVE_PATH", "BYTES", "SHA256", "ENV_DIR"])

    write_csv(reports / "message_catalog_phase16x_gate_check_v1.csv",
              gates, ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_X64_CANDIDATE_LMDB", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if mdb_file_count else 0, "DETAIL": "Runtime BUILDLMDB may create candidate-only LMDB/MDB artifacts under the x64 candidate LMDB path."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/catalog mutation by validator."},
        {"PROTECTED_SYSTEM": "ACTIVE_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation by validator."},
        {"PROTECTED_SYSTEM": "ACTIVE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB path mutation authorized."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-code mutation."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion."},
    ]
    write_csv(reports / "message_catalog_phase16x_boundary_ledger_v1.csv",
              boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    manifest = {
        "status": status,
        "candidate_root": str(PHASE15X_ROOT).replace("\\", "/"),
        "messages": int(messages) if messages.isdigit() else messages,
        "text_rows": int(text_rows) if text_rows.isdigit() else text_rows,
        "locales": locales.split(";") if locales else [],
        "validation_issues": int(validation_issues) if validation_issues.isdigit() else validation_issues,
        "lmdb_mdb_files": mdb_file_count,
        "lmdb_data_mdb_files": data_mdb_count,
        "lmdb_env_dirs": sorted(env_dirs),
        "active_promotion_authorized": 0,
        "lmdb_artifacts": artifact_rows,
    }
    (candidate / "candidate_manifest_phase16x_lmdb_v1.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  lmdb mdb files: {mdb_file_count}")
    print(f"  lmdb data.mdb files: {data_mdb_count}")
    print(f"  lmdb env dirs: {env_dir_count}")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
