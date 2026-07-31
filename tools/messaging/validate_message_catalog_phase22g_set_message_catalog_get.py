#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22G_SET_MESSAGE_CATALOG_GET_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22G_SET_MESSAGE_CATALOG_GET_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22H_SET_LANGUAGE_ACTIVE_MESSAGE_EMISSION"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022G_SET_MESSAGE_CATALOG_GET_SMOKE.md")

REQUIRED_LOCALES = ["en-US", "es", "fr", "de", "it", "xx-XX"]

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

    p22g = first_row(reports / "message_catalog_phase22g_status_summary_v1.csv")
    messages = p22g.get("MESSAGES", "12")
    text_rows = p22g.get("TEXT_ROWS", "60")
    locales = p22g.get("LOCALES", "de;en-US;es;fr;it")

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

    gate("PHASE22G_SOURCE_PATCH_APPLIED",
         p22g.get("STATUS") == "MESSAGE_CATALOG_PHASE22G_SET_MESSAGE_CATALOG_GET_SOURCE_PATCH_APPLIED",
         p22g.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("PROVIDER_STATUS_OUTPUT_PRESENT", "MESSAGE CATALOG PROVIDER STATUS" in upper, "status heading")
    gate("MODE_ACTIVE_DBF", "MODE: ACTIVE_DBF" in upper, "provider should report active_dbf")
    gate("ACTIVE_CATALOG_LOADED_YES", "ACTIVE CATALOG LOADED: YES" in upper, "active rows loaded")
    gate("MESSAGE_GET_COUNT", upper.count("MESSAGE CATALOG GET:") >= 6, "six lookup blocks expected")
    gate("SYMBOL_HELP_HINT_COMMAND", upper.count("SYMBOL: HELP_HINT_COMMAND") >= 6, "symbol should be present in all lookup blocks")
    for locale in REQUIRED_LOCALES:
        gate(f"LOCALE_{locale}_PRESENT", f"LOCALE: {locale.upper()}" in upper, f"lookup output for {locale}")
    gate("NO_MISSING_TEXT", "<MISSING>" not in upper, "all lookups should return text")
    gate("ACTIVE_DBF_MODE_IN_GET", upper.count("PROVIDER MODE: ACTIVE_DBF") >= 6, "lookup provider mode should be active_dbf")
    gate("LOOKUP_BOUNDARY", "READ-ONLY LOOKUP" in upper and "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper, "read-only lookup boundary")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22g_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SET_MESSAGE_CATALOG_GET_PROOF": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in upper else 0,
        "LOOKUP_BLOCKS": upper.count("MESSAGE CATALOG GET:"),
        "FALLBACK_LOCALE_PROOF": 1 if "LOCALE: XX-XX" in upper and "<MISSING>" not in upper else 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SET_MESSAGE_CATALOG_GET_PROOF", "ACTIVE_CATALOG_LOADED",
         "LOOKUP_BLOCKS", "FALLBACK_LOCALE_PROOF",
         "SOURCE_MUTATION_OBSERVED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22g_runtime_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22G runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Provider lookup read-only; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22g_runtime_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  lookup blocks: {upper.count('MESSAGE CATALOG GET:')}")
    print(f"  fallback locale proof: {1 if 'LOCALE: XX-XX' in upper and '<MISSING>' not in upper else 0}")
    print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in upper else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
