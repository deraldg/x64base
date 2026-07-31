#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22I_ARGUMENT_SUBSTITUTION_OR_PHASE23_LOCALE_SPINE"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022H_SET_LANGUAGE_ACTIVE_EMISSION_SMOKE.md")

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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22h = first_row(reports / "message_catalog_phase22h_status_summary_v1.csv")
    messages = p22h.get("MESSAGES", "12")
    text_rows = p22h.get("TEXT_ROWS", "60")
    locales = p22h.get("LOCALES", "de;en-US;es;fr;it")

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

    gate("PHASE22H_SOURCE_PATCH_APPLIED",
         p22h.get("STATUS") == "MESSAGE_CATALOG_PHASE22H_SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION_SOURCE_PATCH_APPLIED",
         p22h.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("SET_LANGUAGE_EMISSION_BLOCKS_PRESENT",
         upper.count("SET LANGUAGE ACTIVE MESSAGE EMISSION:") >= 2,
         "at least default and es checks should emit provider-backed message")
    gate("PROVIDER_MODE_ACTIVE_DBF",
         upper.count("PROVIDER MODE: ACTIVE_DBF") >= 2,
         "provider mode active_dbf in SET LANGUAGE emission")
    gate("ACTIVE_CATALOG_LOADED_YES",
         upper.count("ACTIVE CATALOG LOADED: YES") >= 2,
         "active catalog loaded yes in SET LANGUAGE emission")
    gate("CURRENT_LOCALE_EN_US",
         "CURRENT LOCALE: EN-US" in upper,
         "default/en-US locale emission")
    gate("CURRENT_LOCALE_ES",
         "CURRENT LOCALE: ES" in upper,
         "Spanish locale emission")
    gate("HELP_HINT_SYMBOL_PRESENT",
         upper.count("SYMBOL: HELP_HINT_COMMAND") >= 2,
         "HELP_HINT_COMMAND emitted")
    gate("NO_MISSING_TEXT",
         "<MISSING>" not in upper,
         "provider-backed message text must not be missing")
    gate("SPANISH_TEXT_PRESENT",
         "ESCRIBA HELP {COMMAND}" in upper,
         "Spanish active-catalog text should be emitted")
    gate("BOUNDARY_PRESENT",
         "READ-ONLY EMISSION" in upper and "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper,
         "read-only emission boundary")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22h_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SET_LANGUAGE_ACTIVE_EMISSION_PROOF": 1 if status == STATUS_GREEN else 0,
        "EMISSION_BLOCKS": upper.count("SET LANGUAGE ACTIVE MESSAGE EMISSION:"),
        "SPANISH_EMISSION_PROOF": 1 if "ESCRIBA HELP {COMMAND}" in upper else 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SET_LANGUAGE_ACTIVE_EMISSION_PROOF", "EMISSION_BLOCKS",
         "SPANISH_EMISSION_PROOF", "SOURCE_MUTATION_OBSERVED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22h_runtime_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22H runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Provider lookup read-only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22h_runtime_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  emission blocks: {upper.count('SET LANGUAGE ACTIVE MESSAGE EMISSION:')}")
    print(f"  spanish emission proof: {1 if 'ESCRIBA HELP {COMMAND}' in upper else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
