#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_BUILD_SMOKE_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_BUILD_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_MESSAGE_CATALOG_SCHEMA_FIELD_RECONCILIATION"
REPORT_DIR = Path("docs/locale/reports")
RUNLOG = Path("docs/locale/runlog/LOC-023P_MSGMGR_SCHEMA_STATUS_BUILD_AND_SMOKE_PROOF.md")

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

    apply_row = first_row(reports / "locale_phase23p_msgmgr_schema_status_apply_summary_v1.csv")
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

    gate("PHASE23P_APPLY_STATUS_GREEN",
         apply_row.get("STATUS") == "LOCALE_PHASE23P_MSGMGR_SCHEMA_STATUS_SOURCE_PATCH_APPLIED_BUILD_HELD",
         apply_row.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("BUILD_SUCCESS_PROOF",
         "DOTTALKPP.VCXPROJ ->" in upper or "BUILT TARGET DOTTALKPP" in upper or "BUILD SUCCEEDED" in upper,
         "expected dottalkpp build success proof")
    gate("MSGMGR_STATUS_PROOF",
         "MSGMGR STATUS" in upper and "COMMAND HOUSE" in upper and "REGISTERED" in upper,
         "MSGMGR STATUS should still report command house registered")
    gate("SCHEMA_ROOT_PROOF",
         "SCHEMA ROOT" in upper and "DOTTALKPP/DATA/SCHEMAS" in upper,
         "MSGMGR STATUS should report schema root")
    gate("LOCALE_SCHEMA_PATH_PROOF",
         "LOCALE SCHEMA" in upper and "DOTTALKPP/DATA/SCHEMAS/LOCALE/LOCALE_SPINE.DTSCHEMA" in upper,
         "MSGMGR STATUS should report active locale schema path")
    gate("MESSAGING_SCHEMA_HELD_PROOF",
         "MESSAGING SCHEMA" in upper and "HELD" in upper and "FIELD/TAG RECONCILIATION" in upper,
         "MSGMGR STATUS should report Messaging schema held")
    gate("READ_ONLY_BOUNDARY_PROOF",
         "NO DBF/CDX/LMDB MUTATION" in upper or "NO DBF" in upper,
         "read-only boundary should be visible")
    gate("NO_UNKNOWN_COMMAND",
         "UNKNOWN COMMAND" not in upper and "UNRECOGNIZED" not in upper,
         "MSGMGR should remain registered")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Validation only; source mutation already accounted by apply step."},
        {"PROTECTED_SYSTEM": "BUILD_RUNTIME", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if status == STATUS_GREEN else 0, "DETAIL": "Build/runtime smoke proof supplied by operator."},
        {"PROTECTED_SYSTEM": "ACTIVE_SCHEMA_CONTRACTS", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active schema mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_DBF_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    write_csv(reports / "locale_phase23p_msgmgr_schema_status_validation_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "BUILD_PROOF": 1 if ("DOTTALKPP.VCXPROJ ->" in upper or "BUILT TARGET DOTTALKPP" in upper or "BUILD SUCCEEDED" in upper) else 0,
        "MSGMGR_STATUS_PROOF": 1 if ("MSGMGR STATUS" in upper and "COMMAND HOUSE" in upper and "REGISTERED" in upper) else 0,
        "SCHEMA_ROOT_PROOF": 1 if ("SCHEMA ROOT" in upper and "DOTTALKPP/DATA/SCHEMAS" in upper) else 0,
        "LOCALE_SCHEMA_PATH_PROOF": 1 if ("LOCALE SCHEMA" in upper and "DOTTALKPP/DATA/SCHEMAS/LOCALE/LOCALE_SPINE.DTSCHEMA" in upper) else 0,
        "MESSAGING_SCHEMA_HELD_PROOF": 1 if ("MESSAGING SCHEMA" in upper and "HELD" in upper and "FIELD/TAG RECONCILIATION" in upper) else 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "BUILD_PROOF", "MSGMGR_STATUS_PROOF",
         "SCHEMA_ROOT_PROOF", "LOCALE_SCHEMA_PATH_PROOF", "MESSAGING_SCHEMA_HELD_PROOF",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])
    write_csv(reports / "locale_phase23p_msgmgr_schema_status_validation_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23p_msgmgr_schema_status_validation_boundary_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  build proof: {1 if ('DOTTALKPP.VCXPROJ ->' in upper or 'BUILT TARGET DOTTALKPP' in upper or 'BUILD SUCCEEDED' in upper) else 0}")
    print(f"  MSGMGR STATUS proof: {1 if ('MSGMGR STATUS' in upper and 'COMMAND HOUSE' in upper and 'REGISTERED' in upper) else 0}")
    print(f"  schema root proof: {1 if ('SCHEMA ROOT' in upper and 'DOTTALKPP/DATA/SCHEMAS' in upper) else 0}")
    print(f"  locale schema path proof: {1 if ('LOCALE SCHEMA' in upper and 'DOTTALKPP/DATA/SCHEMAS/LOCALE/LOCALE_SPINE.DTSCHEMA' in upper) else 0}")
    print(f"  messaging schema held proof: {1 if ('MESSAGING SCHEMA' in upper and 'HELD' in upper and 'FIELD/TAG RECONCILIATION' in upper) else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
