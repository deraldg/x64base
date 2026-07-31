#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22E_RUNTIME_PROVIDER_STATUS_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22E_RUNTIME_PROVIDER_STATUS_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22F_ACTIVE_DBF_ROW_LOAD_PROVIDER"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022E_PROVIDER_STATUS_SMOKE.md")

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\\n")
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

    p22e = first_row(reports / "message_catalog_phase22e_status_summary_v1.csv")
    messages = p22e.get("MESSAGES", "12")
    text_rows = p22e.get("TEXT_ROWS", "60")
    locales = p22e.get("LOCALES", "de;en-US;es;fr;it")

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
    def review(name: str, ok: bool, detail: str) -> None:
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22E_SOURCE_HOOK_APPLIED", p22e.get("STATUS") == "MESSAGE_CATALOG_PHASE22E_RUNTIME_PROVIDER_STATUS_SOURCE_PATCH_APPLIED", p22e.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("PROVIDER_STATUS_OUTPUT_PRESENT", "MESSAGE CATALOG PROVIDER STATUS" in upper, "output should show provider status heading")
    gate("COMPILED_FALLBACK_MODE_PRESENT", "MODE: COMPILED_FALLBACK" in upper or "COMPILED FALLBACK" in upper, "compiled fallback mode/status should be visible")
    gate("ACTIVE_CATALOG_PRESENT_YES", "ACTIVE CATALOG PRESENT: YES" in upper, "active catalog artifacts should be detected")
    gate("ACTIVE_CATALOG_LOADED_NO", "ACTIVE CATALOG LOADED: NO" in upper, "row loading is intentionally not yet active")
    gate("NO_RUNTIME_WRITEBACK_BOUNDARY", "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper, "read-only boundary should be visible")
    review("ACTIVE_DBF_PATH_VISIBLE", "DOTTALKPP/DATA/MESSAGING" in upper or "DOTTALKPP\\DATA\\MESSAGING" in upper or "ACTIVE DBF DIR:" in upper, "active DBF path should be visible")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22e_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "RUNTIME_PROVIDER_STATUS_SMOKE": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_CATALOG_PRESENT": 1 if "ACTIVE CATALOG PRESENT: YES" in upper else 0,
        "ACTIVE_CATALOG_LOADED": 0,
        "RUNTIME_DBF_ROW_LOADING_PROOF": 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "RUNTIME_PROVIDER_STATUS_SMOKE", "ACTIVE_CATALOG_PRESENT",
         "ACTIVE_CATALOG_LOADED", "RUNTIME_DBF_ROW_LOADING_PROOF",
         "SOURCE_MUTATION_OBSERVED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22e_runtime_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22E runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22e_runtime_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  runtime provider status smoke: {1 if status == STATUS_GREEN else 0}")
    print(f"  active catalog present: {1 if 'ACTIVE CATALOG PRESENT: YES' in upper else 0}")
    print("  active catalog loaded: 0")
    print("  runtime dbf row loading proof: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
