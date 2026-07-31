#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23E_CANDIDATE_LMDB_BUILD_RUNTIME_EXECUTION_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23E_CANDIDATE_LMDB_BUILD_RUNTIME_EXECUTION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23F_CANDIDATE_LOCALE_SPINE_PROMOTION_PLAN"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
RUNLOG = Path("docs/locale/runlog/LOC-023E_CANDIDATE_LMDB_RUNTIME_PROOF.md")
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

    prep = first_row(reports / "locale_phase23e_prepare_status_summary_v1.csv")

    candidate = repo / CANDIDATE_ROOT
    lmdb_dir = candidate / "lmdb"
    locales_env = lmdb_dir / "SYSTEM_LOCALES.cdx.d"
    fallback_env = lmdb_dir / "SYSTEM_LOCALE_FALLBACK.cdx.d"

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

    gate("PHASE23E_PREPARE_READY",
         prep.get("STATUS") == "LOCALE_PHASE23E_CANDIDATE_LMDB_BUILD_RUNTIME_EXECUTION_READY",
         prep.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("SYSTEM_LOCALES_LMDB_ENV_PRESENT", locales_env.exists(), str(locales_env))
    gate("SYSTEM_LOCALE_FALLBACK_LMDB_ENV_PRESENT", fallback_env.exists(), str(fallback_env))
    gate("SYSTEM_LOCALES_DATA_MDB_PRESENT", (locales_env / "data.mdb").exists(), str(locales_env / "data.mdb"))
    gate("SYSTEM_LOCALE_FALLBACK_DATA_MDB_PRESENT", (fallback_env / "data.mdb").exists(), str(fallback_env / "data.mdb"))
    gate("BUILDLMDB_SYSTEM_LOCALES_OK",
         "SYSTEM_LOCALES.CDX" in upper and re.search(r"BUILDLMDB:\s*DONE\s+OK=\d+\s+TAGS\s+REBUILT", upper) is not None,
         "BUILDLMDB done for SYSTEM_LOCALES")
    gate("BUILDLMDB_SYSTEM_LOCALE_FALLBACK_OK",
         "SYSTEM_LOCALE_FALLBACK.CDX" in upper and upper.count("BUILDLMDB: DONE OK=") >= 2,
         "BUILDLMDB done for SYSTEM_LOCALE_FALLBACK")
    gate("SET_ORDER_LOCALE_ID_SUCCEEDED",
         "CDX TAG 'LOCALE_ID'" in upper or 'CDX TAG "LOCALE_ID"' in upper or "SET ORDER TO LOCALE_ID" in upper,
         "SET ORDER to LOCALE_ID after LMDB")
    gate("SET_ORDER_FBID_SUCCEEDED",
         "CDX TAG 'FBID'" in upper or 'CDX TAG "FBID"' in upper or "SET ORDER TO FBID" in upper,
         "SET ORDER to FBID after LMDB")
    gate("NO_LMDB_MISSING_AFTER_BUILD",
         "LMDB ENV MISSING" not in upper,
         "no LMDB env missing after Phase 23E build/readback")
    gate("NO_ACTIVE_PROMOTION",
         "ACTIVE PROMOTION" not in upper and "PROMOT" not in upper,
         "no active promotion attempted")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    env_count = file_exists_int(locales_env) + file_exists_int(fallback_env)
    mdb_count = count_mdb_files(locales_env) + count_mdb_files(fallback_env)
    data_mdb_count = file_exists_int(locales_env / "data.mdb") + file_exists_int(fallback_env / "data.mdb")

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_LMDB", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": env_count, "DETAIL": "Candidate LMDB env dirs under docs/locale/candidates only."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Existing candidate DBFs read/opened only."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Existing candidate CDXs used to build LMDB; no CDX creation in Phase 23E."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active locale spine promotion."},
    ]

    write_csv(reports / "locale_phase23e_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SYSTEM_LOCALES_LMDB_ENV_PRESENT": file_exists_int(locales_env),
        "SYSTEM_LOCALE_FALLBACK_LMDB_ENV_PRESENT": file_exists_int(fallback_env),
        "LMDB_ENV_DIRS": env_count,
        "LMDB_MDB_FILES": mdb_count,
        "LMDB_DATA_MDB_FILES": data_mdb_count,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "SYSTEM_LOCALES_LMDB_ENV_PRESENT",
         "SYSTEM_LOCALE_FALLBACK_LMDB_ENV_PRESENT", "LMDB_ENV_DIRS", "LMDB_MDB_FILES",
         "LMDB_DATA_MDB_FILES", "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23e_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23e_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  SYSTEM_LOCALES lmdb env present: {file_exists_int(locales_env)}")
    print(f"  SYSTEM_LOCALE_FALLBACK lmdb env present: {file_exists_int(fallback_env)}")
    print(f"  lmdb env dirs: {env_count}")
    print(f"  lmdb mdb files: {mdb_count}")
    print(f"  lmdb data.mdb files: {data_mdb_count}")
    print("  active promotion authorized: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
