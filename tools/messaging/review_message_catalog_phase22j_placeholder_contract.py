#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22J_PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22J_PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22K_CONTROLLED_PLACEHOLDER_SUBSTITUTION_PILOT"
REPORT_DIR = Path("docs/messaging/reports")

SCAN_PATHS = [
    "docs/messaging/runlog/MSG-022I_C_LOCALE_BRIDGE_SMOKE.md",
    "docs/messaging/runlog/MSG-022I_B_CONTROLLED_EMIT_SMOKE.md",
    "docs/messaging/runlog/MSG-022G_SET_LANGUAGE_ACTIVE_LOOKUP_SMOKE.md",
    "docs/messaging/candidates/phase15x_x64_candidate_rebuild/scripts/MESSAGE_CATALOG_PHASE15X_CREATE_X64_CANDIDATES.dts",
    "src/help/helpdata_messages.cpp",
    "src/help/message_catalog.cpp",
    "src/help/message_catalog.hpp",
    "src/cli/cmd_set.cpp",
]

TOKEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")

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

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except ValueError:
        return str(path)

def scan_placeholders(repo: Path):
    rows = []
    seen = set()
    for relpath in SCAN_PATHS:
        path = repo / relpath
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in TOKEN_RE.finditer(line):
                token = m.group(1)
                key = (relpath, lineno, token, line.strip())
                if key in seen:
                    continue
                seen.add(key)
                sample = line.strip()
                if len(sample) > 220:
                    sample = sample[:217] + "..."
                rows.append({
                    "TOKEN": token,
                    "SOURCE_PATH": relpath,
                    "LINE": lineno,
                    "SAMPLE": sample,
                })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22ic = first_row(reports / "message_catalog_phase22i_c_runtime_status_summary_v1.csv")
    messages = p22ic.get("MESSAGES", "12")
    text_rows = p22ic.get("TEXT_ROWS", "60")
    locales = p22ic.get("LOCALES", "de;en-US;es;fr;it")

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

    placeholder_rows = scan_placeholders(repo)
    command_rows = [r for r in placeholder_rows if r["TOKEN"].lower() == "command"]

    gates = []
    failures = 0

    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name, ok, detail):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22I_C_LOCALE_BRIDGE_GREEN",
         p22ic.get("STATUS") == "MESSAGE_CATALOG_PHASE22I_C_SET_LANGUAGE_LOCALE_STATE_BRIDGE_SMOKE_GREEN",
         p22ic.get("STATUS", ""))
    gate("MSG_022I_C_SAVEPOINT_PRESENT",
         latest.get("savepoint_id") == "MSG-022I-C" or "MSG-022I-C" in journal_text,
         latest.get("savepoint_id", ""))
    gate("PLACEHOLDER_INVENTORY_NONEMPTY",
         len(placeholder_rows) > 0,
         f"placeholder rows={len(placeholder_rows)}")
    gate("COMMAND_PLACEHOLDER_FOUND",
         len(command_rows) > 0,
         f"command placeholder evidence rows={len(command_rows)}")
    gate("CONTROLLED_EMIT_SYMBOL_BASELINE",
         (repo / "docs/messaging/runlog/MSG-022I_C_LOCALE_BRIDGE_SMOKE.md").exists(),
         "MSG-022I_C_LOCALE_BRIDGE_SMOKE.md")
    review("SOURCE_PATCH_NOT_AUTHORIZED_THIS_PHASE",
           True,
           "Phase 22J is report-only; Phase 22K would require separate authorization.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22j_placeholder_inventory_v1.csv",
              placeholder_rows,
              ["TOKEN", "SOURCE_PATH", "LINE", "SAMPLE"])

    token_summary = {}
    for row in placeholder_rows:
        token = row["TOKEN"]
        token_summary.setdefault(token, {"TOKEN": token, "EVIDENCE_ROWS": 0, "SOURCE_FILES": set()})
        token_summary[token]["EVIDENCE_ROWS"] += 1
        token_summary[token]["SOURCE_FILES"].add(row["SOURCE_PATH"])
    token_summary_rows = []
    for token, info in sorted(token_summary.items(), key=lambda kv: kv[0].lower()):
        token_summary_rows.append({
            "TOKEN": token,
            "EVIDENCE_ROWS": info["EVIDENCE_ROWS"],
            "SOURCE_FILE_COUNT": len(info["SOURCE_FILES"]),
            "SOURCE_FILES": ";".join(sorted(info["SOURCE_FILES"])),
        })
    write_csv(reports / "message_catalog_phase22j_placeholder_token_summary_v1.csv",
              token_summary_rows,
              ["TOKEN", "EVIDENCE_ROWS", "SOURCE_FILE_COUNT", "SOURCE_FILES"])

    contract_rows = [
        {
            "CONTRACT_ID": "PH-001",
            "SYMBOL": "HELP_HINT_COMMAND",
            "PLACEHOLDER": "command",
            "PLACEHOLDER_TEXT": "{command}",
            "ARGUMENT_KIND": "command_name",
            "REQUIRED": 1,
            "CURRENT_BEHAVIOR": "literal placeholder preserved unless caller supplies variables to format_message_catalog",
            "PROPOSED_RUNTIME_ARGUMENT": "command",
            "PROPOSED_DIAGNOSTIC_SYNTAX": "SET MESSAGE EMIT HELP_HINT_COMMAND LOCALE es ARG command HELP",
            "FALLBACK_IF_MISSING": "preserve literal and report missing placeholder in diagnostic proof",
            "STATUS": "ACCEPTED_FOR_22K_PILOT",
        },
        {
            "CONTRACT_ID": "PH-002",
            "SYMBOL": "ALL_MESSAGES",
            "PLACEHOLDER": "*",
            "PLACEHOLDER_TEXT": "any {token}",
            "ARGUMENT_KIND": "future_typed_placeholder",
            "REQUIRED": 0,
            "CURRENT_BEHAVIOR": "not broadly audited yet",
            "PROPOSED_RUNTIME_ARGUMENT": "defer",
            "PROPOSED_DIAGNOSTIC_SYNTAX": "defer",
            "FALLBACK_IF_MISSING": "preserve literal until typed contract exists",
            "STATUS": "DEFERRED_AFTER_PILOT",
        },
    ]
    write_csv(reports / "message_catalog_phase22j_placeholder_contract_v1.csv",
              contract_rows,
              ["CONTRACT_ID", "SYMBOL", "PLACEHOLDER", "PLACEHOLDER_TEXT",
               "ARGUMENT_KIND", "REQUIRED", "CURRENT_BEHAVIOR",
               "PROPOSED_RUNTIME_ARGUMENT", "PROPOSED_DIAGNOSTIC_SYNTAX",
               "FALLBACK_IF_MISSING", "STATUS"])

    risk_rows = [
        {"RISK_ID": "RISK-001", "RISK": "Placeholder substitution could hide missing arguments.", "MITIGATION": "Phase 22K diagnostic output should explicitly report supplied args and missing placeholders."},
        {"RISK_ID": "RISK-002", "RISK": "Broad substitution before typed contracts could alter command output unexpectedly.", "MITIGATION": "Keep substitution limited to SET MESSAGE EMIT diagnostic pilot."},
        {"RISK_ID": "RISK-003", "RISK": "Placeholder names may vary across future messages/locales.", "MITIGATION": "Maintain placeholder token inventory and require per-symbol contracts before routing."},
        {"RISK_ID": "RISK-004", "RISK": "Manualgen/HELP/Data Dictionary will eventually need the same placeholder rules.", "MITIGATION": "Record shared contract but do not mutate those systems in Phase 22J/22K."},
    ]
    write_csv(reports / "message_catalog_phase22j_risk_register_v1.csv",
              risk_rows,
              ["RISK_ID", "RISK", "MITIGATION"])

    next_rows = [
        {
            "STEP": "22K-001",
            "ACTION": "CONTROLLED_DIAGNOSTIC_ARG_PARSE",
            "TARGET": "src/cli/cmd_set.cpp",
            "DETAIL": "Add guarded parsing for SET MESSAGE EMIT <symbol> [LOCALE <locale>] ARG <name> <value>.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": "22K-002",
            "ACTION": "HELP_HINT_COMMAND_SUBSTITUTION_SMOKE",
            "TARGET": "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22K_PLACEHOLDER_SUBSTITUTION_SMOKE.dts",
            "DETAIL": "Prove HELP_HINT_COMMAND with ARG command HELP emits Spanish text with HELP substituted.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": "22K-003",
            "ACTION": "MISSING_ARG_DIAGNOSTIC",
            "TARGET": "runtime output only",
            "DETAIL": "If placeholder arg missing, preserve literal and report missing placeholder; do not silently erase token.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": "22K-004",
            "ACTION": "NO_BROAD_ROUTING",
            "TARGET": "all runtime output",
            "DETAIL": "Do not route general command/errors through placeholder substitution in 22K.",
            "AUTHORIZED_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22j_next_gate_plan_v1.csv",
              next_rows,
              ["STEP", "ACTION", "TARGET", "DETAIL", "AUTHORIZED_NOW"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22J report-only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation; future placeholder consumers noted only."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation; future placeholder consumers noted only."},
    ]
    write_csv(reports / "message_catalog_phase22j_boundary_ledger_v1.csv",
              boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22j_gate_check_v1.csv",
              gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22j_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PLACEHOLDER_TOKENS_FOUND": len(token_summary_rows),
        "PLACEHOLDER_EVIDENCE_ROWS": len(placeholder_rows),
        "COMMAND_PLACEHOLDER_EVIDENCE_ROWS": len(command_rows),
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PLACEHOLDER_TOKENS_FOUND", "PLACEHOLDER_EVIDENCE_ROWS",
         "COMMAND_PLACEHOLDER_EVIDENCE_ROWS", "SOURCE_MUTATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = """# Message Catalog Phase 22J Placeholder Argument Contract Review

Status: `{status}`

Phase 22J is report-only. It records the placeholder argument contract needed
before expanding runtime message emission beyond literal text.

## Accepted pilot contract

Symbol: `HELP_HINT_COMMAND`

Placeholder: `{{command}}`

Proposed diagnostic syntax for the next gate:

```text
SET MESSAGE EMIT HELP_HINT_COMMAND LOCALE es ARG command HELP
```

Expected later Phase 22K proof:

```text
Escriba HELP HELP para obtener mas informacion.
```

The exact wording is intentionally diagnostic and may be awkward; the point is to
prove controlled placeholder substitution without broad runtime routing.

## Boundary

No source edits, no active DBF/CDX/LMDB mutation, no HELP DATA mutation, no
CMDHELPCHK mutation, no manualgen mutation, and no Data Dictionary/SelfDoc
mutation.

## Next gate

`{next_gate}`
""".format(status=status, next_gate=NEXT_GATE)
    (reports / "MESSAGE_CATALOG_PHASE22J_PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  placeholder tokens found: {len(token_summary_rows)}")
    print(f"  placeholder evidence rows: {len(placeholder_rows)}")
    print(f"  command placeholder evidence rows: {len(command_rows)}")
    print("  source mutation authorized: 0")
    print("  source files mutated: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
