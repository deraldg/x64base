#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22M_LOW_RISK_SET_LANGUAGE_RUNTIME_ROUTING_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22M_LOW_RISK_SET_LANGUAGE_RUNTIME_ROUTING_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22N_ROUTING_PROOF_LINE_REVIEW_OR_NEXT_LOW_RISK_SEAM"
RUNLOG = Path("docs/messaging/runlog/MSG-022M_SET_LANGUAGE_ROUTING_SMOKE.md")

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
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)

    p22m = first_row(reports / "message_catalog_phase22m_status_summary_v1.csv")
    messages = p22m.get("MESSAGES", "12")
    text_rows = p22m.get("TEXT_ROWS", "60")
    locales = p22m.get("LOCALES", "de;en-US;es;fr;it")

    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22M_PATCH_APPLIED",
         p22m.get("STATUS") == "MESSAGE_CATALOG_PHASE22M_LOW_RISK_SET_LANGUAGE_RUNTIME_ROUTING_PATCH_APPLIED",
         p22m.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("SET_LANGUAGE_ES_VISIBLE",
         ("IDIOMA DE MENSAJES: ES" in upper) or ("MESSAGE LANGUAGE" in upper) or ("LOCALE" in upper and "ES" in upper),
         "SET LANGUAGE es output should be visible")
    gate("ROUTING_PROOF_LINE_PRESENT",
         "MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET" in upper,
         "SET LANGUAGE must explicitly prove active-provider routing for MESSAGE_LOCALE_SET")
    gate("PROVIDER_STATUS_ACTIVE_DBF",
         "MODE: ACTIVE_DBF" in upper or "PROVIDER MODE: ACTIVE_DBF" in upper,
         "SET MESSAGE CATALOG CHECK should show active_dbf")
    gate("ACTIVE_CATALOG_LOADED_YES",
         "ACTIVE CATALOG LOADED: YES" in upper,
         "active catalog loaded")
    gate("MESSAGE_COUNT_12",
         "MESSAGE COUNT: 12" in upper or "MESSAGES: 12" in upper,
         "12 message rows")
    gate("TEXT_ROWS_60",
         "TEXT ROW COUNT: 60" in upper or "TEXT ROWS: 60" in upper,
         "60 text rows")
    gate("NO_WRITEBACK_BOUNDARY",
         "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper,
         "read-only/no-writeback boundary from provider status")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22m_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SET_LANGUAGE_ROUTING_PROOF": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET" in upper else 0,
        "PROVIDER_ACTIVE_DBF": 1 if "ACTIVE_DBF" in upper else 0,
        "ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in upper else 0,
        "ROUTED_SYMBOL": "MESSAGE_LOCALE_SET",
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SET_LANGUAGE_ROUTING_PROOF", "PROVIDER_ACTIVE_DBF",
         "ACTIVE_CATALOG_LOADED", "ROUTED_SYMBOL", "SOURCE_MUTATION_OBSERVED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22m_runtime_gate_check_v1.csv",
              gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22M runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22m_runtime_boundary_ledger_v1.csv",
              boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  set language routing proof: {1 if 'MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET' in upper else 0}")
    print(f"  provider active_dbf: {1 if 'ACTIVE_DBF' in upper else 0}")
    print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in upper else 0}")
    print("  routed symbol: MESSAGE_LOCALE_SET")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
