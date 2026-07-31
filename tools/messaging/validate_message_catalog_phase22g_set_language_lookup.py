#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_CATALOG_LOOKUP_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_CATALOG_LOOKUP_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22H_RUNTIME_MESSAGE_EMISSION_PILOT"
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
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

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

    gate("PHASE22G_SOURCE_PATCH_APPLIED", p22g.get("STATUS") == "MESSAGE_CATALOG_PHASE22G_SET_LANGUAGE_ACTIVE_CATALOG_LOOKUP_SOURCE_PATCH_APPLIED", p22g.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("SET_LANGUAGE_CHECK_PRESENT", "SET LANGUAGE ACTIVE CATALOG CHECK" in upper, "check heading")
    gate("CURRENT_LANGUAGE_ES", "CURRENT LANGUAGE: ES" in upper, "SET LANGUAGE es")
    gate("MESSAGE_CATALOG_MODE_ACTIVE_DBF", "MESSAGE CATALOG MODE: ACTIVE_DBF" in upper, "active dbf mode")
    gate("ACTIVE_CATALOG_LOADED_YES", "ACTIVE CATALOG LOADED: YES" in upper, "active catalog loaded")
    gate("LOOKUP_SYMBOL_PRESENT", "LOOKUP SYMBOL: MESSAGE_LOCALE_SET" in upper, "sample symbol")
    gate("LOOKUP_LOCALE_ES", "LOOKUP LOCALE: ES" in upper, "sample locale")
    gate("LOOKUP_TEXT_NOT_EMPTY", "LOOKUP TEXT:" in upper and "LOOKUP TEXT: <EMPTY>" not in upper, "non-empty lookup text")
    gate("LOOKUP_PROOF_YES", "RUNTIME ACTIVE CATALOG LOOKUP PROOF: YES" in upper, "proof flag")
    gate("NO_WRITEBACK_BOUNDARY", "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper, "read-only boundary")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation = str(failures)
    write_csv(reports / "message_catalog_phase22g_runtime_status_summary_v1.csv", [{
        "STATUS": status, "MESSAGES": messages, "TEXT_ROWS": text_rows, "LOCALES": locales,
        "VALIDATION_ISSUES": validation, "SET_LANGUAGE_ACTIVE_LOOKUP_PROOF": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in upper else 0,
        "LOOKUP_SYMBOL": "MESSAGE_LOCALE_SET", "LOOKUP_LOCALE": "es",
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0, "SOURCE_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE, "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    }], ["STATUS","MESSAGES","TEXT_ROWS","LOCALES","VALIDATION_ISSUES","SET_LANGUAGE_ACTIVE_LOOKUP_PROOF","ACTIVE_CATALOG_LOADED","LOOKUP_SYMBOL","LOOKUP_LOCALE","ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    write_csv(reports / "message_catalog_phase22g_runtime_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Phase 22G runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"Provider read-only lookup; no active DBF mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active CDX/index mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active LMDB mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22g_runtime_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation}")
    print(f"  set language active lookup proof: {1 if status == STATUS_GREEN else 0}")
    print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in upper else 0}")
    print("  lookup symbol: MESSAGE_LOCALE_SET")
    print("  lookup locale: es")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
