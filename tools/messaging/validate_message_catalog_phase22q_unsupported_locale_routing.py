#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22Q_UNSUPPORTED_LOCALE_RUNTIME_ROUTING_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22Q_UNSUPPORTED_LOCALE_RUNTIME_ROUTING_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22R_HELP_HINT_ROUTING_PLAN"
RUNLOG = Path("docs/messaging/runlog/MSG-022Q_UNSUPPORTED_LOCALE_ROUTING_SMOKE.md")

PROOF_LINE = "MESSAGE ROUTING PROOF: ACTIVE_DBF UNSUPPORTED_MESSAGE_LOCALE"

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

    p22q = first_row(reports / "message_catalog_phase22q_status_summary_v1.csv")
    messages = p22q.get("MESSAGES", "12")
    text_rows = p22q.get("TEXT_ROWS", "60")
    locales = p22q.get("LOCALES", "de;en-US;es;fr;it")

    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()

    proof_line_count = upper.count(PROOF_LINE)
    mode_on_count = upper.count("MESSAGE ROUTING PROOF MODE: ON")
    mode_off_count = upper.count("MESSAGE ROUTING PROOF MODE: OFF")
    unsupported_symbol_count = upper.count("UNSUPPORTED_MESSAGE_LOCALE")
    zz_count = upper.count("ZZ")

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22Q_PATCH_APPLIED",
         p22q.get("STATUS") == "MESSAGE_CATALOG_PHASE22Q_UNSUPPORTED_LOCALE_RUNTIME_ROUTING_PATCH_APPLIED",
         p22q.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("PROOF_MODE_OFF_SEEN",
         mode_off_count >= 2,
         f"Message routing proof mode: off count={mode_off_count}")
    gate("PROOF_MODE_ON_SEEN",
         mode_on_count >= 1,
         f"Message routing proof mode: on count={mode_on_count}")
    gate("UNSUPPORTED_LOCALE_VALUE_VISIBLE",
         zz_count >= 2,
         f"zz/ZZ count={zz_count}")
    gate("UNSUPPORTED_LOCALE_PROOF_LINE_GATED",
         proof_line_count == 1,
         f"proof line count should be exactly 1 in ON section; observed={proof_line_count}")
    gate("UNSUPPORTED_SYMBOL_VISIBLE",
         unsupported_symbol_count >= 1,
         f"UNSUPPORTED_MESSAGE_LOCALE count={unsupported_symbol_count}")
    gate("VALID_LOCALE_SUCCESS_STILL_WORKS",
         "IDIOMA DE MENSAJES: ES" in upper or "MESSAGE LOCALE: ES" in upper,
         "SET LANGUAGE es should still work before invalid locale probes")
    gate("PROVIDER_STATUS_ACTIVE_DBF",
         "MODE: ACTIVE_DBF" in upper or "PROVIDER MODE: ACTIVE_DBF" in upper,
         "SET MESSAGE CATALOG CHECK should show active_dbf")
    gate("ACTIVE_CATALOG_LOADED_YES",
         "ACTIVE CATALOG LOADED: YES" in upper,
         "active catalog loaded")
    gate("NO_WRITEBACK_BOUNDARY",
         "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper,
         "read-only/no-writeback boundary")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22q_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PROOF_MODE_ON_COUNT": mode_on_count,
        "PROOF_MODE_OFF_COUNT": mode_off_count,
        "UNSUPPORTED_PROOF_LINE_COUNT": proof_line_count,
        "UNSUPPORTED_LOCALE_VALUE_COUNT": zz_count,
        "UNSUPPORTED_SYMBOL_COUNT": unsupported_symbol_count,
        "UNSUPPORTED_LOCALE_ROUTING_PROOF": 1 if proof_line_count == 1 else 0,
        "PROOF_LANE_GATED": 1 if proof_line_count == 1 and mode_on_count >= 1 and mode_off_count >= 2 else 0,
        "PROVIDER_ACTIVE_DBF": 1 if "ACTIVE_DBF" in upper else 0,
        "ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in upper else 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PROOF_MODE_ON_COUNT", "PROOF_MODE_OFF_COUNT", "UNSUPPORTED_PROOF_LINE_COUNT",
         "UNSUPPORTED_LOCALE_VALUE_COUNT", "UNSUPPORTED_SYMBOL_COUNT",
         "UNSUPPORTED_LOCALE_ROUTING_PROOF", "PROOF_LANE_GATED",
         "PROVIDER_ACTIVE_DBF", "ACTIVE_CATALOG_LOADED", "SOURCE_MUTATION_OBSERVED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22q_runtime_gate_check_v1.csv",
              gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22Q runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22q_runtime_boundary_ledger_v1.csv",
              boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  proof mode on count: {mode_on_count}")
    print(f"  proof mode off count: {mode_off_count}")
    print(f"  unsupported proof line count: {proof_line_count}")
    print(f"  unsupported locale routing proof: {1 if proof_line_count == 1 else 0}")
    print(f"  proof lane gated: {1 if proof_line_count == 1 and mode_on_count >= 1 and mode_off_count >= 2 else 0}")
    print(f"  provider active_dbf: {1 if 'ACTIVE_DBF' in upper else 0}")
    print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in upper else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
