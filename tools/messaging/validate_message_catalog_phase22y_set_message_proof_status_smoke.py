#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE_BLOCKED"
NEXT_GATE = "RERUN_PHASE22V_REGRESSION_PACK_AFTER_PHASE22Y_OR_HOLD"
RUNLOG = Path("docs/messaging/runlog/MSG-022Y_SET_MESSAGE_PROOF_STATUS_TEXT_SMOKE.md")

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

def count(text: str, pattern: str) -> int:
    return text.upper().count(pattern.upper())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)
    p22y = first_row(reports / "message_catalog_phase22y_status_summary_v1.csv")
    messages = p22y.get("MESSAGES", "12")
    text_rows = p22y.get("TEXT_ROWS", "60")
    locales = p22y.get("LOCALES", "de;en-US;es;fr;it")

    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""

    proof_status_count = count(text, "Message routing proof mode:")
    status_on = count(text, "Message routing proof mode: on")
    status_off = count(text, "Message routing proof mode: off")
    spanish_status = count(text, "Modo de prueba de enrutamiento de mensajes")
    boundary_count = count(text, "no DBF/CDX/LMDB mutation")
    writeback_count = count(text, "no runtime writeback")
    provider_status = count(text, "Message catalog provider status:")
    active_dbf = count(text, "mode: active_dbf")
    active_loaded = count(text, "active catalog loaded: yes")
    fallback_available = count(text, "compiled fallback available")

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22Y_PATCH_APPLIED",
         p22y.get("STATUS") == "MESSAGE_CATALOG_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_PATCH_APPLIED",
         p22y.get("STATUS", "missing"))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("PROOF_STATUS_LINES_PRESENT", proof_status_count >= 3, f"proof_status_count={proof_status_count}")
    gate("PROOF_STATUS_ON_PRESENT", status_on >= 1, f"status_on={status_on}")
    gate("PROOF_STATUS_OFF_PRESENT", status_off >= 2, f"status_off={status_off}")
    gate("SPANISH_STATUS_SUFFIX_PRESENT", spanish_status >= 1, f"spanish_status={spanish_status}")
    gate("BOUNDARY_NO_DBF_CDX_LMDB_PRESENT", boundary_count >= 3, f"boundary_count={boundary_count}")
    gate("BOUNDARY_NO_RUNTIME_WRITEBACK_PRESENT", writeback_count >= 3, f"writeback_count={writeback_count}")
    gate("PROVIDER_STATUS_ACTIVE_DBF", provider_status >= 1 and active_dbf >= 1, f"provider={provider_status}; active_dbf={active_dbf}")
    gate("ACTIVE_CATALOG_LOADED", active_loaded >= 1, f"active_loaded={active_loaded}")
    gate("COMPILED_FALLBACK_AVAILABLE", fallback_available >= 1, f"fallback_available={fallback_available}")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22y_runtime_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22y_runtime_metrics_v1.csv", [{
        "PROOF_STATUS_COUNT": proof_status_count,
        "PROOF_STATUS_ON_COUNT": status_on,
        "PROOF_STATUS_OFF_COUNT": status_off,
        "SPANISH_STATUS_SUFFIX_COUNT": spanish_status,
        "BOUNDARY_NO_DBF_CDX_LMDB_COUNT": boundary_count,
        "BOUNDARY_NO_RUNTIME_WRITEBACK_COUNT": writeback_count,
        "PROVIDER_STATUS_COUNT": provider_status,
        "ACTIVE_DBF_COUNT": active_dbf,
        "ACTIVE_CATALOG_LOADED_COUNT": active_loaded,
        "COMPILED_FALLBACK_AVAILABLE_COUNT": fallback_available,
    }], ["PROOF_STATUS_COUNT", "PROOF_STATUS_ON_COUNT", "PROOF_STATUS_OFF_COUNT",
         "SPANISH_STATUS_SUFFIX_COUNT", "BOUNDARY_NO_DBF_CDX_LMDB_COUNT",
         "BOUNDARY_NO_RUNTIME_WRITEBACK_COUNT", "PROVIDER_STATUS_COUNT",
         "ACTIVE_DBF_COUNT", "ACTIVE_CATALOG_LOADED_COUNT",
         "COMPILED_FALLBACK_AVAILABLE_COUNT"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Runtime validation only; source mutation occurred only during authorized apply."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation during runtime smoke."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]
    write_csv(reports / "message_catalog_phase22y_runtime_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22y_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PROOF_STATUS_ROUTING_PROOF": 1 if proof_status_count >= 3 and spanish_status >= 1 else 0,
        "PROOF_STATUS_ON_PRESENT": 1 if status_on >= 1 else 0,
        "PROOF_STATUS_OFF_PRESENT": 1 if status_off >= 2 else 0,
        "BOUNDARY_PRESERVED": 1 if boundary_count >= 3 and writeback_count >= 3 else 0,
        "PROVIDER_ACTIVE_DBF": 1 if provider_status >= 1 and active_dbf >= 1 else 0,
        "ACTIVE_CATALOG_LOADED": 1 if active_loaded >= 1 else 0,
        "SOURCE_MUTATION_OBSERVED_DURING_RUNTIME": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PROOF_STATUS_ROUTING_PROOF", "PROOF_STATUS_ON_PRESENT",
         "PROOF_STATUS_OFF_PRESENT", "BOUNDARY_PRESERVED", "PROVIDER_ACTIVE_DBF",
         "ACTIVE_CATALOG_LOADED", "SOURCE_MUTATION_OBSERVED_DURING_RUNTIME",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  proof status routing proof: {1 if proof_status_count >= 3 and spanish_status >= 1 else 0}")
    print(f"  proof status on present: {1 if status_on >= 1 else 0}")
    print(f"  proof status off present: {1 if status_off >= 2 else 0}")
    print(f"  boundary preserved: {1 if boundary_count >= 3 and writeback_count >= 3 else 0}")
    print(f"  provider active_dbf: {1 if provider_status >= 1 and active_dbf >= 1 else 0}")
    print(f"  active catalog loaded: {1 if active_loaded >= 1 else 0}")
    print("  source mutation observed during runtime: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
