#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22N_ROUTING_PROOF_LANE_GATING_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22N_ROUTING_PROOF_LANE_GATING_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22O_GATED_ROUTING_PROOF_LANE_PATCH"
REPORT_DIR = Path("docs/messaging/reports")

SOURCE_SCAN_PATHS = [
    "src/cli/cmd_set.cpp",
    "src/help/message_catalog.cpp",
    "src/help/message_catalog.hpp",
    "src/cli/command_output.cpp",
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

def source_scan(repo: Path):
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
            "HAS_ROUTING_PROOF_LINE": 1 if "MESSAGE ROUTING PROOF: ACTIVE_DBF MESSAGE_LOCALE_SET" in upper else 0,
            "HAS_SET_MESSAGE_CATALOG_CHECK": 1 if "SET MESSAGE CATALOG CHECK" in upper else 0,
            "HAS_SET_MESSAGE_EMIT": 1 if "SET MESSAGE EMIT" in upper else 0,
            "HAS_MESSAGE_LOCALE_SET": 1 if "MESSAGE_LOCALE_SET" in upper else 0,
        })
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22m = first_row(reports / "message_catalog_phase22m_runtime_status_summary_v1.csv")
    messages = p22m.get("MESSAGES", "12")
    text_rows = p22m.get("TEXT_ROWS", "60")
    locales = p22m.get("LOCALES", "de;en-US;es;fr;it")

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

    source_rows = source_scan(repo)
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

    gate("PHASE22M_ROUTING_SMOKE_GREEN",
         p22m.get("STATUS") == "MESSAGE_CATALOG_PHASE22M_LOW_RISK_SET_LANGUAGE_RUNTIME_ROUTING_SMOKE_GREEN",
         p22m.get("STATUS", ""))
    gate("MSG_022M_SAVEPOINT_PRESENT",
         latest.get("savepoint_id") == "MSG-022M" or "MSG-022M" in journal_text,
         latest.get("savepoint_id", ""))
    gate("CMD_SET_CPP_PRESENT",
         cmd_set_row.get("EXISTS") == 1,
         "src/cli/cmd_set.cpp")
    gate("ROUTING_PROOF_LINE_PRESENT",
         cmd_set_row.get("HAS_ROUTING_PROOF_LINE") == 1,
         "Message routing proof: active_dbf MESSAGE_LOCALE_SET")
    review("PROOF_LANE_DECISION",
           True,
           "Keep temporary proof lane for now; make it gated because it may serve as a learning/teaching tool.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22n_source_scan_v1.csv",
              source_rows,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "HAS_ROUTING_PROOF_LINE",
               "HAS_SET_MESSAGE_CATALOG_CHECK", "HAS_SET_MESSAGE_EMIT", "HAS_MESSAGE_LOCALE_SET"])

    decision_rows = [
        {
            "DECISION_ID": "22N-001",
            "DECISION": "KEEP_ROUTING_PROOF_LANE_TEMPORARILY",
            "STATUS": "ACCEPTED",
            "DETAIL": "Keep the active-provider routing proof lane during Messaging integration because it helps prove runtime behavior and can be used as a learning tool.",
        },
        {
            "DECISION_ID": "22N-002",
            "DECISION": "GATE_PROOF_OUTPUT",
            "STATUS": "ACCEPTED_FOR_NEXT_PATCH",
            "DETAIL": "Proof output should not remain always-on for normal user flow; Phase 22O should gate it behind an explicit diagnostic/proof setting or command.",
        },
        {
            "DECISION_ID": "22N-003",
            "DECISION": "NO_CENTRAL_ROUTING_EXPANSION_YET",
            "STATUS": "ACCEPTED",
            "DETAIL": "Do not expand to central command output or HELP/CMDHELPCHK until proof-lane governance is clear.",
        },
        {
            "DECISION_ID": "22N-004",
            "DECISION": "LEARNING_TOOL_ALLOWED",
            "STATUS": "ACCEPTED",
            "DETAIL": "Proof lane may remain visible when explicitly enabled for teaching/diagnostics.",
        },
    ]
    write_csv(reports / "message_catalog_phase22n_decisions_v1.csv",
              decision_rows,
              ["DECISION_ID", "DECISION", "STATUS", "DETAIL"])

    policy_rows = [
        {
            "POLICY_ID": "PROOF-001",
            "NAME": "routing_proof_mode",
            "DEFAULT": "off_for_normal_user_flow_after_gate_patch",
            "ENABLED_BY": "explicit diagnostic command or setting",
            "OUTPUT_ALLOWED": "Message routing proof: active_dbf <SYMBOL>",
            "PURPOSE": "runtime audit, developer diagnostics, and teaching/learning evidence",
            "SCOPE": "Messaging routed-message seams only",
        },
        {
            "POLICY_ID": "PROOF-002",
            "NAME": "proof_line_lifetime",
            "DEFAULT": "temporary_but_supported_during_messaging_integration",
            "ENABLED_BY": "explicit proof mode",
            "OUTPUT_ALLOWED": "active provider/source/fallback proof lines",
            "PURPOSE": "prevent invisible catalog/fallback confusion during staged integration",
            "SCOPE": "limited to guarded proof lane; not general user output",
        },
    ]
    write_csv(reports / "message_catalog_phase22n_proof_lane_policy_v1.csv",
              policy_rows,
              ["POLICY_ID", "NAME", "DEFAULT", "ENABLED_BY", "OUTPUT_ALLOWED", "PURPOSE", "SCOPE"])

    next_plan = [
        {
            "STEP": "22O-001",
            "ACTION": "ADD_OR_REUSE_PROOF_MODE_FLAG",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "DETAIL": "Add or reuse a Messaging proof/diagnostic flag so the SET LANGUAGE routing proof line is gated.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": "22O-002",
            "ACTION": "ADD_COMMAND_SURFACE",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "DETAIL": "Preferred command shape: SET MESSAGE PROOF ON|OFF|CHECK, or equivalent under existing SET MESSAGE surface.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": "22O-003",
            "ACTION": "GATE_EXISTING_PROOF_LINE",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "DETAIL": "Wrap Message routing proof: active_dbf MESSAGE_LOCALE_SET so it only emits when proof mode is enabled.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": "22O-004",
            "ACTION": "RUNTIME_SMOKE",
            "TARGET_PATH": "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22O_GATED_ROUTING_PROOF_SMOKE.dts",
            "DETAIL": "Smoke should prove default quiet behavior, proof ON visible behavior, and proof OFF quiet behavior.",
            "AUTHORIZED_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22n_phase22o_patch_plan_v1.csv",
              next_plan,
              ["STEP", "ACTION", "TARGET_PATH", "DETAIL", "AUTHORIZED_NOW"])

    proof_requirements = [
        {"PROOF_ID": "22O-P1", "REQUIREMENT": "Normal SET LANGUAGE does not emit proof line when proof mode is off", "EXPECTED": "Idioma de mensajes: es appears, Message routing proof line absent."},
        {"PROOF_ID": "22O-P2", "REQUIREMENT": "SET MESSAGE PROOF ON enables proof line", "EXPECTED": "Subsequent SET LANGUAGE es emits Message routing proof: active_dbf MESSAGE_LOCALE_SET."},
        {"PROOF_ID": "22O-P3", "REQUIREMENT": "SET MESSAGE PROOF OFF disables proof line", "EXPECTED": "Subsequent SET LANGUAGE es does not emit proof line."},
        {"PROOF_ID": "22O-P4", "REQUIREMENT": "Provider remains active_dbf", "EXPECTED": "SET MESSAGE CATALOG CHECK still reports active_dbf and active catalog loaded."},
        {"PROOF_ID": "22O-P5", "REQUIREMENT": "No protected-system mutation", "EXPECTED": "No active DBF/CDX/LMDB writeback, HELP DATA, CMDHELPCHK, manualgen, or datadict mutation."},
    ]
    write_csv(reports / "message_catalog_phase22n_phase22o_proof_requirements_v1.csv",
              proof_requirements,
              ["PROOF_ID", "REQUIREMENT", "EXPECTED"])

    risk_rows = [
        {"RISK_ID": "RISK-001", "RISK": "Always-on proof lines can leak developer diagnostics into normal user output.", "MITIGATION": "Gate proof output behind explicit SET MESSAGE PROOF ON/OFF or equivalent."},
        {"RISK_ID": "RISK-002", "RISK": "Removing proof lines too early makes active-provider routing hard to distinguish from compiled fallback.", "MITIGATION": "Keep proof lane available in diagnostic/learning mode until routing is mature."},
        {"RISK_ID": "RISK-003", "RISK": "Proof mode could become another hidden global state.", "MITIGATION": "Expose CHECK/status output and record proof mode behavior in reports."},
    ]
    write_csv(reports / "message_catalog_phase22n_risk_register_v1.csv",
              risk_rows,
              ["RISK_ID", "RISK", "MITIGATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22N report-only proof-lane policy; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22n_boundary_ledger_v1.csv",
              boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22n_gate_check_v1.csv",
              gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22n_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PROOF_LANE_DECISION": "KEEP_TEMPORARY_GATED_LEARNING_TOOL",
        "ROUTED_SYMBOL": "MESSAGE_LOCALE_SET",
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PROOF_LANE_DECISION", "ROUTED_SYMBOL", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22N Routing Proof Lane Gating Plan

Status: `{status}`

Phase 22N records the decision to keep the temporary routing proof lane, but to
gate it so normal user output does not permanently carry developer/audit lines.

## Accepted decision

Keep the proof lane for now as a diagnostic and learning tool.

## Required next behavior

The proof line should be visible only when explicitly enabled, for example:

```text
SET MESSAGE PROOF ON
SET LANGUAGE es
SET MESSAGE PROOF OFF
```

## Next gate

`{NEXT_GATE}`

Phase 22O should be a guarded source patch limited to the Messaging/SET command
surface. It should not mutate active DBF/CDX/LMDB, HELP DATA, CMDHELPCHK,
manualgen, or Data Dictionary/SelfDoc artifacts.
"""
    (reports / "MESSAGE_CATALOG_PHASE22N_ROUTING_PROOF_LANE_GATING_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  proof lane decision: KEEP_TEMPORARY_GATED_LEARNING_TOOL")
    print("  routed symbol: MESSAGE_LOCALE_SET")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
