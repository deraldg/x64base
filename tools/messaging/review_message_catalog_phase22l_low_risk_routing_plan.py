#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22L_LOW_RISK_RUNTIME_MESSAGE_ROUTING_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22L_LOW_RISK_RUNTIME_MESSAGE_ROUTING_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22M_LOW_RISK_SET_LANGUAGE_RUNTIME_ROUTING_PATCH"
REPORT_DIR = Path("docs/messaging/reports")

SOURCE_SCAN_PATHS = [
    "src/cli/cmd_set.cpp",
    "src/help/message_catalog.cpp",
    "src/help/message_catalog.hpp",
    "src/help/helpdata_messages.cpp",
    "src/cli/command_output.cpp",
    "src/cli/cmd_help.cpp",
    "src/cli/cmd_display.cpp",
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

def scan_source(repo: Path):
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
            "HAS_SET_LANGUAGE": 1 if "SET LANGUAGE" in upper or 'OPT == "LANGUAGE"' in upper else 0,
            "HAS_MESSAGE_LOCALE_SET": 1 if "MESSAGE_LOCALE_SET" in upper else 0,
            "HAS_HELP_HINT_COMMAND": 1 if "HELP_HINT_COMMAND" in upper else 0,
            "HAS_FORMAT_MESSAGE": 1 if "FORMAT_MESSAGE(" in upper else 0,
            "HAS_FORMAT_MESSAGE_CATALOG": 1 if "FORMAT_MESSAGE_CATALOG" in upper else 0,
            "HAS_ACTIVE_PROVIDER_STATUS": 1 if "ACTIVE_MESSAGE_CATALOG_STATUS" in upper else 0,
            "HAS_OUTPUT_ROUTER": 1 if "OUTPUTROUTER" in upper or "OUTPUT_ROUTER" in upper else 0,
        })
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22k = first_row(reports / "message_catalog_phase22k_runtime_status_summary_v1.csv")
    messages = p22k.get("MESSAGES", "12")
    text_rows = p22k.get("TEXT_ROWS", "60")
    locales = p22k.get("LOCALES", "de;en-US;es;fr;it")

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

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22K_PLACEHOLDER_SUBSTITUTION_GREEN",
         p22k.get("STATUS") == "MESSAGE_CATALOG_PHASE22K_CONTROLLED_PLACEHOLDER_SUBSTITUTION_SMOKE_GREEN",
         p22k.get("STATUS", ""))
    gate("MSG_022K_SAVEPOINT_PRESENT",
         latest.get("savepoint_id") == "MSG-022K" or "MSG-022K" in journal_text,
         latest.get("savepoint_id", ""))
    gate("CMD_SET_CPP_PRESENT", (repo / "src/cli/cmd_set.cpp").exists(), "src/cli/cmd_set.cpp")
    gate("MESSAGE_PROVIDER_PRESENT", (repo / "src/help/message_catalog.cpp").exists(), "src/help/message_catalog.cpp")
    review("CENTRAL_OUTPUT_ROUTER_PRESENT",
           (repo / "src/cli/command_output.cpp").exists(),
           "central output path exists but is intentionally not selected for first real routing patch")

    source_rows = scan_source(repo)
    write_csv(reports / "message_catalog_phase22l_source_scan_v1.csv", source_rows,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "HAS_SET_LANGUAGE",
               "HAS_MESSAGE_LOCALE_SET", "HAS_HELP_HINT_COMMAND", "HAS_FORMAT_MESSAGE",
               "HAS_FORMAT_MESSAGE_CATALOG", "HAS_ACTIVE_PROVIDER_STATUS",
               "HAS_OUTPUT_ROUTER"])

    seam_rows = [
        {
            "SEAM_ID": "RT-001",
            "SEAM": "SET LANGUAGE / SET LOCALE status output",
            "SOURCE_PATH": "src/cli/cmd_set.cpp",
            "SYMBOL": "MESSAGE_LOCALE_SET",
            "RISK": "LOW",
            "SELECTED_FOR_NEXT_PATCH": 1,
            "RATIONALE": "This is already a Messaging-owned command surface, already locale-aware, and narrow enough to route through active provider with compiled fallback.",
            "PATCH_RECOMMENDATION": "Route SET LANGUAGE success/status message through active DBF-backed provider first, preserving existing compiled behavior as fallback."
        },
        {
            "SEAM_ID": "RT-002",
            "SEAM": "HELP hint command output",
            "SOURCE_PATH": "src/cli/cmd_help.cpp or existing HELP output path",
            "SYMBOL": "HELP_HINT_COMMAND",
            "RISK": "MEDIUM",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "HELP paths may interact with HELP DATA and CMDHELPCHK expectations.",
            "PATCH_RECOMMENDATION": "Defer until after first SET LANGUAGE routing proof."
        },
        {
            "SEAM_ID": "RT-003",
            "SEAM": "Command output router / central emission path",
            "SOURCE_PATH": "src/cli/command_output.cpp",
            "SYMBOL": "multiple",
            "RISK": "HIGH",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Central routing can affect many commands at once and is too broad for first production routing.",
            "PATCH_RECOMMENDATION": "Do not patch in Phase 22M."
        },
        {
            "SEAM_ID": "RT-004",
            "SEAM": "HELP DATA / CMDHELPCHK consumer surfaces",
            "SOURCE_PATH": "dottalkpp/data/help and CMDHELPCHK lanes",
            "SYMBOL": "multiple",
            "RISK": "HIGH_PROTECTED",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Protected validation lanes with independent mutation gates.",
            "PATCH_RECOMMENDATION": "No HELP DATA or CMDHELPCHK mutation in Phase 22M."
        },
        {
            "SEAM_ID": "RT-005",
            "SEAM": "Manualgen / Data Dictionary localization consumers",
            "SOURCE_PATH": "docs/manuals and docs/datadict lanes",
            "SYMBOL": "future",
            "RISK": "MEDIUM_DEFERRED",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Integration is important, but manuals/datadict should consume the shared locale/message infrastructure after runtime routing contracts stabilize.",
            "PATCH_RECOMMENDATION": "No manualgen/datadict mutation in Phase 22M."
        },
    ]
    write_csv(reports / "message_catalog_phase22l_candidate_runtime_seams_v1.csv", seam_rows,
              ["SEAM_ID", "SEAM", "SOURCE_PATH", "SYMBOL", "RISK",
               "SELECTED_FOR_NEXT_PATCH", "RATIONALE", "PATCH_RECOMMENDATION"])

    selected_plan = [
        {
            "PLAN_ID": "22M-001",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "ACTION": "ROUTE_SET_LANGUAGE_STATUS_THROUGH_ACTIVE_PROVIDER",
            "SYMBOL": "MESSAGE_LOCALE_SET",
            "DETAIL": "Use active DBF-backed provider for SET LANGUAGE success/status emission when active catalog is loaded; preserve compiled/static fallback if provider unavailable.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22M-002",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "ACTION": "PRESERVE_COMPILED_FALLBACK",
            "SYMBOL": "MESSAGE_LOCALE_SET",
            "DETAIL": "If active provider is unavailable or lookup returns empty, retain existing compiled/localized status output.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22M-003",
            "TARGET_PATH": "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22M_SET_LANGUAGE_ROUTING_SMOKE.dts",
            "ACTION": "CREATE_RUNTIME_SMOKE",
            "SYMBOL": "MESSAGE_LOCALE_SET",
            "DETAIL": "Smoke should run SET LANGUAGE es and verify active_dbf-backed routing proof without broad command-output routing.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22M-004",
            "TARGET_PATH": "tools/messaging/*phase22m*",
            "ACTION": "CREATE_VALIDATOR_AND_SAVEPOINT",
            "SYMBOL": "MESSAGE_LOCALE_SET",
            "DETAIL": "Validate active routing proof, fallback boundary, no writeback, and no HELP/CMDHELPCHK/manualgen/datadict mutation.",
            "AUTHORIZED_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22l_selected_runtime_routing_plan_v1.csv", selected_plan,
              ["PLAN_ID", "TARGET_PATH", "ACTION", "SYMBOL", "DETAIL", "AUTHORIZED_NOW"])

    proof_requirements = [
        {"PROOF_ID": "P22M-001", "REQUIREMENT": "SET LANGUAGE es still succeeds", "EXPECTED": "Spanish/localized language status message remains visible."},
        {"PROOF_ID": "P22M-002", "REQUIREMENT": "Active provider routing is explicitly reported by smoke", "EXPECTED": "Runtime smoke reports provider mode active_dbf and symbol MESSAGE_LOCALE_SET."},
        {"PROOF_ID": "P22M-003", "REQUIREMENT": "Compiled fallback remains available", "EXPECTED": "Patch must not remove existing compiled/static message behavior."},
        {"PROOF_ID": "P22M-004", "REQUIREMENT": "No broad command-output routing", "EXPECTED": "Only the SET LANGUAGE status seam is patched."},
        {"PROOF_ID": "P22M-005", "REQUIREMENT": "No protected-system mutation", "EXPECTED": "No active DBF/CDX/LMDB writeback, HELP DATA, CMDHELPCHK, manualgen, or datadict mutation."},
    ]
    write_csv(reports / "message_catalog_phase22l_phase22m_proof_requirements_v1.csv",
              proof_requirements,
              ["PROOF_ID", "REQUIREMENT", "EXPECTED"])

    risk_rows = [
        {"RISK_ID": "RISK-001", "RISK": "Routing a real command message may change existing output wording.", "MITIGATION": "Choose SET LANGUAGE only; preserve compiled fallback and validate output shape."},
        {"RISK_ID": "RISK-002", "RISK": "Provider lookup may be unavailable in some deployments.", "MITIGATION": "Patch must fallback to compiled/static message path if active provider is unavailable or empty."},
        {"RISK_ID": "RISK-003", "RISK": "Command-output router patch would be too broad.", "MITIGATION": "Do not touch central output routing in Phase 22M."},
        {"RISK_ID": "RISK-004", "RISK": "HELP/CMDHELPCHK/manualgen/datadict integration pressure could expand scope.", "MITIGATION": "Keep Phase 22M source scope limited to cmd_set.cpp; record integrations for later phases."},
    ]
    write_csv(reports / "message_catalog_phase22l_risk_register_v1.csv",
              risk_rows,
              ["RISK_ID", "RISK", "MITIGATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22L report-only plan; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation; future consumer need recorded only."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation; future consumer need recorded only."},
    ]
    write_csv(reports / "message_catalog_phase22l_boundary_ledger_v1.csv",
              boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22l_gate_check_v1.csv",
              gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22l_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SELECTED_SEAM": "RT-001 SET LANGUAGE / SET LOCALE status output",
        "SELECTED_SYMBOL": "MESSAGE_LOCALE_SET",
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SELECTED_SEAM", "SELECTED_SYMBOL", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22L Low-Risk Runtime Message Routing Plan

Status: `{status}`

Phase 22L is report-only. It selects the first real runtime message seam after
the diagnostic `SET MESSAGE EMIT` path proved locale state and placeholder
substitution.

## Selected seam

`SET LANGUAGE / SET LOCALE` status output in `src/cli/cmd_set.cpp`.

## Selected symbol

`MESSAGE_LOCALE_SET`

## Why this seam

It is owned by the Messaging/locale command surface, already locale-aware, and
narrow enough to route through the active provider without touching central
command output, HELP DATA, CMDHELPCHK, manualgen, or Data Dictionary/SelfDoc.

## Next patch gate

`{NEXT_GATE}`

Phase 22M should be a guarded source patch, limited to `src/cli/cmd_set.cpp`, with
compiled fallback preserved.
"""
    (reports / "MESSAGE_CATALOG_PHASE22L_LOW_RISK_RUNTIME_MESSAGE_ROUTING_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  selected seam: RT-001 SET LANGUAGE / SET LOCALE status output")
    print("  selected symbol: MESSAGE_LOCALE_SET")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
