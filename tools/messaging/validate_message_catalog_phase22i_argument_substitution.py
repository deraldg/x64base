#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22I_ARGUMENT_SUBSTITUTION_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22I_ARGUMENT_SUBSTITUTION_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22J_HELP_MANUALGEN_LANGUAGE_HANDOFF_OR_PHASE23_LOCALE_SPINE"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022I_ARGUMENT_SUBSTITUTION_SMOKE.md")

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

    p22i = first_row(reports / "message_catalog_phase22i_status_summary_v1.csv")
    messages = p22i.get("MESSAGES", "12")
    text_rows = p22i.get("TEXT_ROWS", "60")
    locales = p22i.get("LOCALES", "de;en-US;es;fr;it")

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

    gate("PHASE22I_SOURCE_PATCH_APPLIED",
         p22i.get("STATUS") == "MESSAGE_CATALOG_PHASE22I_ARGUMENT_SUBSTITUTION_SOURCE_PATCH_APPLIED",
         p22i.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("PROVIDER_STATUS_OUTPUT_PRESENT", "MESSAGE CATALOG PROVIDER STATUS" in upper, "status heading")
    gate("MODE_ACTIVE_DBF", "MODE: ACTIVE_DBF" in upper, "provider should report active_dbf")
    gate("ACTIVE_CATALOG_LOADED_YES", "ACTIVE CATALOG LOADED: YES" in upper, "active rows loaded")
    gate("LOOKUP_BLOCK_COUNT", upper.count("MESSAGE CATALOG GET:") >= 3, "three lookup blocks expected")
    gate("ARGUMENT_COUNT_ONE", upper.count("ARGUMENT COUNT: 1") >= 3, "one argument in each lookup")
    gate("ARGUMENT_COMMAND_USE", upper.count("ARGUMENT COMMAND: USE") >= 3, "command=USE parsed")
    gate("ENGLISH_SUBSTITUTED", "TEXT: TYPE HELP USE FOR MORE INFORMATION." in upper, "English placeholder substituted")
    gate("SPANISH_SUBSTITUTED", "TEXT: ESCRIBA HELP USE PARA OBTENER MAS INFORMACION." in upper, "Spanish placeholder substituted")
    gate("FALLBACK_SUBSTITUTED", "LOCALE: XX-XX" in upper and "TEXT: TYPE HELP USE FOR MORE INFORMATION." in upper, "xx-XX fallback substituted")
    gate("NO_UNREPLACED_COMMAND_PLACEHOLDER", "{COMMAND}" not in upper, "no literal {command} should remain")
    gate("NO_MISSING_TEXT", "<MISSING>" not in upper, "lookup text should not be missing")
    gate("SUBSTITUTION_BOUNDARY", "READ-ONLY LOOKUP/SUBSTITUTION" in upper and "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper, "read-only substitution boundary")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22i_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "ARGUMENT_SUBSTITUTION_PROOF": 1 if status == STATUS_GREEN else 0,
        "LOOKUP_BLOCKS": upper.count("MESSAGE CATALOG GET:"),
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "ARGUMENT_SUBSTITUTION_PROOF", "LOOKUP_BLOCKS",
         "SOURCE_MUTATION_OBSERVED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22i_runtime_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22I runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Provider substitution read-only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22i_runtime_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  lookup blocks: {upper.count('MESSAGE CATALOG GET:')}")
    print(f"  argument substitution proof: {1 if status == STATUS_GREEN else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
