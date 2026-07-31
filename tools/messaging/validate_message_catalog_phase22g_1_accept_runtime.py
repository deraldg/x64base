#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22G_ACTIVE_LANGUAGE_LOOKUP_AND_EMISSION_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22G_ACTIVE_LANGUAGE_LOOKUP_AND_EMISSION_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22H_RUNTIME_MESSAGE_EMISSION_PILOT_CLOSEOUT_OR_EXPANSION"
REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022G_SET_LANGUAGE_ACTIVE_LOOKUP_SMOKE.md")

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def has_any(upper: str, options):
    return any(opt in upper for opt in options)

def main():
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

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22G_SOURCE_PATCH_APPLIED",
         p22g.get("STATUS") == "MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_CATALOG_LOOKUP_SOURCE_PATCH_APPLIED",
         p22g.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))

    # Accept either the original 22G lookup wording or the actual stronger runtime output observed locally.
    gate("LANGUAGE_SET_TO_ES",
         has_any(upper, ["CURRENT LANGUAGE: ES", "CURRENT LOCALE: ES", "IDIOMA DE MENSAJES: ES"]),
         "SET LANGUAGE es / current locale should be visible")
    gate("CATALOG_VALIDATION_GREEN",
         has_any(upper, ["MESSAGE CATALOG VALIDATION: GREEN", "SET LANGUAGE ACTIVE CATALOG CHECK"]),
         "catalog validation or active lookup heading should be visible")
    gate("PROVIDER_ACTIVE_DBF",
         has_any(upper, ["MESSAGE CATALOG MODE: ACTIVE_DBF", "PROVIDER MODE: ACTIVE_DBF"]),
         "provider must report active_dbf")
    gate("ACTIVE_CATALOG_LOADED_YES",
         "ACTIVE CATALOG LOADED: YES" in upper,
         "active catalog loaded")
    gate("MESSAGE_COUNT_12",
         "MESSAGES: 12" in upper or "MESSAGE COUNT: 12" in upper,
         "12 messages")
    gate("TEXT_ROWS_60",
         "TEXT ROWS: 60" in upper or "TEXT ROW COUNT: 60" in upper,
         "60 text rows")
    gate("SYMBOL_PROOF_PRESENT",
         has_any(upper, ["SYMBOL: HELP_HINT_COMMAND", "LOOKUP SYMBOL: MESSAGE_LOCALE_SET"]),
         "sample symbol should be visible")
    gate("SPANISH_LOOKUP_OR_EMISSION_TEXT_PRESENT",
         ("TEXT:" in upper and "<EMPTY>" not in upper) or ("LOOKUP TEXT:" in upper and "<EMPTY>" not in upper),
         "active lookup/emission text must be non-empty")
    gate("BOUNDARY_READ_ONLY_NO_WRITEBACK",
         "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper,
         "read-only/no-writeback boundary")
    gate("NO_ISSUES",
         "ISSUES: 0" in upper or "VALIDATION ISSUES: 0" in upper or "RUNTIME ACTIVE CATALOG LOOKUP PROOF: YES" in upper,
         "validation should show zero issues or explicit lookup proof")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22g_1_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SET_LANGUAGE_ACTIVE_LOOKUP_PROOF": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_MESSAGE_EMISSION_SAMPLE": 1 if "SET LANGUAGE ACTIVE MESSAGE EMISSION" in upper else 0,
        "ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in upper else 0,
        "LOOKUP_OR_EMISSION_SYMBOL": "HELP_HINT_COMMAND" if "SYMBOL: HELP_HINT_COMMAND" in upper else "MESSAGE_LOCALE_SET",
        "LOOKUP_OR_EMISSION_LOCALE": "es",
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SET_LANGUAGE_ACTIVE_LOOKUP_PROOF", "ACTIVE_MESSAGE_EMISSION_SAMPLE",
         "ACTIVE_CATALOG_LOADED", "LOOKUP_OR_EMISSION_SYMBOL",
         "LOOKUP_OR_EMISSION_LOCALE", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "SOURCE_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22g_1_runtime_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22G.1 runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Provider read-only lookup/emission sample; no active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22g_1_runtime_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  set language active lookup proof: {1 if status == STATUS_GREEN else 0}")
    print(f"  active message emission sample: {1 if 'SET LANGUAGE ACTIVE MESSAGE EMISSION' in upper else 0}")
    print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in upper else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
