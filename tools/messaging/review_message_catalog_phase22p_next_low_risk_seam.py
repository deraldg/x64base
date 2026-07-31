#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22P_NEXT_LOW_RISK_ROUTING_SEAM_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22P_NEXT_LOW_RISK_ROUTING_SEAM_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22Q_UNSUPPORTED_LOCALE_RUNTIME_ROUTING_PATCH"
REPORT_DIR = Path("docs/messaging/reports")

SOURCE_SCAN_PATHS = [
    "src/cli/cmd_set.cpp",
    "src/help/message_catalog.cpp",
    "src/help/message_catalog.hpp",
    "src/help/helpdata_messages.cpp",
    "src/cli/command_output.cpp",
    "src/cli/cmd_help.cpp",
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
            "HAS_SET_LANGUAGE": 1 if "SET LANGUAGE" in upper or 'OPT == "LANGUAGE"' in upper else 0,
            "HAS_MESSAGE_LOCALE_SET": 1 if "MESSAGE_LOCALE_SET" in upper else 0,
            "HAS_UNSUPPORTED_MESSAGE_LOCALE": 1 if "UNSUPPORTED_MESSAGE_LOCALE" in upper else 0,
            "HAS_HELP_HINT_COMMAND": 1 if "HELP_HINT_COMMAND" in upper else 0,
            "HAS_MESSAGE_PROOF": 1 if "SET MESSAGE PROOF" in upper or "MESSAGE_ROUTING_PROOF_ENABLED" in upper else 0,
            "HAS_FORMAT_MESSAGE_CATALOG": 1 if "FORMAT_MESSAGE_CATALOG" in upper else 0,
            "HAS_ACTIVE_PROVIDER_STATUS": 1 if "ACTIVE_MESSAGE_CATALOG_STATUS" in upper else 0,
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

    p22o = first_row(reports / "message_catalog_phase22o_runtime_status_summary_v1.csv")
    messages = p22o.get("MESSAGES", "12")
    text_rows = p22o.get("TEXT_ROWS", "60")
    locales = p22o.get("LOCALES", "de;en-US;es;fr;it")

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
    cmd_set_row = next((r for r in source_rows if r["SOURCE_PATH"] == "src/cli/cmd_set.cpp"), {})

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22O_GATED_PROOF_LANE_GREEN",
         p22o.get("STATUS") == "MESSAGE_CATALOG_PHASE22O_GATED_ROUTING_PROOF_LANE_SMOKE_GREEN",
         p22o.get("STATUS", ""))
    gate("MSG_022O_SAVEPOINT_PRESENT",
         latest.get("savepoint_id") == "MSG-022O" or "MSG-022O" in journal_text,
         latest.get("savepoint_id", ""))
    gate("CMD_SET_CPP_PRESENT",
         cmd_set_row.get("EXISTS") == 1,
         "src/cli/cmd_set.cpp")
    gate("UNSUPPORTED_MESSAGE_LOCALE_SYMBOL_VISIBLE",
         any(r.get("HAS_UNSUPPORTED_MESSAGE_LOCALE") == 1 for r in source_rows),
         "UNSUPPORTED_MESSAGE_LOCALE")
    gate("PROOF_LANE_GATED",
         p22o.get("PROOF_LANE_GATED") == "1",
         p22o.get("PROOF_LANE_GATED", ""))
    review("NEXT_SEAM_POLICY",
           True,
           "Choose another narrow Messaging-owned SET LANGUAGE seam before touching HELP, central output routing, manualgen, or Data Dictionary.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22p_source_scan_v1.csv",
              source_rows,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "HAS_SET_LANGUAGE",
               "HAS_MESSAGE_LOCALE_SET", "HAS_UNSUPPORTED_MESSAGE_LOCALE",
               "HAS_HELP_HINT_COMMAND", "HAS_MESSAGE_PROOF",
               "HAS_FORMAT_MESSAGE_CATALOG", "HAS_ACTIVE_PROVIDER_STATUS",
               "HAS_CMDHELPCHK"])

    candidate_rows = [
        {
            "SEAM_ID": "RT-006",
            "SEAM": "SET LANGUAGE unsupported locale rejection/status",
            "SOURCE_PATH": "src/cli/cmd_set.cpp",
            "SYMBOL": "UNSUPPORTED_MESSAGE_LOCALE",
            "RISK": "LOW",
            "SELECTED_FOR_NEXT_PATCH": 1,
            "RATIONALE": "Messaging-owned SET LANGUAGE path, narrow error/status output, useful for proving active-provider routing on non-success path while preserving fallback.",
            "PATCH_RECOMMENDATION": "Route unsupported locale message through active provider with compiled fallback; keep proof line gated by SET MESSAGE PROOF."
        },
        {
            "SEAM_ID": "RT-007",
            "SEAM": "HELP hint command actual HELP path",
            "SOURCE_PATH": "src/cli/cmd_help.cpp or HELP output path",
            "SYMBOL": "HELP_HINT_COMMAND",
            "RISK": "MEDIUM",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Already proven diagnostically, but actual HELP paths may interact with HELP DATA and CMDHELPCHK expectations.",
            "PATCH_RECOMMENDATION": "Defer until unsupported-locale error/status routing is proven."
        },
        {
            "SEAM_ID": "RT-008",
            "SEAM": "SET MESSAGE CATALOG CHECK provider status output",
            "SOURCE_PATH": "src/cli/cmd_set.cpp",
            "SYMBOL": "provider_status_future",
            "RISK": "LOW_MEDIUM",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "It is still a diagnostic surface; useful but less representative than a real user-facing error/status message.",
            "PATCH_RECOMMENDATION": "Keep as diagnostic, do not prioritize as next real routed message."
        },
        {
            "SEAM_ID": "RT-009",
            "SEAM": "Central command output router",
            "SOURCE_PATH": "src/cli/command_output.cpp",
            "SYMBOL": "multiple",
            "RISK": "HIGH",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Too broad; could change many commands at once.",
            "PATCH_RECOMMENDATION": "Do not patch until several narrow seams are proven."
        },
        {
            "SEAM_ID": "RT-010",
            "SEAM": "Manualgen/Data Dictionary/HELP consumers",
            "SOURCE_PATH": "docs/manuals, docs/datadict, HELP DATA",
            "SYMBOL": "future",
            "RISK": "DEFERRED_INTEGRATION",
            "SELECTED_FOR_NEXT_PATCH": 0,
            "RATIONALE": "Important integration consumers, but should not drive runtime command-routing patch order.",
            "PATCH_RECOMMENDATION": "Keep recorded as downstream consumers; no mutation in Phase 22Q."
        },
    ]
    write_csv(reports / "message_catalog_phase22p_candidate_runtime_seams_v1.csv",
              candidate_rows,
              ["SEAM_ID", "SEAM", "SOURCE_PATH", "SYMBOL", "RISK",
               "SELECTED_FOR_NEXT_PATCH", "RATIONALE", "PATCH_RECOMMENDATION"])

    selected_plan = [
        {
            "PLAN_ID": "22Q-001",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "ACTION": "ROUTE_UNSUPPORTED_LOCALE_MESSAGE_THROUGH_ACTIVE_PROVIDER",
            "SYMBOL": "UNSUPPORTED_MESSAGE_LOCALE",
            "DETAIL": "When SET LANGUAGE receives unsupported locale, emit active-provider message if available; preserve compiled/static fallback if provider unavailable or lookup empty.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22Q-002",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "ACTION": "PRESERVE_GATED_PROOF_LANE",
            "SYMBOL": "UNSUPPORTED_MESSAGE_LOCALE",
            "DETAIL": "When SET MESSAGE PROOF ON is active, emit proof line for UNSUPPORTED_MESSAGE_LOCALE routing; otherwise keep user output quiet.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22Q-003",
            "TARGET_PATH": "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22Q_UNSUPPORTED_LOCALE_ROUTING_SMOKE.dts",
            "ACTION": "CREATE_RUNTIME_SMOKE",
            "SYMBOL": "UNSUPPORTED_MESSAGE_LOCALE",
            "DETAIL": "Smoke should prove unsupported locale message routed through active DBF provider with proof mode on, and no proof line with proof mode off.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PLAN_ID": "22Q-004",
            "TARGET_PATH": "tools/messaging/*phase22q*",
            "ACTION": "CREATE_VALIDATOR_AND_SAVEPOINT",
            "SYMBOL": "UNSUPPORTED_MESSAGE_LOCALE",
            "DETAIL": "Validate active routing proof, fallback boundary, no writeback, and no HELP/CMDHELPCHK/manualgen/datadict mutation.",
            "AUTHORIZED_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22p_selected_runtime_routing_plan_v1.csv",
              selected_plan,
              ["PLAN_ID", "TARGET_PATH", "ACTION", "SYMBOL", "DETAIL", "AUTHORIZED_NOW"])

    proof_requirements = [
        {"PROOF_ID": "22Q-P1", "REQUIREMENT": "Unsupported locale path remains functional", "EXPECTED": "SET LANGUAGE xx emits unsupported-locale message and does not corrupt current locale state."},
        {"PROOF_ID": "22Q-P2", "REQUIREMENT": "Active provider routing proof can be shown", "EXPECTED": "With SET MESSAGE PROOF ON, output contains Message routing proof: active_dbf UNSUPPORTED_MESSAGE_LOCALE."},
        {"PROOF_ID": "22Q-P3", "REQUIREMENT": "Proof lane remains gated", "EXPECTED": "With proof mode off, unsupported-locale message appears without proof line."},
        {"PROOF_ID": "22Q-P4", "REQUIREMENT": "Compiled fallback remains available", "EXPECTED": "Patch leaves existing unsupported-locale fallback path below/available."},
        {"PROOF_ID": "22Q-P5", "REQUIREMENT": "No protected-system mutation", "EXPECTED": "No active DBF/CDX/LMDB writeback, HELP DATA, CMDHELPCHK, manualgen, or datadict mutation."},
    ]
    write_csv(reports / "message_catalog_phase22p_phase22q_proof_requirements_v1.csv",
              proof_requirements,
              ["PROOF_ID", "REQUIREMENT", "EXPECTED"])

    risk_rows = [
        {"RISK_ID": "RISK-001", "RISK": "Unsupported-locale message may include placeholder names not yet fully contracted.", "MITIGATION": "Route only if active-provider lookup returns text; keep literal placeholders if substitution is not yet needed; preserve fallback."},
        {"RISK_ID": "RISK-002", "RISK": "Invalid SET LANGUAGE smoke may leave runtime state ambiguous.", "MITIGATION": "Smoke should set a known valid locale first and verify invalid locale does not break provider status."},
        {"RISK_ID": "RISK-003", "RISK": "Proof-line gating could regress while adding second routed seam.", "MITIGATION": "Phase 22Q validator must check proof line appears only when proof mode is on."},
        {"RISK_ID": "RISK-004", "RISK": "Pressure to patch HELP next is understandable but premature.", "MITIGATION": "Prove one success path and one rejection/error path before moving to HELP surfaces."},
    ]
    write_csv(reports / "message_catalog_phase22p_risk_register_v1.csv",
              risk_rows,
              ["RISK_ID", "RISK", "MITIGATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22P report-only next-seam plan; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation; future consumer need recorded only."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation; future consumer need recorded only."},
    ]
    write_csv(reports / "message_catalog_phase22p_boundary_ledger_v1.csv",
              boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22p_gate_check_v1.csv",
              gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22p_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SELECTED_SEAM": "RT-006 SET LANGUAGE unsupported locale rejection/status",
        "SELECTED_SYMBOL": "UNSUPPORTED_MESSAGE_LOCALE",
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SELECTED_SEAM", "SELECTED_SYMBOL", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22P Next Low-Risk Routing Seam Plan

Status: `{status}`

Phase 22P is report-only. It selects the next low-risk runtime message routing
seam after Phase 22O gated the routing proof lane.

## Selected next seam

`SET LANGUAGE` unsupported-locale rejection/status path.

## Selected symbol

`UNSUPPORTED_MESSAGE_LOCALE`

## Why this seam

It is still inside the Messaging-owned `SET LANGUAGE` command surface. It proves
a rejection/error-status path before we move into HELP, central output routing,
manualgen, or Data Dictionary consumers.

## Next gate

`{NEXT_GATE}`

Phase 22Q should be a guarded source patch limited to `src/cli/cmd_set.cpp`.
It must preserve compiled fallback and keep the proof line gated.
"""
    (reports / "MESSAGE_CATALOG_PHASE22P_NEXT_LOW_RISK_ROUTING_SEAM_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  selected seam: RT-006 SET LANGUAGE unsupported locale rejection/status")
    print("  selected symbol: UNSUPPORTED_MESSAGE_LOCALE")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
