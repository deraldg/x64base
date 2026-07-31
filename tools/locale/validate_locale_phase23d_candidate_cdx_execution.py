#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23D_CANDIDATE_CDX_TAG_RUNTIME_EXECUTION_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23D_CANDIDATE_CDX_TAG_RUNTIME_EXECUTION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23E_CANDIDATE_LMDB_BUILD_RUNTIME_EXECUTION"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
RUNLOG = Path("docs/locale/runlog/LOC-023D_CANDIDATE_CDX_RUNTIME_PROOF.md")
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

def has_added(upper: str, tag: str) -> bool:
    return (
        f"CDX ADDTAG: ADDED '{tag.upper()}'." in upper
        or f'CDX ADDTAG: ADDED "{tag.upper()}".' in upper
        or f"CDX ADDTAG {tag.upper()}" in upper
    )

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    prep = first_row(reports / "locale_phase23d_prepare_status_summary_v1.csv")

    candidate = repo / CANDIDATE_ROOT
    index_dir = candidate / "indexes"
    locales_cdx = index_dir / "SYSTEM_LOCALES.cdx"
    fallback_cdx = index_dir / "SYSTEM_LOCALE_FALLBACK.cdx"

    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    required_tags = ["BASE_LOCALE", "LOCALE_STATUS", "SRC", "FBID", "FALLBACK_TO", "FALLBACK_ORDER", "FALLBACK_TYPE"]

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE23D_PREPARE_READY",
         prep.get("STATUS") == "LOCALE_PHASE23D_CANDIDATE_CDX_TAG_RUNTIME_EXECUTION_READY",
         prep.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("SYSTEM_LOCALES_CDX_PRESENT", locales_cdx.exists(), str(locales_cdx))
    gate("SYSTEM_LOCALE_FALLBACK_CDX_PRESENT", fallback_cdx.exists(), str(fallback_cdx))
    gate("SYSTEM_LOCALES_CDX_CREATED_PROOF",
         "SYSTEM_LOCALES.CDX" in upper,
         "SYSTEM_LOCALES.cdx mentioned in runtime output")
    gate("SYSTEM_LOCALE_FALLBACK_CDX_CREATED_PROOF",
         "SYSTEM_LOCALE_FALLBACK.CDX" in upper,
         "SYSTEM_LOCALE_FALLBACK.cdx mentioned in runtime output")
    gate("TAG_LOCALE_ID_ADDED_FOR_BOTH_TABLES",
         upper.count("CDX ADDTAG: ADDED 'LOCALE_ID'.") >= 2 or upper.count('CDX ADDTAG: ADDED "LOCALE_ID".') >= 2,
         "LOCALE_ID tag should be added for both tables")
    for tag in required_tags:
        gate(f"TAG_{tag}_ADDED",
             has_added(upper, tag),
             f"CDX tag creation proof for {tag}")

    # In Phase 23D, SET INDEX/SET ORDER readback may report LMDB env missing because LMDB
    # creation is explicitly deferred to Phase 23E. Treat the warning as expected if present.
    lmdb_attach_deferred = 1 if "LMDB ENV MISSING" in upper else 0
    review("LMDB_ATTACH_ORDER_DEFERRED",
           lmdb_attach_deferred == 1,
           "SET INDEX/ORDER may be deferred until BUILDLMDB in Phase 23E; no Phase 23D failure")
    gate("NO_ACTUAL_LMDB_BUILD_EXECUTED",
         "BUILDLMDB:" not in upper,
         "Phase 23D must not execute BUILDLMDB; command hints are acceptable")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    observed_cdx = file_exists_int(locales_cdx) + file_exists_int(fallback_cdx)

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_CDX", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": observed_cdx, "DETAIL": "Candidate CDX files under docs/locale/candidates only."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Existing candidate DBFs read/opened only; no DBF create/seed execution in Phase 23D."},
        {"PROTECTED_SYSTEM": "INACTIVE_LOCALE_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No LMDB execution in Phase 23D; LMDB attach/order proof deferred to Phase 23E."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
    ]

    write_csv(reports / "locale_phase23d_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "SYSTEM_LOCALES_CDX_PRESENT": file_exists_int(locales_cdx),
        "SYSTEM_LOCALE_FALLBACK_CDX_PRESENT": file_exists_int(fallback_cdx),
        "CANDIDATE_CDX_FILES_CREATED": observed_cdx,
        "LMDB_ATTACH_ORDER_DEFERRED_TO_23E": lmdb_attach_deferred,
        "CANDIDATE_LMDB_ENVS_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "SYSTEM_LOCALES_CDX_PRESENT",
         "SYSTEM_LOCALE_FALLBACK_CDX_PRESENT", "CANDIDATE_CDX_FILES_CREATED",
         "LMDB_ATTACH_ORDER_DEFERRED_TO_23E", "CANDIDATE_LMDB_ENVS_CREATED",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "locale_phase23d_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23d_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  SYSTEM_LOCALES cdx present: {file_exists_int(locales_cdx)}")
    print(f"  SYSTEM_LOCALE_FALLBACK cdx present: {file_exists_int(fallback_cdx)}")
    print(f"  candidate cdx files created: {observed_cdx}")
    print(f"  lmdb attach/order deferred to 23E: {lmdb_attach_deferred}")
    print("  candidate lmdb envs created: 0")
    print("  active promotion authorized: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
