#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "LOCALE_PHASE23L_MSGMGR_HOUSE_COMMAND_BUILD_SMOKE_GREEN"
STATUS_BLOCKED = "LOCALE_PHASE23L_MSGMGR_HOUSE_COMMAND_BUILD_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_MSGMGR_RUNTIME_STATUS_WIRING"
LOCALE_REPORT_DIR = Path("docs/locale/reports")
RUNLOG = Path("docs/locale/runlog/LOC-023L_MSGMGR_HOUSE_BUILD_AND_SMOKE_PROOF.md")

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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / LOCALE_REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    apply_row = first_row(reports / "locale_phase23l_msgmgr_apply_status_summary_v1.csv")
    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    cmd_file = repo / "src/cli/cmd_msgmgr.cpp"
    gates: list[dict[str, Any]] = []
    failures = 0
    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE23L_APPLY_STATUS_GREEN", apply_row.get("STATUS") == "LOCALE_PHASE23L_MSGMGR_HOUSE_COMMAND_SOURCE_PATCH_APPLIED_BUILD_HELD", apply_row.get("STATUS", ""))
    gate("CMD_MSGMGR_PRESENT", cmd_file.exists(), str(cmd_file))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("BUILD_SUCCESS_PROOF", "DOTTALKPP.VCXPROJ ->" in upper or "BUILT TARGET DOTTALKPP" in upper or "BUILD SUCCEEDED" in upper, "expected dottalkpp build success proof")
    gate("MSGMGR_STATUS_PROOF", "MSGMGR STATUS" in upper and "COMMAND HOUSE" in upper and "REGISTERED" in upper, "MSGMGR STATUS should report command house registered")
    gate("MSGMGR_CHECK_PROOF", upper.count("MSGMGR STATUS") >= 2 or "MSGMGR CHECK" in upper, "MSGMGR CHECK should route to same read-only status")
    gate("READ_ONLY_BOUNDARY_PROOF", "NO DBF/CDX/LMDB MUTATION" in upper or "NO DBF" in upper, "read-only boundary should be visible")
    gate("NO_UNKNOWN_COMMAND", "UNKNOWN COMMAND" not in upper and "UNRECOGNIZED" not in upper, "MSGMGR should be registered")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)
    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "23L validation only; source mutation already accounted by apply step."},
        {"PROTECTED_SYSTEM": "BUILD", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if status == STATUS_GREEN else 0, "DETAIL": "Build proof supplied by operator."},
        {"PROTECTED_SYSTEM": "RUNTIME_SMOKE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if status == STATUS_GREEN else 0, "DETAIL": "MSGMGR command-house smoke proof supplied by operator."},
        {"PROTECTED_SYSTEM": "ACTIVE_LOCALE_SPINE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active locale DBF/CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active Messaging catalog mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "locale_phase23l_msgmgr_status_summary_v1.csv", [{
        "STATUS": status, "VALIDATION_ISSUES": validation_issues, "CMD_MSGMGR_PRESENT": exists_i(cmd_file),
        "BUILD_PROOF": 1 if ("DOTTALKPP.VCXPROJ ->" in upper or "BUILT TARGET DOTTALKPP" in upper or "BUILD SUCCEEDED" in upper) else 0,
        "MSGMGR_STATUS_PROOF": 1 if ("MSGMGR STATUS" in upper and "COMMAND HOUSE" in upper and "REGISTERED" in upper) else 0,
        "MSGMGR_CHECK_PROOF": 1 if (upper.count("MSGMGR STATUS") >= 2 or "MSGMGR CHECK" in upper) else 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "CMD_MSGMGR_PRESENT", "BUILD_PROOF", "MSGMGR_STATUS_PROOF", "MSGMGR_CHECK_PROOF", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])
    write_csv(reports / "locale_phase23l_msgmgr_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "locale_phase23l_msgmgr_validation_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  cmd_msgmgr present: {exists_i(cmd_file)}")
    print(f"  build proof: {1 if ('DOTTALKPP.VCXPROJ ->' in upper or 'BUILT TARGET DOTTALKPP' in upper or 'BUILD SUCCEEDED' in upper) else 0}")
    print(f"  MSGMGR STATUS proof: {1 if ('MSGMGR STATUS' in upper and 'COMMAND HOUSE' in upper and 'REGISTERED' in upper) else 0}")
    print(f"  MSGMGR CHECK proof: {1 if (upper.count('MSGMGR STATUS') >= 2 or 'MSGMGR CHECK' in upper) else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
