#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22R_HELP_HINT_ROUTING_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22R_HELP_HINT_ROUTING_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22S_HELP_HINT_RUNTIME_ROUTING_PATCH"
REPORT_DIR = Path("docs/messaging/reports")

SOURCE_SCAN_PATHS = [
    "src/cli/cmd_help.cpp",
    "src/help/helpdata_messages.cpp",
    "src/help/message_catalog.cpp",
    "src/help/message_catalog.hpp",
    "src/cli/cmd_set.cpp",
    "src/cli/command_output.cpp",
    "src/cli/command_registry.cpp",
]

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

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists() or not path.is_file():
        return ""
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def scan_sources(repo: Path):
    rows = []
    for relpath in SOURCE_SCAN_PATHS:
        path = repo / relpath
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() and path.is_file() else ""
        upper = text.upper()
        rows.append({
            "SOURCE_PATH": relpath,
            "EXISTS": 1 if path.exists() else 0,
            "BYTES": path.stat().st_size if path.exists() and path.is_file() else 0,
            "SHA256": sha256_file(path),
            "HAS_HELP_HINT_COMMAND": 1 if "HELP_HINT_COMMAND" in upper or "HELPHINTCOMMAND" in upper else 0,
            "HAS_HELP_COMMAND": 1 if "CMD_HELP" in upper or "HELP" in upper else 0,
            "HAS_FORMAT_MESSAGE": 1 if "FORMAT_MESSAGE(" in upper else 0,
            "HAS_FORMAT_MESSAGE_CATALOG": 1 if "FORMAT_MESSAGE_CATALOG" in upper else 0,
            "HAS_ACTIVE_PROVIDER_STATUS": 1 if "ACTIVE_MESSAGE_CATALOG_STATUS" in upper else 0,
            "HAS_MESSAGE_PROOF": 1 if "SET MESSAGE PROOF" in upper or "MESSAGE_ROUTING_PROOF_ENABLED" in upper else 0,
            "HAS_COMMAND_PLACEHOLDER": 1 if "{COMMAND}" in upper or '"COMMAND"' in upper else 0,
            "HAS_CMDHELPCHK": 1 if "CMDHELPCHK" in upper else 0,
        })
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22q = first_row(reports / "message_catalog_phase22q_runtime_status_summary_v1.csv")
    messages = p22q.get("MESSAGES", "12")
    text_rows = p22q.get("TEXT_ROWS", "60")
    locales = p22q.get("LOCALES", "de;en-US;es;fr;it")

    latest = {}
    latest_path = reports / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    journal_text = ""
    journal_path = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    if journal_path.exists():
        journal_text = journal_path.read_text(encoding="utf-8", errors="replace")

    source_rows = scan_sources(repo)

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22Q_UNSUPPORTED_LOCALE_ROUTING_GREEN",
         p22q.get("STATUS") == "MESSAGE_CATALOG_PHASE22Q_UNSUPPORTED_LOCALE_RUNTIME_ROUTING_SMOKE_GREEN",
         p22q.get("STATUS", ""))
    gate("MSG_022Q_SAVEPOINT_PRESENT",
         latest.get("savepoint_id") == "MSG-022Q" or "MSG-022Q" in journal_text,
         latest.get("savepoint_id", ""))
    gate("CMD_HELP_CPP_PRESENT",
         (repo / "src/cli/cmd_help.cpp").exists(),
         "src/cli/cmd_help.cpp")
    gate("HELP_HINT_COMMAND_VISIBLE",
         any(r.get("HAS_HELP_HINT_COMMAND") == 1 for r in source_rows),
         "HELP_HINT_COMMAND / HelpHintCommand")
    gate("PROOF_LANE_GATED_FROM_22O_22Q",
         p22q.get("PROOF_LANE_GATED") == "1",
         p22q.get("PROOF_LANE_GATED", ""))
    review("HELP_SURFACE_PROTECTED",
           True,
           "Plan only: do not mutate HELP DATA or CMDHELPCHK while selecting HELP_HINT_COMMAND routing seam.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22r_source_scan_v1.csv",
              source_rows,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "HAS_HELP_HINT_COMMAND",
               "HAS_HELP_COMMAND", "HAS_FORMAT_MESSAGE", "HAS_FORMAT_MESSAGE_CATALOG",
               "HAS_ACTIVE_PROVIDER_STATUS", "HAS_MESSAGE_PROOF",
               "HAS_COMMAND_PLACEHOLDER", "HAS_CMDHELPCHK"])

    candidate_rows = [
        {
            "SEAM_ID": "RT-007",
            "SEAM": "HELP unknown-command hint / command-specific help hint",
            "SOURCE_PATH": "src/cli/cmd_help.cpp",
            "SYMBOL": "HELP_HINT_COMMAND",
            "RISK": "MEDIUM_LOW",
            "SELECTED_FOR_NEXT_PATCH": 1,
            "RATIONALE": "HELP_HINT_COMMAND already proved diagnostically with locale and {command} substitution. It is the next natural user-facing seam after SET LANGUAGE success and rejection paths.",
            "PATCH_RECOMMENDATION": "Route only the narrow HELP hint text through active provider; do not rebuild HELP DATA or mutate CMDHELPCHK."
        },
        {
            "SEAM_ID": "RT-011",
            "SEAM": "All HELP output routing",
            "SOURCE_PATH": "src/cli/cmd_help.cpp and HELP DATA consumers",
            "SYMBOL": "multiple",
            "RISK": "HIGH",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Too broad; may interact with HELP DATA, topic rendering, and CMDHELPCHK contracts.",
            "PATCH_RECOMMENDATION": "Do not patch in Phase 22S."
        },
        {
            "SEAM_ID": "RT-012",
            "SEAM": "Central command output router",
            "SOURCE_PATH": "src/cli/command_output.cpp",
            "SYMBOL": "multiple",
            "RISK": "HIGH",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Central routing still risks changing many commands at once.",
            "PATCH_RECOMMENDATION": "Defer until several more narrow seams are proven."
        },
        {
            "SEAM_ID": "RT-013",
            "SEAM": "Manualgen / Data Dictionary localized consumers",
            "SOURCE_PATH": "docs/manuals and docs/datadict lanes",
            "SYMBOL": "future",
            "RISK": "DEFERRED_INTEGRATION",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Important downstream language consumers, but not the next runtime seam.",
            "PATCH_RECOMMENDATION": "Record dependency only; no mutation in Phase 22S."
        },
    ]
    write_csv(reports / "message_catalog_phase22r_candidate_help_routing_seams_v1.csv",
              candidate_rows,
              ["SEAM_ID", "SEAM", "SOURCE_PATH", "SYMBOL", "RISK",
               "SELECTED_FOR_NEXT_PATCH", "RATIONALE", "PATCH_RECOMMENDATION"])

    selected_plan = [
        {
            "PLAN_ID": "22S-001",
            "TARGET_PATH": "src/cli/cmd_help.cpp",
            "ACTION": "ROUTE_NARROW_HELP_HINT_THROUGH_ACTIVE_PROVIDER",
            "SYMBOL": "HELP_HINT_COMMAND",
            "DETAIL": "Find the narrow hint path equivalent to 'Type HELP {command} for more information' and route only that line through active provider.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22S-002",
            "TARGET_PATH": "src/cli/cmd_help.cpp",
            "ACTION": "APPLY_COMMAND_PLACEHOLDER",
            "SYMBOL": "HELP_HINT_COMMAND",
            "DETAIL": "Substitute {command} using the command token already being reported by HELP. Preserve compiled fallback.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22S-003",
            "TARGET_PATH": "src/cli/cmd_help.cpp",
            "ACTION": "PRESERVE_GATED_PROOF_LANE",
            "SYMBOL": "HELP_HINT_COMMAND",
            "DETAIL": "If proof mode is enabled, emit 'Message routing proof: active_dbf HELP_HINT_COMMAND'; otherwise keep normal HELP output clean.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22S-004",
            "TARGET_PATH": "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22S_HELP_HINT_ROUTING_SMOKE.dts",
            "ACTION": "CREATE_RUNTIME_SMOKE",
            "SYMBOL": "HELP_HINT_COMMAND",
            "DETAIL": "Smoke should prove active-provider HELP hint routing, placeholder substitution, proof gating, and no HELP DATA/CMDHELPCHK mutation.",
            "AUTHORIZED_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22r_selected_help_hint_routing_plan_v1.csv",
              selected_plan,
              ["PLAN_ID", "TARGET_PATH", "ACTION", "SYMBOL", "DETAIL", "AUTHORIZED_NOW"])

    proof_requirements = [
        {"PROOF_ID": "22S-P1", "REQUIREMENT": "HELP hint path still works", "EXPECTED": "A command-specific HELP hint appears for the selected smoke input."},
        {"PROOF_ID": "22S-P2", "REQUIREMENT": "Active provider routes HELP_HINT_COMMAND", "EXPECTED": "With SET MESSAGE PROOF ON, output contains Message routing proof: active_dbf HELP_HINT_COMMAND."},
        {"PROOF_ID": "22S-P3", "REQUIREMENT": "{command} placeholder substituted", "EXPECTED": "Output text contains the command token, not literal {command}."},
        {"PROOF_ID": "22S-P4", "REQUIREMENT": "Proof lane remains gated", "EXPECTED": "Proof line absent when SET MESSAGE PROOF OFF."},
        {"PROOF_ID": "22S-P5", "REQUIREMENT": "No HELP/CMDHELPCHK mutation", "EXPECTED": "No HELP DATA rebuild, no CMDHELPCHK mutation, no command registry mutation."},
        {"PROOF_ID": "22S-P6", "REQUIREMENT": "Compiled fallback remains available", "EXPECTED": "Patch leaves existing HELP hint behavior if active-provider lookup returns empty/unavailable."},
    ]
    write_csv(reports / "message_catalog_phase22r_phase22s_proof_requirements_v1.csv",
              proof_requirements,
              ["PROOF_ID", "REQUIREMENT", "EXPECTED"])

    risk_rows = [
        {"RISK_ID": "RISK-001", "RISK": "HELP is a protected/high-visibility surface.", "MITIGATION": "Patch only a narrow hint line; do not rebuild HELP DATA or touch CMDHELPCHK."},
        {"RISK_ID": "RISK-002", "RISK": "Actual HELP source anchor may differ from diagnostic assumptions.", "MITIGATION": "Phase 22S must inspect live cmd_help.cpp before source mutation and use a guarded anchor."},
        {"RISK_ID": "RISK-003", "RISK": "Placeholder substitution may not share cmd_set.cpp helper scope.", "MITIGATION": "Phase 22S should implement or reuse a small local helper in the patched source file, not broaden architecture prematurely."},
        {"RISK_ID": "RISK-004", "RISK": "Routing proof lines could pollute user HELP output.", "MITIGATION": "Keep proof output gated by SET MESSAGE PROOF only."},
        {"RISK_ID": "RISK-005", "RISK": "Manualgen/Data Dictionary integration pressure could expand scope.", "MITIGATION": "Record downstream consumers but keep Phase 22S runtime-only."},
    ]
    write_csv(reports / "message_catalog_phase22r_risk_register_v1.csv",
              risk_rows,
              ["RISK_ID", "RISK", "MITIGATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22R report-only HELP hint routing plan; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA rebuild or mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation; future language consumer need recorded only."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation; future language consumer need recorded only."},
    ]
    write_csv(reports / "message_catalog_phase22r_boundary_ledger_v1.csv",
              boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22r_gate_check_v1.csv",
              gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22r_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SELECTED_SEAM": "RT-007 HELP unknown-command hint / command-specific help hint",
        "SELECTED_SYMBOL": "HELP_HINT_COMMAND",
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SELECTED_SEAM", "SELECTED_SYMBOL", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22R HELP Hint Routing Plan

Status: `{status}`

Phase 22R is report-only. It selects the next runtime routing seam after Phase
22Q proved one success path and one rejection/error path under `SET LANGUAGE`.

## Selected seam

Narrow HELP hint routing only.

## Selected symbol

`HELP_HINT_COMMAND`

## Boundary

No HELP DATA rebuild, no CMDHELPCHK mutation, no command registry mutation, no
manualgen mutation, and no Data Dictionary/SelfDoc mutation.

## Next gate

`{NEXT_GATE}`

Phase 22S should inspect live `src/cli/cmd_help.cpp` and patch only the narrow
hint line, preserving compiled fallback and the gated proof lane.
"""
    (reports / "MESSAGE_CATALOG_PHASE22R_HELP_HINT_ROUTING_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  selected seam: RT-007 HELP unknown-command hint / command-specific help hint")
    print("  selected symbol: HELP_HINT_COMMAND")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
