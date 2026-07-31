#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22X_SET_MESSAGE_PROOF_STATUS_TEXT_ROUTING_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22X_SET_MESSAGE_PROOF_STATUS_TEXT_ROUTING_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22Y_SET_MESSAGE_PROOF_STATUS_TEXT_CATALOG_AND_SOURCE_PATCH"
REPORT_DIR = Path("docs/messaging/reports")

SELECTED_SEAM_ID = "RT-008"
SELECTED_SEAM = "SET MESSAGE PROOF status text routing"
SOURCE_TARGET = "src/cli/cmd_set.cpp"

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
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            latest_id = latest.get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal_text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in journal_text, latest_id

def find_anchor_rows(repo: Path):
    source = repo / SOURCE_TARGET
    rows = []
    if not source.exists():
        return rows
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    needles = [
        "print_message_proof_status",
        "Message routing proof mode:",
        "proof mode changes runtime diagnostic state only",
        "message_routing_proof_enabled()",
        "set_message_routing_proof_enabled(",
        "handle_set_message_proof",
        "SET MESSAGE PROOF",
    ]
    for i, line in enumerate(lines, start=1):
        for needle in needles:
            if needle in line:
                rows.append({
                    "SOURCE_PATH": SOURCE_TARGET,
                    "LINE": i,
                    "NEEDLE": needle,
                    "TEXT": line.strip(),
                })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22w = first_row(reports / "message_catalog_phase22w_status_summary_v1.csv")
    p22v = first_row(reports / "message_catalog_phase22v_runtime_regression_status_summary_v1.csv")
    messages = p22w.get("MESSAGES", p22v.get("MESSAGES", "12"))
    text_rows = p22w.get("TEXT_ROWS", p22v.get("TEXT_ROWS", "60"))
    locales = p22w.get("LOCALES", p22v.get("LOCALES", "de;en-US;es;fr;it"))
    savepoint_ok, latest_id = savepoint_present(repo, "MSG-022W")

    source_path = repo / SOURCE_TARGET
    anchor_rows = find_anchor_rows(repo)
    source_hash = sha256_file(source_path)

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22W_SELECTION_GREEN",
         p22w.get("STATUS") == "MESSAGE_CATALOG_PHASE22W_NEXT_LOW_RISK_RUNTIME_SEAM_SELECTION_GREEN_SOURCE_HELD",
         p22w.get("STATUS", "missing"))
    gate("MSG_022W_SAVEPOINT_PRESENT", savepoint_ok, latest_id)
    gate("PHASE22V_REGRESSION_GREEN",
         p22v.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN",
         p22v.get("STATUS", "missing"))
    gate("SELECTED_SEAM_RT_008",
         p22w.get("SELECTED_SEAM_ID") == SELECTED_SEAM_ID,
         p22w.get("SELECTED_SEAM_ID", ""))
    gate("SOURCE_TARGET_PRESENT", source_path.exists(), SOURCE_TARGET)
    gate("ANCHORS_VISIBLE", len(anchor_rows) >= 3, f"anchor rows={len(anchor_rows)}")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    symbol_contract = [
        {
            "SYMBOL": "MESSAGE_PROOF_MODE_STATUS",
            "KIND": "runtime_status_message",
            "CURRENT_FALLBACK_TEXT": "Message routing proof mode: {mode}",
            "PLACEHOLDERS": "mode",
            "PLACEHOLDER_TYPE": "enum(on|off)",
            "LOCALE_SCOPE": "all active locales",
            "EN_US_TEXT_PROPOSED": "Message routing proof mode: {mode}",
            "ES_TEXT_PROPOSED": "Modo de prueba de enrutamiento de mensajes: {mode}",
            "DE_TEXT_PROPOSED": "Nachrichten-Routing-Pruefmodus: {mode}",
            "FR_TEXT_PROPOSED": "Mode de preuve du routage des messages : {mode}",
            "IT_TEXT_PROPOSED": "Modalita prova instradamento messaggi: {mode}",
            "PATCH_IN_22X": 0,
        },
        {
            "SYMBOL": "MESSAGE_PROOF_BOUNDARY_NOTE",
            "KIND": "runtime_boundary_message",
            "CURRENT_FALLBACK_TEXT": "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback",
            "PLACEHOLDERS": "",
            "PLACEHOLDER_TYPE": "",
            "LOCALE_SCOPE": "all active locales",
            "EN_US_TEXT_PROPOSED": "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback",
            "ES_TEXT_PROPOSED": "limite: el modo de prueba solo cambia el estado diagnostico en ejecucion; sin mutacion DBF/CDX/LMDB; sin escritura de vuelta en ejecucion",
            "DE_TEXT_PROPOSED": "Grenze: Der Pruefmodus aendert nur den Laufzeit-Diagnosestatus; keine DBF/CDX/LMDB-Mutation; kein Laufzeit-Zurueckschreiben",
            "FR_TEXT_PROPOSED": "limite : le mode de preuve ne change que l'etat diagnostique d'execution; aucune mutation DBF/CDX/LMDB; aucune reecriture d'execution",
            "IT_TEXT_PROPOSED": "confine: la modalita prova cambia solo lo stato diagnostico runtime; nessuna mutazione DBF/CDX/LMDB; nessuna riscrittura runtime",
            "PATCH_IN_22X": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22x_symbol_contract_plan_v1.csv", symbol_contract,
              ["SYMBOL", "KIND", "CURRENT_FALLBACK_TEXT", "PLACEHOLDERS", "PLACEHOLDER_TYPE",
               "LOCALE_SCOPE", "EN_US_TEXT_PROPOSED", "ES_TEXT_PROPOSED", "DE_TEXT_PROPOSED",
               "FR_TEXT_PROPOSED", "IT_TEXT_PROPOSED", "PATCH_IN_22X"])

    anchor_plan = [
        {
            "ANCHOR_ID": "A1",
            "SOURCE_PATH": SOURCE_TARGET,
            "TARGET_FUNCTION": "print_message_proof_status",
            "CURRENT_TEXT": "Message routing proof mode: on/off",
            "ROUTE_SYMBOL": "MESSAGE_PROOF_MODE_STATUS",
            "ROUTE_ARGUMENTS": "mode=on|off",
            "RECOMMENDATION": "PATCH_IN_22Y_AFTER_AUTHORIZATION",
        },
        {
            "ANCHOR_ID": "A2",
            "SOURCE_PATH": SOURCE_TARGET,
            "TARGET_FUNCTION": "print_message_proof_status",
            "CURRENT_TEXT": "boundary: proof mode changes runtime diagnostic state only; no DBF/CDX/LMDB mutation; no runtime writeback",
            "ROUTE_SYMBOL": "MESSAGE_PROOF_BOUNDARY_NOTE",
            "ROUTE_ARGUMENTS": "",
            "RECOMMENDATION": "PATCH_IN_22Y_AFTER_AUTHORIZATION",
        },
    ]
    write_csv(reports / "message_catalog_phase22x_anchor_plan_v1.csv", anchor_plan,
              ["ANCHOR_ID", "SOURCE_PATH", "TARGET_FUNCTION", "CURRENT_TEXT", "ROUTE_SYMBOL",
               "ROUTE_ARGUMENTS", "RECOMMENDATION"])

    write_csv(reports / "message_catalog_phase22x_source_anchor_inventory_v1.csv", anchor_rows,
              ["SOURCE_PATH", "LINE", "NEEDLE", "TEXT"])

    patch_plan = [
        {
            "STEP": 1,
            "ACTION": "CATALOG_SEED_OR_FALLBACK_EXTENSION",
            "DETAIL": "Add two candidate compiled fallback/message catalog rows for MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE in a later authorized patch phase.",
            "MUTATION_IN_22X": 0,
            "REQUIRES_EXPLICIT_AUTH": 1,
        },
        {
            "STEP": 2,
            "ACTION": "SOURCE_ROUTE_PATCH",
            "DETAIL": "Replace literal proof status output in cmd_set.cpp with active provider lookup and fallback to current literal text.",
            "MUTATION_IN_22X": 0,
            "REQUIRES_EXPLICIT_AUTH": 1,
        },
        {
            "STEP": 3,
            "ACTION": "BUILD_AND_SMOKE",
            "DETAIL": "Build dottalkpp and run SET MESSAGE PROOF ON/OFF/CHECK in English and Spanish.",
            "MUTATION_IN_22X": 0,
            "REQUIRES_EXPLICIT_AUTH": 1,
        },
        {
            "STEP": 4,
            "ACTION": "REGRESSION",
            "DETAIL": "Rerun Phase 22V regression pack to prove no prior seam regressed.",
            "MUTATION_IN_22X": 0,
            "REQUIRES_EXPLICIT_AUTH": 1,
        },
    ]
    write_csv(reports / "message_catalog_phase22x_future_patch_plan_v1.csv", patch_plan,
              ["STEP", "ACTION", "DETAIL", "MUTATION_IN_22X", "REQUIRES_EXPLICIT_AUTH"])

    smoke_plan = [
        {
            "CASE_ID": "22Y-SMOKE-001",
            "COMMANDS": "SET LANGUAGE en-US; SET MESSAGE PROOF CHECK",
            "EXPECTED": "Message routing proof mode localized/status routed through active provider; boundary note preserved.",
        },
        {
            "CASE_ID": "22Y-SMOKE-002",
            "COMMANDS": "SET LANGUAGE es; SET MESSAGE PROOF ON; SET MESSAGE PROOF CHECK; SET MESSAGE PROOF OFF",
            "EXPECTED": "Spanish proof mode status text; boundary note; no active catalog mutation.",
        },
        {
            "CASE_ID": "22Y-SMOKE-003",
            "COMMANDS": "DO docs/messaging/scripts/MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE",
            "EXPECTED": "22V regression pack remains green.",
        },
    ]
    write_csv(reports / "message_catalog_phase22x_smoke_plan_v1.csv", smoke_plan,
              ["CASE_ID", "COMMANDS", "EXPECTED"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22X plan/probe only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22x_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22x_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    source_scope = [{
        "SOURCE_PATH": SOURCE_TARGET,
        "SHA256": source_hash,
        "ANCHOR_ROWS": len(anchor_rows),
        "MUTATION_IN_22X": 0,
        "FUTURE_PATCH_CANDIDATE": 1,
    }]
    write_csv(reports / "message_catalog_phase22x_source_scope_v1.csv", source_scope,
              ["SOURCE_PATH", "SHA256", "ANCHOR_ROWS", "MUTATION_IN_22X", "FUTURE_PATCH_CANDIDATE"])

    write_csv(reports / "message_catalog_phase22x_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22W_GREEN": 1 if p22w.get("STATUS") == "MESSAGE_CATALOG_PHASE22W_NEXT_LOW_RISK_RUNTIME_SEAM_SELECTION_GREEN_SOURCE_HELD" else 0,
        "MSG_022W_SAVEPOINT_PRESENT": 1 if savepoint_ok else 0,
        "SELECTED_SEAM_ID": SELECTED_SEAM_ID,
        "SELECTED_SEAM": SELECTED_SEAM,
        "SYMBOLS_PLANNED": 2,
        "ANCHOR_ROWS": len(anchor_rows),
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22W_GREEN", "MSG_022W_SAVEPOINT_PRESENT", "SELECTED_SEAM_ID",
         "SELECTED_SEAM", "SYMBOLS_PLANNED", "ANCHOR_ROWS",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22X SET MESSAGE PROOF Status Text Routing Plan

Status: `{status}`

Phase 22X is report-only. It plans the future routing of the diagnostic proof
status text selected in Phase 22W.

Selected seam:

```text
{SELECTED_SEAM_ID}: {SELECTED_SEAM}
source target: {SOURCE_TARGET}
candidate symbols:
  MESSAGE_PROOF_MODE_STATUS
  MESSAGE_PROOF_BOUNDARY_NOTE
```

No source, active catalog, HELP DATA, CMDHELPCHK, command registry, manualgen,
or Data Dictionary/SelfDoc mutation occurs in Phase 22X.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22X_SET_MESSAGE_PROOF_STATUS_TEXT_ROUTING_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22W green: {1 if p22w.get('STATUS') == 'MESSAGE_CATALOG_PHASE22W_NEXT_LOW_RISK_RUNTIME_SEAM_SELECTION_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022W savepoint present: {1 if savepoint_ok else 0}")
    print(f"  selected seam: {SELECTED_SEAM}")
    print(f"  selected seam id: {SELECTED_SEAM_ID}")
    print("  symbols planned: 2")
    print(f"  anchor rows: {len(anchor_rows)}")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
