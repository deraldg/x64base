#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22I_A_CONTROLLED_RUNTIME_EMISSION_EXPANSION_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22I_A_CONTROLLED_RUNTIME_EMISSION_EXPANSION_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_PATCH"
REPORT_DIR = Path("docs/messaging/reports")

SOURCE_CANDIDATES = [
    "src/help/message_catalog.hpp",
    "src/help/message_catalog.cpp",
    "src/help/helpdata_messages.cpp",
    "src/help/helpdata_messages.hpp",
    "src/cli/cmd_set.cpp",
    "src/cli/command_output.cpp",
    "src/cli/cmd_display.cpp",
    "src/cli/command_registry.cpp",
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

def source_scan(repo: Path):
    rows = []
    for relpath in SOURCE_CANDIDATES:
        path = repo / relpath
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() and path.is_file() else ""
        upper = text.upper()
        rows.append({
            "SOURCE_PATH": relpath,
            "EXISTS": 1 if path.exists() else 0,
            "BYTES": path.stat().st_size if path.exists() and path.is_file() else 0,
            "SHA256": sha256_file(path),
            "HAS_FORMAT_MESSAGE_CATALOG": 1 if "FORMAT_MESSAGE_CATALOG" in upper else 0,
            "HAS_ACTIVE_MESSAGE_CATALOG_STATUS": 1 if "ACTIVE_MESSAGE_CATALOG_STATUS" in upper else 0,
            "HAS_SET_LANGUAGE": 1 if "SET LANGUAGE" in upper else 0,
            "HAS_OUTPUT_ROUTER": 1 if "OUTPUTROUTER" in upper or "OUTPUT_ROUTER" in upper else 0,
            "HAS_HELP_HINT_COMMAND": 1 if "HELP_HINT_COMMAND" in upper else 0,
            "HAS_MESSAGE_LOCALE_SET": 1 if "MESSAGE_LOCALE_SET" in upper else 0,
        })
    return rows

def contains_file(repo: Path, relpath: str, needle: str) -> bool:
    path = repo / relpath
    if not path.exists() or not path.is_file():
        return False
    return needle.upper() in path.read_text(encoding="utf-8", errors="replace").upper()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22h = first_row(reports / "message_catalog_phase22h_status_summary_v1.csv")
    p22g = first_row(reports / "message_catalog_phase22g_1_runtime_status_summary_v1.csv")

    latest = {}
    latest_path = reports / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
        except Exception:
            latest = {}

    messages = p22h.get("MESSAGES", p22g.get("MESSAGES", "12"))
    text_rows = p22h.get("TEXT_ROWS", p22g.get("TEXT_ROWS", "60"))
    locales = p22h.get("LOCALES", p22g.get("LOCALES", "de;en-US;es;fr;it"))

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name, ok, detail):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22H_CLOSEOUT_GREEN",
         p22h.get("STATUS") == "MESSAGE_CATALOG_PHASE22H_RUNTIME_MESSAGE_EMISSION_PILOT_CLOSEOUT_GREEN",
         p22h.get("STATUS", ""))
    gate("MSG_022H_SAVEPOINT_PRESENT",
         latest.get("savepoint_id") == "MSG-022H" or (repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md").exists() and "MSG-022H" in (repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md").read_text(encoding="utf-8", errors="replace"),
         latest.get("savepoint_id", ""))
    gate("MESSAGE_PROVIDER_HEADER_PRESENT", (repo / "src/help/message_catalog.hpp").exists(), "src/help/message_catalog.hpp")
    gate("MESSAGE_PROVIDER_CPP_PRESENT", (repo / "src/help/message_catalog.cpp").exists(), "src/help/message_catalog.cpp")
    gate("CMD_SET_PRESENT", (repo / "src/cli/cmd_set.cpp").exists(), "src/cli/cmd_set.cpp")
    review("COMMAND_OUTPUT_PRESENT", (repo / "src/cli/command_output.cpp").exists(), "central output router candidate, not selected for patch yet")
    review("CMD_HELP_PRESENT", (repo / "src/cli/cmd_help.cpp").exists(), "potential HELP consumer; not selected for patch yet")

    scan_rows = source_scan(repo)
    write_csv(reports / "message_catalog_phase22i_a_source_scan_v1.csv", scan_rows,
              ["SOURCE_PATH", "EXISTS", "BYTES", "SHA256", "HAS_FORMAT_MESSAGE_CATALOG",
               "HAS_ACTIVE_MESSAGE_CATALOG_STATUS", "HAS_SET_LANGUAGE", "HAS_OUTPUT_ROUTER",
               "HAS_HELP_HINT_COMMAND", "HAS_MESSAGE_LOCALE_SET"])

    seam_rows = [
        {
            "SEAM_ID": "SEAM-001",
            "SEAM": "SET LANGUAGE / SET LOCALE command surface",
            "SOURCE_PATH": "src/cli/cmd_set.cpp",
            "CURRENT_STATUS": "PROVEN_PILOT_SEAM",
            "RISK": "LOW",
            "RATIONALE": "Already proven through MSG-022G; can host controlled diagnostic emission without broad runtime routing.",
            "RECOMMENDATION": "Use as first controlled expansion seam only if Phase 22I-B is authorized.",
        },
        {
            "SEAM_ID": "SEAM-002",
            "SEAM": "Message catalog provider format API",
            "SOURCE_PATH": "src/help/message_catalog.cpp/.hpp",
            "CURRENT_STATUS": "PROVEN_ACTIVE_PROVIDER",
            "RISK": "LOW",
            "RATIONALE": "Provider already loads active rows and formats active catalog text with fallback.",
            "RECOMMENDATION": "Preserve compiled fallback and avoid writeback.",
        },
        {
            "SEAM_ID": "SEAM-003",
            "SEAM": "Command output router / general output path",
            "SOURCE_PATH": "src/cli/command_output.cpp",
            "CURRENT_STATUS": "DEFERRED_HIGHER_RISK",
            "RISK": "MEDIUM_HIGH",
            "RATIONALE": "Central output can affect many commands at once; too broad for next patch.",
            "RECOMMENDATION": "Do not route central output in 22I-B.",
        },
        {
            "SEAM_ID": "SEAM-004",
            "SEAM": "HELP/CMDHELPCHK integration",
            "SOURCE_PATH": "src/cli/cmd_help.cpp and HELP DATA lanes",
            "CURRENT_STATUS": "DEFERRED_PROTECTED",
            "RISK": "HIGH",
            "RATIONALE": "HELP DATA and CMDHELPCHK are protected systems with separate validation lanes.",
            "RECOMMENDATION": "No HELP DATA/CMDHELPCHK mutation in 22I-B.",
        },
        {
            "SEAM_ID": "SEAM-005",
            "SEAM": "Manualgen/Data Dictionary consumers",
            "SOURCE_PATH": "docs/manuals and docs/datadict lanes",
            "CURRENT_STATUS": "INTEGRATION_AWARE_DEFERRED",
            "RISK": "MEDIUM",
            "RATIONALE": "Manualgen and Data Dictionary need language support but should consume the shared locale/message infrastructure later.",
            "RECOMMENDATION": "Record dependency; do not mutate manualgen/datadict in 22I-B.",
        },
    ]
    write_csv(reports / "message_catalog_phase22i_a_candidate_seams_v1.csv", seam_rows,
              ["SEAM_ID", "SEAM", "SOURCE_PATH", "CURRENT_STATUS", "RISK", "RATIONALE", "RECOMMENDATION"])

    pilot_rows = [
        {
            "PILOT_ID": "22I-P1",
            "TITLE": "Diagnostic active emission command",
            "SELECTED": 1,
            "TARGET_SEAM": "SEAM-001",
            "TARGET_SOURCE": "src/cli/cmd_set.cpp",
            "PROPOSED_COMMAND": "SET MESSAGE EMIT <SYMBOL> [LOCALE <locale>]",
            "SAMPLE": "SET MESSAGE EMIT HELP_HINT_COMMAND LOCALE es",
            "EXPECTED_PROOF": "Emits active DBF-backed text for selected symbol/locale and reports provider mode active_dbf.",
            "WHY_SELECTED": "Low-risk, explicit diagnostic command; no broad runtime behavior change.",
        },
        {
            "PILOT_ID": "22I-P2",
            "TITLE": "Default locale diagnostic emission",
            "SELECTED": 1,
            "TARGET_SEAM": "SEAM-001",
            "TARGET_SOURCE": "src/cli/cmd_set.cpp",
            "PROPOSED_COMMAND": "SET MESSAGE EMIT <SYMBOL>",
            "SAMPLE": "SET LANGUAGE es; SET MESSAGE EMIT HELP_HINT_COMMAND",
            "EXPECTED_PROOF": "Uses current SET LANGUAGE locale when no LOCALE argument is supplied.",
            "WHY_SELECTED": "Connects locale state to explicit emission without replacing command output globally.",
        },
        {
            "PILOT_ID": "22I-P3",
            "TITLE": "General command output routing",
            "SELECTED": 0,
            "TARGET_SEAM": "SEAM-003",
            "TARGET_SOURCE": "src/cli/command_output.cpp",
            "PROPOSED_COMMAND": "n/a",
            "SAMPLE": "n/a",
            "EXPECTED_PROOF": "deferred",
            "WHY_SELECTED": "Rejected for next patch because it is too broad.",
        },
    ]
    write_csv(reports / "message_catalog_phase22i_a_selected_pilots_v1.csv", pilot_rows,
              ["PILOT_ID", "TITLE", "SELECTED", "TARGET_SEAM", "TARGET_SOURCE",
               "PROPOSED_COMMAND", "SAMPLE", "EXPECTED_PROOF", "WHY_SELECTED"])

    patch_plan_rows = [
        {
            "PATCH_ID": "22I-B-001",
            "TARGET_PATH": "src/cli/cmd_set.cpp",
            "ACTION": "ADD_EXPLICIT_DIAGNOSTIC_BRANCH",
            "DETAIL": "Add SET MESSAGE EMIT <symbol> [LOCALE <locale>] as diagnostic emission only.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PATCH_ID": "22I-B-002",
            "TARGET_PATH": "src/help/message_catalog.cpp/.hpp",
            "ACTION": "REVIEW_ONLY_UNLESS_BUILD_REQUIRES",
            "DETAIL": "Provider API already has format_message_catalog(locale,symbol,vars). No change expected.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PATCH_ID": "22I-B-003",
            "TARGET_PATH": "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_EMIT_SMOKE.dts",
            "ACTION": "CREATE_SMOKE_SCRIPT",
            "DETAIL": "Smoke should run SET LANGUAGE es and SET MESSAGE EMIT HELP_HINT_COMMAND.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "PATCH_ID": "22I-B-004",
            "TARGET_PATH": "tools/messaging/*phase22i_b*",
            "ACTION": "CREATE_VALIDATION_TOOLING",
            "DETAIL": "Validate explicit emission output, active provider, no writeback, and row counts.",
            "AUTHORIZED_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22i_a_guarded_patch_plan_v1.csv", patch_plan_rows,
              ["PATCH_ID", "TARGET_PATH", "ACTION", "DETAIL", "AUTHORIZED_NOW"])

    risk_rows = [
        {"RISK_ID": "RISK-001", "RISK": "Broad output routing could destabilize unrelated commands.", "MITIGATION": "Do not touch command_output.cpp in 22I-B; use explicit diagnostic command only."},
        {"RISK_ID": "RISK-002", "RISK": "Placeholder substitution is not fully typed/catalog-validated.", "MITIGATION": "Allow literal placeholder retention for pilot; plan placeholder contract review separately."},
        {"RISK_ID": "RISK-003", "RISK": "Locale fallback policy is still transitioning to shared locale spine.", "MITIGATION": "Keep en-US fallback behavior and record Phase 23 locale-spine dependency."},
        {"RISK_ID": "RISK-004", "RISK": "Repeated active DBF loads may be inefficient.", "MITIGATION": "Accept for pilot; consider caching only after correctness and invalidation policy are clear."},
        {"RISK_ID": "RISK-005", "RISK": "Manualgen/Data Dictionary consumers need localization later.", "MITIGATION": "Keep integration-aware records but do not mutate those lanes in 22I-B."},
    ]
    write_csv(reports / "message_catalog_phase22i_a_risk_register_v1.csv", risk_rows,
              ["RISK_ID", "RISK", "MITIGATION"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22I-A plan/report only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation; integration need recorded only."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation; integration need recorded only."},
    ]
    write_csv(reports / "message_catalog_phase22i_a_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22i_a_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "SELECTED_PILOTS": 2 if status == STATUS_GREEN else 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED", "SELECTED_PILOTS",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22i_a_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    md = f"""# Message Catalog Phase 22I-A Controlled Runtime Emission Expansion Plan

Status: `{status}`

Phase 22I-A is report-only. It selects a narrow next expansion seam after the
Phase 22H runtime emission pilot closeout.

## Selected next patch target

`src/cli/cmd_set.cpp`

## Selected pilot command shape

```text
SET MESSAGE EMIT <SYMBOL> [LOCALE <locale>]
```

Initial smoke:

```text
SET LANGUAGE es
SET MESSAGE EMIT HELP_HINT_COMMAND
SET MESSAGE EMIT HELP_HINT_COMMAND LOCALE es
```

## Why this seam

It is explicit and diagnostic. It proves active-provider message emission for
chosen symbols/locales without changing broad command output, HELP DATA,
CMDHELPCHK, manualgen, or Data Dictionary/SelfDoc behavior.

## Deferred

- central output routing
- HELP/CMDHELPCHK integration
- placeholder argument contract enforcement
- manualgen/Data Dictionary localization consumers
- provider caching/invalidation policy

## Next gate

`{NEXT_GATE}`
"""
    (reports / "MESSAGE_CATALOG_PHASE22I_A_CONTROLLED_RUNTIME_EMISSION_EXPANSION_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print(f"  selected pilots: {2 if status == STATUS_GREEN else 0}")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
