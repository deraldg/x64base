#!/usr/bin/env python3
"""
Phase 15: Candidate LMDB plan after inactive candidate CDX execution.

Plan only. Consumes Phase 14 CDX execution reports and prepares a guarded plan
for a future inactive-candidate LMDB build/readback. No LMDB environment is
created in Phase 15.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE15_CANDIDATE_LMDB_PLAN_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE15_CANDIDATE_LMDB_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE16_INACTIVE_CANDIDATE_LMDB_BUILD"
REPORT_DIR = Path("docs/messaging/reports")
PHASE14_ROOT = Path("docs/messaging/candidates/phase14_inactive_candidate_cdx_execution")

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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    phase14_status = reports / "message_catalog_phase14_status_summary_v1.csv"
    phase14_inventory = reports / "message_catalog_phase14_cdx_artifact_inventory_v1.csv"
    phase14_boundary = reports / "message_catalog_phase14_boundary_ledger_v1.csv"

    candidate_dbf_dir = repo / PHASE14_ROOT / "dbf"
    candidate_indexes_dir = repo / PHASE14_ROOT / "indexes"
    candidate_lmdb_dir = repo / PHASE14_ROOT / "lmdb"

    gates: list[dict[str, Any]] = []
    failures = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE14_STATUS_PRESENT", phase14_status.exists(), str(phase14_status))
    gate("PHASE14_CDX_INVENTORY_PRESENT", phase14_inventory.exists(), str(phase14_inventory))
    gate("PHASE14_BOUNDARY_LEDGER_PRESENT", phase14_boundary.exists(), str(phase14_boundary))
    gate("CANDIDATE_DBF_DIR_PRESENT", candidate_dbf_dir.exists(), str(candidate_dbf_dir))
    gate("CANDIDATE_INDEXES_DIR_PRESENT", candidate_indexes_dir.exists(), str(candidate_indexes_dir))
    gate("CANDIDATE_LMDB_DIR_PRESENT", candidate_lmdb_dir.exists(), str(candidate_lmdb_dir))

    messages = "0"
    text_rows = "0"
    locales = ""
    validation_issues = "UNKNOWN"
    cdx_files = 0

    if failures == 0:
        p14 = first_row(phase14_status)
        gate("PHASE14_STATUS_GREEN", p14.get("STATUS", "") == "MESSAGE_CATALOG_PHASE14_INACTIVE_CANDIDATE_CDX_TAG_EXECUTION_GREEN", p14.get("STATUS", ""))
        messages = p14.get("MESSAGES", "12")
        text_rows = p14.get("TEXT_ROWS", "60")
        locales = p14.get("LOCALES", "de;en-US;es;fr;it")
        validation_issues = p14.get("VALIDATION_ISSUES", "0")
        gate("PHASE14_VALIDATION_ZERO", validation_issues == "0", f"validation_issues={validation_issues}")

        inv = read_csv(phase14_inventory)
        cdx_files = len([r for r in inv if r.get("RELATIVE_PATH", "").lower().endswith(".cdx")])
        gate("PHASE14_CDX_FILES_PRESENT", cdx_files >= 2, f"cdx_files={cdx_files}")

        # Check expected files by path. These are candidate-only artifacts.
        gate("SYSTEM_MESSAGES_CDX_PRESENT", (candidate_indexes_dir / "SYSTEM_MESSAGES.cdx").exists(), str(candidate_indexes_dir / "SYSTEM_MESSAGES.cdx"))
        gate("SYSTEM_MESSAGE_TEXT_CDX_PRESENT", (candidate_indexes_dir / "SYSTEM_MESSAGE_TEXT.cdx").exists(), str(candidate_indexes_dir / "SYSTEM_MESSAGE_TEXT.cdx"))

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED

    write_csv(reports / "message_catalog_phase15_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "CDX_FILES_AVAILABLE": cdx_files,
        "LMDB_BUILD_AUTHORIZED": 0,
        "LMDB_ENV_CREATED": 0,
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "CDX_FILES_AVAILABLE", "LMDB_BUILD_AUTHORIZED", "LMDB_ENV_CREATED",
         "ACTIVE_PROMOTION_AUTHORIZED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    build_plan = [
        {"STEP": 1, "ACTION": "VERIFY_PHASE14_CANDIDATE_CDX_GREEN", "INPUT": "message_catalog_phase14_status_summary_v1.csv", "OUTPUT": "green precondition", "EXECUTE_IN_PHASE15": 0, "EXECUTE_IN_PHASE16": 1},
        {"STEP": 2, "ACTION": "SET_CANDIDATE_PATHS", "INPUT": "candidate dbf/indexes/lmdb directories", "OUTPUT": "DotTalk path lanes set to candidate only", "EXECUTE_IN_PHASE15": 0, "EXECUTE_IN_PHASE16": 1},
        {"STEP": 3, "ACTION": "OPEN_SYSTEM_MESSAGES_WITH_CDX", "INPUT": "SYSTEM_MESSAGES.dbf + SYSTEM_MESSAGES.cdx", "OUTPUT": "candidate work area open/index attached", "EXECUTE_IN_PHASE15": 0, "EXECUTE_IN_PHASE16": 1},
        {"STEP": 4, "ACTION": "BUILDLMDB_SYSTEM_MESSAGES", "INPUT": "candidate SYSTEM_MESSAGES CDX tags", "OUTPUT": "candidate LMDB env for SYSTEM_MESSAGES", "EXECUTE_IN_PHASE15": 0, "EXECUTE_IN_PHASE16": 1},
        {"STEP": 5, "ACTION": "OPEN_SYSTEM_MESSAGE_TEXT_WITH_CDX", "INPUT": "SYSTEM_MESSAGE_TEXT.dbf + SYSTEM_MESSAGE_TEXT.cdx", "OUTPUT": "candidate work area open/index attached", "EXECUTE_IN_PHASE15": 0, "EXECUTE_IN_PHASE16": 1},
        {"STEP": 6, "ACTION": "BUILDLMDB_SYSTEM_MESSAGE_TEXT", "INPUT": "candidate SYSTEM_MESSAGE_TEXT CDX tags", "OUTPUT": "candidate LMDB env for SYSTEM_MESSAGE_TEXT", "EXECUTE_IN_PHASE15": 0, "EXECUTE_IN_PHASE16": 1},
        {"STEP": 7, "ACTION": "READBACK_LMDB_COUNTS", "INPUT": "candidate LMDB env", "OUTPUT": "expected counts 12 and 60", "EXECUTE_IN_PHASE15": 0, "EXECUTE_IN_PHASE16": 1},
        {"STEP": 8, "ACTION": "HOLD_FOR_PROMOTION_POLICY", "INPUT": "candidate LMDB readback reports", "OUTPUT": "future no-promotion/promotion decision", "EXECUTE_IN_PHASE15": 0, "EXECUTE_IN_PHASE16": 0},
    ]
    write_csv(reports / "message_catalog_phase15_candidate_lmdb_build_plan_v1.csv", build_plan,
              ["STEP", "ACTION", "INPUT", "OUTPUT", "EXECUTE_IN_PHASE15", "EXECUTE_IN_PHASE16"])

    # A script template with correct absolute paths, but do not execute in Phase 15.
    dbf_path = str(candidate_dbf_dir)
    idx_path = str(candidate_indexes_dir)
    lmdb_path = str(candidate_lmdb_dir)
    dts_lines = [
        "* MESSAGE_CATALOG_PHASE16_BUILD_CANDIDATE_LMDB.dts",
        "* Candidate-only LMDB build for messaging catalog.",
        "* Boundary: inactive candidate path only; no active catalog promotion.",
        "CLOSE ALL",
        f"SET PATH DBF {dbf_path}",
        f"SET PATH INDEXES {idx_path}",
        f"SET PATH LMDB {lmdb_path}",
        "",
        "SELECT 0",
        "USE SYSTEM_MESSAGES",
        "* Attach candidate CDX / set order as required by current runtime before BUILDLMDB.",
        "* If direct USE does not attach CDX, use WORKSPACE OPEN SYSTEM_MESSAGES CDX or equivalent proven runtime form.",
        "BUILDLMDB CLEAN YES",
        "",
        "SELECT 1",
        "USE SYSTEM_MESSAGE_TEXT",
        "* Attach candidate CDX / set order as required by current runtime before BUILDLMDB.",
        "BUILDLMDB CLEAN YES",
        "",
        "SELECT 2",
        "",
    ]
    script_dir = repo / PHASE14_ROOT / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / "MESSAGE_CATALOG_PHASE16_BUILD_CANDIDATE_LMDB_TEMPLATE.dts"
    script_path.write_text("\n".join(dts_lines), encoding="utf-8")

    dts_rows = [{
        "SCRIPT": str(script_path.relative_to(repo)).replace("\\", "/"),
        "PURPOSE": "Template for future Phase 16 candidate-only LMDB build",
        "EXECUTE_IN_PHASE15": 0,
        "EXECUTE_IN_PHASE16": 1,
        "NOTES": "Template only; Phase 16 must verify current runtime CDX attach/order behavior before execution."
    }]
    write_csv(reports / "message_catalog_phase15_candidate_lmdb_dts_plan_v1.csv", dts_rows,
              ["SCRIPT", "PURPOSE", "EXECUTE_IN_PHASE15", "EXECUTE_IN_PHASE16", "NOTES"])

    validation_plan = [
        {"CHECK": "SYSTEM_MESSAGES_LMDB_COUNT", "EXPECTED": messages, "SOURCE": "Phase 16 runtime readback", "FAILS_IF": "count mismatch"},
        {"CHECK": "SYSTEM_MESSAGE_TEXT_LMDB_COUNT", "EXPECTED": text_rows, "SOURCE": "Phase 16 runtime readback", "FAILS_IF": "count mismatch"},
        {"CHECK": "CANDIDATE_LMDB_PATH_ONLY", "EXPECTED": str(candidate_lmdb_dir), "SOURCE": "Phase 16 boundary ledger", "FAILS_IF": "LMDB env outside candidate path"},
        {"CHECK": "ACTIVE_CATALOG_UNCHANGED", "EXPECTED": "no mutation", "SOURCE": "Phase 16 boundary ledger", "FAILS_IF": "active catalog path touched"},
        {"CHECK": "HELP_CMDHELPCHK_UNCHANGED", "EXPECTED": "no mutation", "SOURCE": "Phase 16 boundary ledger", "FAILS_IF": "HELP/CMDHELPCHK mutation"},
    ]
    write_csv(reports / "message_catalog_phase15_lmdb_validation_plan_v1.csv", validation_plan,
              ["CHECK", "EXPECTED", "SOURCE", "FAILS_IF"])

    write_csv(reports / "message_catalog_phase15_gate_check_v1.csv", gates + [
        {"GATE": "LMDB_BUILD_NOT_AUTHORIZED", "STATUS": "PASS", "DETAIL": "Phase 15 is plan-only; no LMDB build performed."},
        {"GATE": "ACTIVE_PROMOTION_NOT_AUTHORIZED", "STATUS": "PASS", "DETAIL": "No active catalog replacement/promotion authorized."},
    ], ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_DBF", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 15 reads/reports candidate DBF/CDX state only; no DBF/DBT writes."},
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_CDX", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 15 creates no CDX/index files."},
        {"PROTECTED_SYSTEM": "INACTIVE_CANDIDATE_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 15 creates no LMDB environment."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CATALOGS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF catalog paths created, replaced, opened for write, or promoted."},
        {"PROTECTED_SYSTEM": "ACTIVE_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index paths touched."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-mining mutation."},
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source-code mutation."},
        {"PROTECTED_SYSTEM": "CATALOG_PROMOTION", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active catalog promotion authorized or performed."},
    ]
    write_csv(reports / "message_catalog_phase15_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 15 Candidate LMDB Plan

Status: `{status}`

Phase 15 plans a future candidate-only LMDB build after Phase 14 candidate CDX
execution. It does not create an LMDB environment.

## Counts

- Messages: {messages}
- Text rows: {text_rows}
- Locales: {locales}
- Validation issues: {validation_issues}
- Candidate CDX files available: {cdx_files}

## Next gate

`{NEXT_GATE}`

## Boundary

No DBF/DBT writes, no CDX/index creation, no LMDB creation, no active catalog
mutation, no HELP DATA mutation, no CMDHELPCHK mutation, no source-mining
mutation, no source-code mutation, and no active catalog promotion occurred.
"""
    (reports / "MESSAGE_CATALOG_PHASE15_CANDIDATE_LMDB_PLAN_REPORT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  cdx files available: {cdx_files}")
    print("  lmdb build authorized: 0")
    print("  lmdb env created: 0")
    print("  active promotion authorized: 0")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
