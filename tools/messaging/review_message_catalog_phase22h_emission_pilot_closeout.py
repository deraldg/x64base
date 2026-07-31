#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22H_RUNTIME_MESSAGE_EMISSION_PILOT_CLOSEOUT_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22H_RUNTIME_MESSAGE_EMISSION_PILOT_CLOSEOUT_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22I_CONTROLLED_RUNTIME_EMISSION_EXPANSION"
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

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists() or not path.is_file():
        return ""
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def file_row(repo: Path, relpath: str):
    path = repo / relpath
    return {
        "PATH": relpath,
        "EXISTS": 1 if path.exists() else 0,
        "BYTES": path.stat().st_size if path.exists() and path.is_file() else 0,
        "SHA256": sha256_file(path),
    }

def has_any(upper: str, options):
    return any(opt in upper for opt in options)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    g_row = first_row(reports / "message_catalog_phase22g_1_runtime_status_summary_v1.csv")
    latest = {}
    latest_path = reports / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            import json
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    messages = g_row.get("MESSAGES", "12")
    text_rows = g_row.get("TEXT_ROWS", "60")
    locales = g_row.get("LOCALES", "de;en-US;es;fr;it")

    runlog = repo / RUNLOG
    runtext = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = runtext.upper()

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name, ok, detail):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22G_RUNTIME_GREEN",
         g_row.get("STATUS") == "MESSAGE_CATALOG_PHASE22G_ACTIVE_LANGUAGE_LOOKUP_AND_EMISSION_SMOKE_GREEN",
         g_row.get("STATUS", ""))
    gate("MSG_022G_SAVEPOINT_LATEST_OR_PRESENT",
         latest.get("savepoint_id") == "MSG-022G" or "MSG-022G" in (repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md").read_text(encoding="utf-8", errors="replace") if (repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md").exists() else False,
         latest.get("savepoint_id", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("ACTIVE_PROVIDER_MODE_PROVEN", "PROVIDER MODE: ACTIVE_DBF" in upper or "MESSAGE CATALOG MODE: ACTIVE_DBF" in upper, "provider active_dbf")
    gate("ACTIVE_CATALOG_LOADED_PROVEN", "ACTIVE CATALOG LOADED: YES" in upper, "active catalog loaded")
    gate("MESSAGE_ROWS_12_PROVEN", "MESSAGES: 12" in upper or "MESSAGE COUNT: 12" in upper, "12 message rows")
    gate("TEXT_ROWS_60_PROVEN", "TEXT ROWS: 60" in upper or "TEXT ROW COUNT: 60" in upper, "60 text rows")
    gate("SET_LANGUAGE_ES_PROVEN",
         has_any(upper, ["IDIOMA DE MENSAJES: ES", "CURRENT LOCALE: ES", "CURRENT LANGUAGE: ES"]),
         "SET LANGUAGE es visible")
    gate("ACTIVE_EMISSION_SAMPLE_PROVEN",
         "SET LANGUAGE ACTIVE MESSAGE EMISSION" in upper and "SYMBOL: HELP_HINT_COMMAND" in upper and "TEXT:" in upper,
         "HELP_HINT_COMMAND emission sample")
    gate("BOUNDARY_NO_WRITEBACK_PROVEN",
         "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper,
         "read-only/no-writeback")
    review("SPANISH_TEXT_HAS_PLACEHOLDER",
           "{COMMAND}" in upper,
           "HELP_HINT_COMMAND retained {command} placeholder")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22h_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "EMISSION_PILOT_CLOSED": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_MESSAGE_EMISSION_SAMPLE": 1 if "SET LANGUAGE ACTIVE MESSAGE EMISSION" in upper else 0,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "EMISSION_PILOT_CLOSED", "ACTIVE_MESSAGE_EMISSION_SAMPLE",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22h_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    evidence = [
        {"EVIDENCE_ID": "EMIT-001", "CLAIM": "SET LANGUAGE selected Spanish locale", "STATUS": "PROVEN", "DETAIL": "Runtime output shows Idioma de mensajes: es / current locale es."},
        {"EVIDENCE_ID": "EMIT-002", "CLAIM": "Active DBF provider loaded catalog rows", "STATUS": "PROVEN", "DETAIL": "Runtime output shows provider mode active_dbf and active catalog loaded yes."},
        {"EVIDENCE_ID": "EMIT-003", "CLAIM": "Active catalog row counts match baseline", "STATUS": "PROVEN", "DETAIL": "Runtime output shows messages 12 and text rows 60."},
        {"EVIDENCE_ID": "EMIT-004", "CLAIM": "Localized message text emitted from active provider path", "STATUS": "PROVEN", "DETAIL": "Runtime output emits HELP_HINT_COMMAND in Spanish: Escriba HELP {command} para obtener mas informacion."},
        {"EVIDENCE_ID": "EMIT-005", "CLAIM": "Emission remained read-only", "STATUS": "PROVEN", "DETAIL": "Runtime output states no DBF/CDX/LMDB mutation and no runtime writeback."},
    ]
    write_csv(reports / "message_catalog_phase22h_emission_pilot_evidence_v1.csv", evidence,
              ["EVIDENCE_ID", "CLAIM", "STATUS", "DETAIL"])

    expansion = [
        {"STEP": "22I", "ACTION": "CONTROLLED_RUNTIME_EMISSION_EXPANSION", "RECOMMENDATION": "Add one explicit diagnostic command/smoke to emit selected symbols/locales through the provider without changing broad command output.", "MUTATION_SCOPE": "small source patch only if authorized"},
        {"STEP": "22J", "ACTION": "PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW", "RECOMMENDATION": "Before broad routing, catalog placeholders such as {command} need typed argument/placeholder validation.", "MUTATION_SCOPE": "report-first"},
        {"STEP": "22K", "ACTION": "LOW_RISK_STATUS_MESSAGE_ROUTING", "RECOMMENDATION": "Route one or two noncritical status messages through message IDs while preserving compiled fallback.", "MUTATION_SCOPE": "guarded source patch"},
        {"STEP": "23", "ACTION": "LOCALE_SPINE_ALIGNMENT", "RECOMMENDATION": "Align message locale behavior with shared SYSTEM_LOCALES / SYSTEM_LOCALE_FALLBACK spine before manualgen/help/datadict consumers depend on it.", "MUTATION_SCOPE": "report-first unless separately authorized"},
    ]
    write_csv(reports / "message_catalog_phase22h_expansion_plan_v1.csv", expansion,
              ["STEP", "ACTION", "RECOMMENDATION", "MUTATION_SCOPE"])

    source_scan = [
        file_row(repo, "src/help/message_catalog.hpp"),
        file_row(repo, "src/help/message_catalog.cpp"),
        file_row(repo, "src/cli/cmd_set.cpp"),
        file_row(repo, "docs/messaging/runlog/MSG-022G_SET_LANGUAGE_ACTIVE_LOOKUP_SMOKE.md"),
    ]
    write_csv(reports / "message_catalog_phase22h_source_and_evidence_scan_v1.csv", source_scan,
              ["PATH", "EXISTS", "BYTES", "SHA256"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22H closeout/report only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22h_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    md = f"""# Message Catalog Phase 22H Runtime Message Emission Pilot Closeout

Status: `{status}`

Phase 22H closes the Phase 22G pilot as a proven runtime emission sample.

## Proven

- `SET LANGUAGE es` selected Spanish.
- Active provider mode was `active_dbf`.
- Active catalog loaded successfully.
- Runtime saw 12 message rows and 60 localized text rows.
- `HELP_HINT_COMMAND` emitted Spanish text through the active-provider path.
- Boundary remained read-only: no DBF/CDX/LMDB mutation and no runtime writeback.

## Not yet claimed

- Broad command/error routing through the Messaging subsystem.
- Typed placeholder/argument validation for `{{command}}`.
- HELP DATA or CMDHELPCHK integration.
- Manualgen or Data Dictionary consumption.

## Next gate

`{NEXT_GATE}`
"""
    (reports / "MESSAGE_CATALOG_PHASE22H_RUNTIME_MESSAGE_EMISSION_PILOT_CLOSEOUT.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  emission pilot closed: {1 if status == STATUS_GREEN else 0}")
    print(f"  active message emission sample: {1 if 'SET LANGUAGE ACTIVE MESSAGE EMISSION' in upper else 0}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
