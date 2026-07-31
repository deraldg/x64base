#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_READY = "LOCALE_PHASE23C_CANDIDATE_X64_DBF_RUNTIME_EXECUTION_READY"
STATUS_BLOCKED = "LOCALE_PHASE23C_CANDIDATE_X64_DBF_RUNTIME_EXECUTION_PREP_BLOCKED"
NEXT_GATE = "RUN_DOTTALK_CREATE_AND_READBACK_THEN_VALIDATE_PHASE23C"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
CANDIDATE_ROOT = Path("docs/locale/candidates/phase23b_shared_locale_spine_candidate")

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

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-candidate-runtime-execution", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase23b = first_row(reports / "locale_phase23b_status_summary_v1.csv")
    proven_locales = phase23b.get("PROVEN_LOCALES_FROM_23A", "de;en-US;es;fr;it")

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    candidate = repo / CANDIDATE_ROOT
    scripts_dir = candidate / "scripts"
    create_script = scripts_dir / "LOCALE_PHASE23B_CREATE_X64_LOCALE_SPINE_CANDIDATES.dts"
    cdx_script = scripts_dir / "LOCALE_PHASE23B_CREATE_CANDIDATE_CDX_TAGS.dts"

    gate("OPERATOR_ALLOWED_CANDIDATE_RUNTIME_EXECUTION",
         args.allow_candidate_runtime_execution,
         "requires --allow-candidate-runtime-execution")
    gate("PHASE23B_STAGING_GREEN",
         phase23b.get("STATUS") == "LOCALE_PHASE23B_CANDIDATE_SYSTEM_LOCALE_SCHEMA_STAGING_GREEN",
         phase23b.get("STATUS", ""))
    gate("PHASE23B_VALIDATION_ZERO",
         phase23b.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={phase23b.get('VALIDATION_ISSUES', '')}")
    gate("CREATE_SCRIPT_PRESENT", create_script.exists(), str(create_script))
    gate("CDX_SCRIPT_PRESENT_FOR_LATER", cdx_script.exists(), str(cdx_script))

    status = STATUS_READY if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    readback_script = scripts_dir / "LOCALE_PHASE23C_READBACK_X64_LOCALE_SPINE_CANDIDATES.dts"
    if status == STATUS_READY:
        scripts_dir.mkdir(parents=True, exist_ok=True)
        dbf = candidate / "dbf"
        indexes = candidate / "indexes"
        lmdb = candidate / "lmdb"
        readback = "\n".join([
            "* LOCALE_PHASE23C_READBACK_X64_LOCALE_SPINE_CANDIDATES.dts",
            "* Candidate-only readback proof for shared locale spine x64 DBFs.",
            "* Boundary: inactive candidate path only; no active catalog promotion.",
            "CLOSE ALL",
            f"SET PATH DBF {dbf}",
            f"SET PATH INDEXES {indexes}",
            f"SET PATH LMDB {lmdb}",
            "",
            "SELECT 0",
            "USE SYSTEM_LOCALES",
            "",
            "SELECT 1",
            "USE SYSTEM_LOCALE_FALLBACK",
            "",
            "SELECT 2",
            "* Phase 23C x64 locale spine candidate readback complete.",
            "",
        ])
        readback_script.write_text(readback, encoding="utf-8")

    staged = []
    for p, role in [
        (create_script, "candidate x64 DBF create/seed script to execute in DotTalk++"),
        (readback_script, "candidate x64 DBF readback proof script"),
    ]:
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            staged.append({
                "ARTIFACT": p.relative_to(repo).as_posix(),
                "ROLE": role,
                "BYTES": p.stat().st_size,
                "SHA256": sha256_text(text),
            })

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_DBF", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 23C authorizes candidate-only DBF runtime execution by operator; prepare script itself creates no DBFs."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "CDX execution deferred to later phase."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "LMDB execution deferred to later phase."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
    ]

    write_csv(reports / "locale_phase23c_prepare_status_summary_v1.csv", [{
        "STATUS": status,
        "PROVEN_LOCALES_FROM_23A": proven_locales,
        "VALIDATION_ISSUES": validation_issues,
        "CANDIDATE_RUNTIME_EXECUTION_AUTHORIZED": 1 if args.allow_candidate_runtime_execution else 0,
        "CREATE_SCRIPT_PRESENT": 1 if create_script.exists() else 0,
        "READBACK_SCRIPT_STAGED": 1 if readback_script.exists() else 0,
        "CANDIDATE_DBF_FILES_CREATED_BY_PREPARE": 0,
        "CANDIDATE_CDX_FILES_CREATED_BY_PREPARE": 0,
        "CANDIDATE_LMDB_ENVS_CREATED_BY_PREPARE": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "PROVEN_LOCALES_FROM_23A", "VALIDATION_ISSUES",
         "CANDIDATE_RUNTIME_EXECUTION_AUTHORIZED", "CREATE_SCRIPT_PRESENT",
         "READBACK_SCRIPT_STAGED", "CANDIDATE_DBF_FILES_CREATED_BY_PREPARE",
         "CANDIDATE_CDX_FILES_CREATED_BY_PREPARE", "CANDIDATE_LMDB_ENVS_CREATED_BY_PREPARE",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23c_prepare_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23c_prepare_artifact_inventory_v1.csv", staged,
              ["ARTIFACT", "ROLE", "BYTES", "SHA256"])
    write_csv(reports / "locale_phase23c_prepare_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  proven locales from 23A: {proven_locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  candidate runtime execution authorized: {1 if args.allow_candidate_runtime_execution else 0}")
    print(f"  create script present: {1 if create_script.exists() else 0}")
    print(f"  readback script staged: {1 if readback_script.exists() else 0}")
    print("  candidate dbf files created by prepare: 0")
    print("  candidate cdx files created by prepare: 0")
    print("  candidate lmdb envs created by prepare: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_READY else 2

if __name__ == "__main__":
    raise SystemExit(main())
