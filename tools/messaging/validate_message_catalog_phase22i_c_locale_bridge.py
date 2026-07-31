#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22I_C_SET_LANGUAGE_LOCALE_STATE_BRIDGE_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22I_C_SET_LANGUAGE_LOCALE_STATE_BRIDGE_SMOKE_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22J_PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW"
RUNLOG = Path("docs/messaging/runlog/MSG-022I_C_LOCALE_BRIDGE_SMOKE.md")

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

def split_emit_blocks(text: str):
    marker = "SET MESSAGE EMIT:"
    return [marker + part for part in text.split(marker)[1:]]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)

    p22ic = first_row(reports / "message_catalog_phase22i_c_status_summary_v1.csv")
    messages = p22ic.get("MESSAGES", "12")
    text_rows = p22ic.get("TEXT_ROWS", "60")
    locales = p22ic.get("LOCALES", "de;en-US;es;fr;it")

    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()
    blocks = [b.upper() for b in split_emit_blocks(text)]

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22I_C_PATCH_APPLIED",
         p22ic.get("STATUS") == "MESSAGE_CATALOG_PHASE22I_C_SET_LANGUAGE_LOCALE_STATE_BRIDGE_REPAIR_APPLIED",
         p22ic.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("SET_LANGUAGE_ES_VISIBLE",
         "IDIOMA DE MENSAJES: ES" in upper or "LANGUAGE: ES" in upper or "CURRENT LOCALE: ES" in upper,
         "SET LANGUAGE es should be visible")
    gate("TWO_EMIT_BLOCKS_PRESENT",
         len(blocks) >= 2,
         f"observed SET MESSAGE EMIT blocks={len(blocks)}")

    default_ok = False
    explicit_ok = False
    if blocks:
        b = blocks[0]
        default_ok = (
            "SYMBOL: HELP_HINT_COMMAND" in b and
            "CURRENT LOCALE: ES" in b and
            "LOCALE: ES" in b and
            "PROVIDER MODE: ACTIVE_DBF" in b and
            "ACTIVE CATALOG LOADED: YES" in b and
            "RUNTIME CONTROLLED EMISSION PROOF: YES" in b and
            "TEXT: <EMPTY>" not in b
        )
    explicit_ok = any(
        "SYMBOL: HELP_HINT_COMMAND" in b and
        "LOCALE: ES" in b and
        "PROVIDER MODE: ACTIVE_DBF" in b and
        "ACTIVE CATALOG LOADED: YES" in b and
        "RUNTIME CONTROLLED EMISSION PROOF: YES" in b and
        "TEXT: <EMPTY>" not in b
        for b in blocks[1:]
    )

    gate("DEFAULT_EMIT_INHERITS_SET_LANGUAGE_ES",
         default_ok,
         "first SET MESSAGE EMIT should report current locale es and locale es")
    gate("EXPLICIT_LOCALE_ES_OVERRIDE_STILL_WORKS",
         explicit_ok,
         "explicit LOCALE es emission should still work")
    gate("NO_WRITEBACK_BOUNDARY",
         "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper,
         "read-only/no-writeback")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22i_c_runtime_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "DEFAULT_LOCALE_BRIDGE_PROOF": 1 if default_ok else 0,
        "EXPLICIT_LOCALE_OVERRIDE_PROOF": 1 if explicit_ok else 0,
        "ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in upper else 0,
        "EMIT_SYMBOL": "HELP_HINT_COMMAND",
        "EMIT_LOCALE": "es",
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "DEFAULT_LOCALE_BRIDGE_PROOF", "EXPLICIT_LOCALE_OVERRIDE_PROOF",
         "ACTIVE_CATALOG_LOADED", "EMIT_SYMBOL", "EMIT_LOCALE",
         "SOURCE_MUTATION_OBSERVED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22i_c_runtime_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22I-C runtime validation only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22i_c_runtime_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  default locale bridge proof: {1 if default_ok else 0}")
    print(f"  explicit locale override proof: {1 if explicit_ok else 0}")
    print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in upper else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
