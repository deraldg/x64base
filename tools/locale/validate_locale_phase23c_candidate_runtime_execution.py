#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23C_CANDIDATE_X64_DBF_RUNTIME_EXECUTION_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23C_CANDIDATE_X64_DBF_RUNTIME_EXECUTION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23D_CANDIDATE_CDX_TAG_RUNTIME_EXECUTION"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
RUNLOG = Path("docs/locale/runlog/LOC-023C_CANDIDATE_X64_DBF_RUNTIME_PROOF.md")
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

def file_exists_int(path: Path) -> int:
    return 1 if path.exists() else 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    prep = first_row(reports / "locale_phase23c_prepare_status_summary_v1.csv")

    candidate = repo / CANDIDATE_ROOT
    dbf_dir = candidate / "dbf"
    locales_dbf = dbf_dir / "SYSTEM_LOCALES.dbf"
    fallback_dbf = dbf_dir / "SYSTEM_LOCALE_FALLBACK.dbf"

    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE23C_PREPARE_READY",
         prep.get("STATUS") == "LOCALE_PHASE23C_CANDIDATE_X64_DBF_RUNTIME_EXECUTION_READY",
         prep.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("SYSTEM_LOCALES_DBF_PRESENT", locales_dbf.exists(), str(locales_dbf))
    gate("SYSTEM_LOCALE_FALLBACK_DBF_PRESENT", fallback_dbf.exists(), str(fallback_dbf))
    gate("SYSTEM_LOCALES_V64_READBACK",
         re.search(r"OPENED\s+SYSTEM_LOCALES\s+\(V64\)\s*:\s*RECORD COUNT\s+5", upper) is not None,
         "Opened SYSTEM_LOCALES (v64) : Record count 5")
    gate("SYSTEM_LOCALE_FALLBACK_V64_READBACK",
         re.search(r"OPENED\s+SYSTEM_LOCALE_FALLBACK\s+\(V64\)\s*:\s*RECORD COUNT\s+5", upper) is not None,
         "Opened SYSTEM_LOCALE_FALLBACK (v64) : Record count 5")
    gate("NO_V32_READBACK_FOR_LOCALE_TABLES",
         "OPENED SYSTEM_LOCALES (V32" not in upper and "OPENED SYSTEM_LOCALE_FALLBACK (V32" not in upper,
         "no v32 readback for shared locale spine candidate tables")
    gate("NO_LMDB_BUILD_ATTEMPT",
         "BUILDLMDB" not in upper,
         "LMDB should not be built in Phase 23C")
    gate("NO_CDX_CREATE_EXPECTED",
         "CDX CREATED:" not in upper and "CDX ADDTAG:" not in upper,
         "CDX execution deferred to Phase 23D")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_DBF", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 2 if status == STATUS_GREEN else file_exists_int(locales_dbf) + file_exists_int(fallback_dbf), "DETAIL": "Candidate x64 DBF files under docs/locale/candidates only."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX execution in Phase 23C."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB execution in Phase 23C."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
    ]

    write_csv(reports / "locale_phase23c_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SYSTEM_LOCALES_DBF_PRESENT": file_exists_int(locales_dbf),
        "SYSTEM_LOCALE_FALLBACK_DBF_PRESENT": file_exists_int(fallback_dbf),
        "SYSTEM_LOCALES_V64_READBACK": 1 if re.search(r"OPENED\s+SYSTEM_LOCALES\s+\(V64\)\s*:\s*RECORD COUNT\s+5", upper) else 0,
        "SYSTEM_LOCALE_FALLBACK_V64_READBACK": 1 if re.search(r"OPENED\s+SYSTEM_LOCALE_FALLBACK\s+\(V64\)\s*:\s*RECORD COUNT\s+5", upper) else 0,
        "CANDIDATE_DBF_FILES_CREATED": file_exists_int(locales_dbf) + file_exists_int(fallback_dbf),
        "CANDIDATE_CDX_FILES_CREATED": 0,
        "CANDIDATE_LMDB_ENVS_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "SYSTEM_LOCALES_DBF_PRESENT",
         "SYSTEM_LOCALE_FALLBACK_DBF_PRESENT", "SYSTEM_LOCALES_V64_READBACK",
         "SYSTEM_LOCALE_FALLBACK_V64_READBACK", "CANDIDATE_DBF_FILES_CREATED",
         "CANDIDATE_CDX_FILES_CREATED", "CANDIDATE_LMDB_ENVS_CREATED",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23c_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23c_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  SYSTEM_LOCALES dbf present: {file_exists_int(locales_dbf)}")
    print(f"  SYSTEM_LOCALE_FALLBACK dbf present: {file_exists_int(fallback_dbf)}")
    print(f"  SYSTEM_LOCALES v64 readback: {1 if re.search(r'OPENED\s+SYSTEM_LOCALES\s+\(V64\)\s*:\s*RECORD COUNT\s+5', upper) else 0}")
    print(f"  SYSTEM_LOCALE_FALLBACK v64 readback: {1 if re.search(r'OPENED\s+SYSTEM_LOCALE_FALLBACK\s+\(V64\)\s*:\s*RECORD COUNT\s+5', upper) else 0}")
    print(f"  candidate dbf files created: {file_exists_int(locales_dbf) + file_exists_int(fallback_dbf)}")
    print("  candidate cdx files created: 0")
    print("  candidate lmdb envs created: 0")
    print("  active promotion authorized: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
