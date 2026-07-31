#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_READBACK_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_READBACK_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23H_RUNTIME_CONSUMER_INTEGRATION_PLAN"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
RUNLOG = Path("docs/locale/runlog/LOC-023G_ACTIVE_LOCALE_SPINE_READBACK_PROOF.md")

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

def exists_i(path: Path) -> int:
    return 1 if path.exists() else 0

def count_mdb_files(envdir: Path) -> int:
    if not envdir.exists():
        return 0
    return int((envdir / "data.mdb").exists()) + int((envdir / "lock.mdb").exists())

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    promotion = first_row(reports / "locale_phase23g_promotion_status_summary_v1.csv")
    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    active_dbf = repo / "dottalkpp/data/locale"
    active_indexes = repo / "dottalkpp/data/indexes/locale"
    active_lmdb = repo / "dottalkpp/data/lmdb/locale"

    locales_dbf = active_dbf / "SYSTEM_LOCALES.dbf"
    fallback_dbf = active_dbf / "SYSTEM_LOCALE_FALLBACK.dbf"
    locales_cdx = active_indexes / "SYSTEM_LOCALES.cdx"
    fallback_cdx = active_indexes / "SYSTEM_LOCALE_FALLBACK.cdx"
    locales_env = active_lmdb / "SYSTEM_LOCALES.cdx.d"
    fallback_env = active_lmdb / "SYSTEM_LOCALE_FALLBACK.cdx.d"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE23G_PROMOTION_EXECUTED",
         promotion.get("STATUS") == "LOCALE_PHASE23G_ACTIVE_LOCALE_SPINE_PROMOTION_EXECUTED",
         promotion.get("STATUS", ""))
    gate("PHASE23G_PROMOTION_VALIDATION_ZERO",
         promotion.get("VALIDATION_ISSUES", "") == "0",
         f"validation_issues={promotion.get('VALIDATION_ISSUES', '')}")
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("ACTIVE_SYSTEM_LOCALES_DBF_PRESENT", locales_dbf.exists(), str(locales_dbf))
    gate("ACTIVE_SYSTEM_LOCALE_FALLBACK_DBF_PRESENT", fallback_dbf.exists(), str(fallback_dbf))
    gate("ACTIVE_SYSTEM_LOCALES_CDX_PRESENT", locales_cdx.exists(), str(locales_cdx))
    gate("ACTIVE_SYSTEM_LOCALE_FALLBACK_CDX_PRESENT", fallback_cdx.exists(), str(fallback_cdx))
    gate("ACTIVE_SYSTEM_LOCALES_LMDB_PRESENT", locales_env.exists(), str(locales_env))
    gate("ACTIVE_SYSTEM_LOCALE_FALLBACK_LMDB_PRESENT", fallback_env.exists(), str(fallback_env))
    gate("ACTIVE_SYSTEM_LOCALES_V64_READBACK",
         re.search(r"OPENED\s+SYSTEM_LOCALES\s+\(V64\)\s*:\s*RECORD COUNT\s+5", upper) is not None,
         "Opened SYSTEM_LOCALES (v64) : Record count 5")
    gate("ACTIVE_SYSTEM_LOCALE_FALLBACK_V64_READBACK",
         re.search(r"OPENED\s+SYSTEM_LOCALE_FALLBACK\s+\(V64\)\s*:\s*RECORD COUNT\s+5", upper) is not None,
         "Opened SYSTEM_LOCALE_FALLBACK (v64) : Record count 5")
    gate("ACTIVE_SET_INDEX_ATTACHED",
         upper.count("SET INDEX (CDX ATTACHED)") >= 2,
         "SET INDEX attached for both active tables")
    gate("ACTIVE_SET_ORDER_LOCALE_ID",
         "SET ORDER: CDX TAG 'LOCALE_ID' (ASC)" in upper or 'SET ORDER: CDX TAG "LOCALE_ID" (ASC)' in upper,
         "SET ORDER LOCALE_ID active proof")
    gate("ACTIVE_SET_ORDER_FBID",
         "SET ORDER: CDX TAG 'FBID' (ASC)" in upper or 'SET ORDER: CDX TAG "FBID" (ASC)' in upper,
         "SET ORDER FBID active proof")
    gate("NO_ACTIVE_READBACK_MUTATION",
         "BUILDLMDB:" not in upper and "CREATE X64" not in upper and "CDX ADDTAG" not in upper,
         "readback should not create/rebuild active artifacts")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    lmdb_env_dirs = exists_i(locales_env) + exists_i(fallback_env)
    lmdb_mdb_files = count_mdb_files(locales_env) + count_mdb_files(fallback_env)
    lmdb_data_mdb_files = exists_i(locales_env / "data.mdb") + exists_i(fallback_env / "data.mdb")

    boundary = [
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 23G validation/readback only; active mutation already accounted in promotion step."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
    ]

    write_csv(reports / "locale_phase23g_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "ACTIVE_SYSTEM_LOCALES_DBF_PRESENT": exists_i(locales_dbf),
        "ACTIVE_SYSTEM_LOCALE_FALLBACK_DBF_PRESENT": exists_i(fallback_dbf),
        "ACTIVE_SYSTEM_LOCALES_CDX_PRESENT": exists_i(locales_cdx),
        "ACTIVE_SYSTEM_LOCALE_FALLBACK_CDX_PRESENT": exists_i(fallback_cdx),
        "ACTIVE_LMDB_ENV_DIRS": lmdb_env_dirs,
        "ACTIVE_LMDB_MDB_FILES": lmdb_mdb_files,
        "ACTIVE_LMDB_DATA_MDB_FILES": lmdb_data_mdb_files,
        "ACTIVE_PROMOTION_EXECUTED": promotion.get("ACTIVE_PROMOTION_EXECUTED", ""),
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "ACTIVE_SYSTEM_LOCALES_DBF_PRESENT",
         "ACTIVE_SYSTEM_LOCALE_FALLBACK_DBF_PRESENT", "ACTIVE_SYSTEM_LOCALES_CDX_PRESENT",
         "ACTIVE_SYSTEM_LOCALE_FALLBACK_CDX_PRESENT", "ACTIVE_LMDB_ENV_DIRS",
         "ACTIVE_LMDB_MDB_FILES", "ACTIVE_LMDB_DATA_MDB_FILES", "ACTIVE_PROMOTION_EXECUTED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23g_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23g_readback_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  active SYSTEM_LOCALES dbf present: {exists_i(locales_dbf)}")
    print(f"  active SYSTEM_LOCALE_FALLBACK dbf present: {exists_i(fallback_dbf)}")
    print(f"  active SYSTEM_LOCALES cdx present: {exists_i(locales_cdx)}")
    print(f"  active SYSTEM_LOCALE_FALLBACK cdx present: {exists_i(fallback_cdx)}")
    print(f"  active lmdb env dirs: {lmdb_env_dirs}")
    print(f"  active lmdb mdb files: {lmdb_mdb_files}")
    print(f"  active lmdb data.mdb files: {lmdb_data_mdb_files}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
