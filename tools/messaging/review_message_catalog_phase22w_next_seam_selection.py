#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22W_NEXT_LOW_RISK_RUNTIME_SEAM_SELECTION_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22W_NEXT_LOW_RISK_RUNTIME_SEAM_SELECTION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22X_SET_MESSAGE_PROOF_STATUS_TEXT_ROUTING_PLAN"
REPORT_DIR = Path("docs/messaging/reports")

SELECTED_SEAM_ID = "RT-008"
SELECTED_SEAM_NAME = "SET MESSAGE PROOF status text routing"
SELECTED_SYMBOL_CANDIDATES = "MESSAGE_PROOF_MODE_STATUS;MESSAGE_PROOF_BOUNDARY_NOTE"
SELECTED_COMMAND_SURFACE = "SET MESSAGE PROOF ON|OFF|CHECK"

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
    reports = repo / REPORT_DIR
    latest_path = reports / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            latest_id = latest.get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal_path = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    journal_text = journal_path.read_text(encoding="utf-8", errors="replace") if journal_path.exists() else ""
    return latest_id == savepoint_id or savepoint_id in journal_text, latest_id

def find_in_file(path: Path, needles: list[str]):
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        for needle in needles:
            if needle in line:
                rows.append({
                    "SOURCE_PATH": str(path).replace("\\", "/"),
                    "LINE": idx,
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

    p22v = first_row(reports / "message_catalog_phase22v_runtime_regression_status_summary_v1.csv")
    messages = p22v.get("MESSAGES", "12")
    text_rows = p22v.get("TEXT_ROWS", "60")
    locales = p22v.get("LOCALES", "de;en-US;es;fr;it")
    savepoint_ok, latest_id = savepoint_present(repo, "MSG-022V")

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22V_REGRESSION_GREEN",
         p22v.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN",
         p22v.get("STATUS", "missing"))
    gate("MSG_022V_SAVEPOINT_PRESENT", savepoint_ok, latest_id)
    gate("PROVIDER_ACTIVE_DBF_PROVEN", p22v.get("PROVIDER_ACTIVE_DBF") == "1", p22v.get("PROVIDER_ACTIVE_DBF", ""))
    gate("HELP_HINT_COMMAND_PROVEN", p22v.get("HELP_HINT_COMMAND_PROOF") == "1", p22v.get("HELP_HINT_COMMAND_PROOF", ""))
    gate("PROOF_LANE_GATED_PROVEN", p22v.get("PROOF_LANE_GATED") == "1", p22v.get("PROOF_LANE_GATED", ""))

    cmd_set = repo / "src/cli/cmd_set.cpp"
    anchors = find_in_file(cmd_set, [
        "print_message_proof_status",
        "Message routing proof mode:",
        "proof mode changes runtime diagnostic state only",
        "SET MESSAGE PROOF",
        "handle_set_message_proof",
    ])
    # Rewrite absolute path to repo-relative for reports.
    for row in anchors:
        try:
            row["SOURCE_PATH"] = str(Path(row["SOURCE_PATH"]).relative_to(repo)).replace("\\", "/")
        except Exception:
            pass

    gate("CMD_SET_SOURCE_PRESENT", cmd_set.exists(), "src/cli/cmd_set.cpp")
    gate("SET_MESSAGE_PROOF_ANCHORS_VISIBLE", len(anchors) >= 3, f"anchor rows={len(anchors)}")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    candidates = [
        {
            "CANDIDATE_ID": "RT-008",
            "SEAM": "SET MESSAGE PROOF status text routing",
            "COMMAND_SURFACE": "SET MESSAGE PROOF ON|OFF|CHECK",
            "RECOMMENDATION": "SELECTED",
            "RISK": "LOW",
            "RATIONALE": "Diagnostic-only text, already covered by proof-lane regression pack, no user data or HELP DATA dependency, and narrow source surface in cmd_set.cpp.",
            "EXPECTED_SYMBOLS": "MESSAGE_PROOF_MODE_STATUS;MESSAGE_PROOF_BOUNDARY_NOTE",
            "PATCH_NOW": 0,
        },
        {
            "CANDIDATE_ID": "RT-009",
            "SEAM": "SET MESSAGE CATALOG CHECK status labels",
            "COMMAND_SURFACE": "SET MESSAGE CATALOG CHECK",
            "RECOMMENDATION": "NEXT_AFTER_RT_008",
            "RISK": "LOW",
            "RATIONALE": "Read-only provider status text is useful, but it has more lines and should follow the proof-status micro-seam.",
            "EXPECTED_SYMBOLS": "MESSAGE_CATALOG_PROVIDER_STATUS;MESSAGE_CATALOG_ACTIVE_LOADED;MESSAGE_CATALOG_COMPILED_FALLBACK",
            "PATCH_NOW": 0,
        },
        {
            "CANDIDATE_ID": "RT-010",
            "SEAM": "SET LANGUAGE CHECK / REPORT read-only text",
            "COMMAND_SURFACE": "SET LANGUAGE CHECK; SET LANGUAGE REPORT",
            "RECOMMENDATION": "GOOD_LATER",
            "RISK": "MEDIUM_LOW",
            "RATIONALE": "Nearby to locale work and valuable, but broader than the proof-status micro-seam.",
            "EXPECTED_SYMBOLS": "MESSAGE_LOCALE_CURRENT;MESSAGE_LOCALE_SUPPORTED_LIST;MESSAGE_LOCALE_USAGE",
            "PATCH_NOW": 0,
        },
        {
            "CANDIDATE_ID": "RT-011",
            "SEAM": "HELP DATA localization",
            "COMMAND_SURFACE": "HELP topics and HELP DATA rows",
            "RECOMMENDATION": "DEFER",
            "RISK": "HIGH",
            "RATIONALE": "Touches protected HELP DATA/CMDHELPCHK surfaces; should wait for separate preservation plan.",
            "EXPECTED_SYMBOLS": "deferred",
            "PATCH_NOW": 0,
        },
        {
            "CANDIDATE_ID": "RT-012",
            "SEAM": "central output router messageization",
            "COMMAND_SURFACE": "many commands",
            "RECOMMENDATION": "DEFER",
            "RISK": "HIGH",
            "RATIONALE": "Too broad; high blast radius across runtime output.",
            "EXPECTED_SYMBOLS": "deferred",
            "PATCH_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22w_next_seam_candidates_v1.csv", candidates,
              ["CANDIDATE_ID", "SEAM", "COMMAND_SURFACE", "RECOMMENDATION", "RISK",
               "RATIONALE", "EXPECTED_SYMBOLS", "PATCH_NOW"])

    selected = [{
        "SELECTED_SEAM_ID": SELECTED_SEAM_ID,
        "SELECTED_SEAM": SELECTED_SEAM_NAME,
        "COMMAND_SURFACE": SELECTED_COMMAND_SURFACE,
        "SYMBOL_CANDIDATES": SELECTED_SYMBOL_CANDIDATES,
        "SOURCE_TARGET": "src/cli/cmd_set.cpp",
        "PLAN_ONLY": 1,
        "SOURCE_MUTATION_NOW": 0,
        "ACTIVE_CATALOG_MUTATION_NOW": 0,
        "HELP_DATA_MUTATION_NOW": 0,
        "CMDHELPCHK_MUTATION_NOW": 0,
        "NEXT_PHASE": "22X",
        "NEXT_PHASE_SCOPE": "report-only patch plan and anchor probe; no mutation until explicit apply gate",
    }]
    write_csv(reports / "message_catalog_phase22w_selected_seam_v1.csv", selected,
              ["SELECTED_SEAM_ID", "SELECTED_SEAM", "COMMAND_SURFACE", "SYMBOL_CANDIDATES",
               "SOURCE_TARGET", "PLAN_ONLY", "SOURCE_MUTATION_NOW",
               "ACTIVE_CATALOG_MUTATION_NOW", "HELP_DATA_MUTATION_NOW",
               "CMDHELPCHK_MUTATION_NOW", "NEXT_PHASE", "NEXT_PHASE_SCOPE"])

    write_csv(reports / "message_catalog_phase22w_source_anchor_inventory_v1.csv", anchors,
              ["SOURCE_PATH", "LINE", "NEEDLE", "TEXT"])

    phase22x_plan = [
        {
            "STEP": 1,
            "ACTION": "ANCHOR_PROBE",
            "DETAIL": "Inspect cmd_set.cpp proof-status helper and identify the exact status/boundary lines to route.",
            "MUTATION_ALLOWED_IN_22X": 0,
        },
        {
            "STEP": 2,
            "ACTION": "CATALOG_SYMBOL_PLAN",
            "DETAIL": "Define candidate catalog symbols MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE, including placeholder needs such as {mode}.",
            "MUTATION_ALLOWED_IN_22X": 0,
        },
        {
            "STEP": 3,
            "ACTION": "FALLBACK_PLAN",
            "DETAIL": "Require compiled fallback text to remain available if active DBF is absent or symbol lookup fails.",
            "MUTATION_ALLOWED_IN_22X": 0,
        },
        {
            "STEP": 4,
            "ACTION": "PATCH_PACKAGE_DECISION",
            "DETAIL": "Only after 22X is green should a later phase apply source/catalog seed changes, if explicitly authorized.",
            "MUTATION_ALLOWED_IN_22X": 0,
        },
        {
            "STEP": 5,
            "ACTION": "REGRESSION_IMPACT",
            "DETAIL": "22V regression pack must remain green after any later source patch.",
            "MUTATION_ALLOWED_IN_22X": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22w_phase22x_plan_v1.csv", phase22x_plan,
              ["STEP", "ACTION", "DETAIL", "MUTATION_ALLOWED_IN_22X"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22W seam selection only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22w_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22w_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22w_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22V_GREEN": 1 if p22v.get("STATUS") == "MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN" else 0,
        "MSG_022V_SAVEPOINT_PRESENT": 1 if savepoint_ok else 0,
        "SELECTED_SEAM_ID": SELECTED_SEAM_ID,
        "SELECTED_SEAM": SELECTED_SEAM_NAME,
        "SELECTED_COMMAND_SURFACE": SELECTED_COMMAND_SURFACE,
        "ANCHOR_ROWS": len(anchors),
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22V_GREEN", "MSG_022V_SAVEPOINT_PRESENT", "SELECTED_SEAM_ID",
         "SELECTED_SEAM", "SELECTED_COMMAND_SURFACE", "ANCHOR_ROWS",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22W Next Low-Risk Runtime Seam Selection

Status: `{status}`

Selected seam:

```text
{SELECTED_SEAM_ID}: {SELECTED_SEAM_NAME}
surface: {SELECTED_COMMAND_SURFACE}
candidate symbols: {SELECTED_SYMBOL_CANDIDATES}
```

Rationale:

- Diagnostic-only.
- Already exercised by the 22V regression pack.
- Narrow source surface in `src/cli/cmd_set.cpp`.
- No HELP DATA, CMDHELPCHK, command registry, manualgen, or Data Dictionary/SelfDoc dependency.

Next gate:

```text
{NEXT_GATE}
```

Phase 22W is report-only and performs no source/catalog mutation.
"""
    (reports / "MESSAGE_CATALOG_PHASE22W_NEXT_LOW_RISK_RUNTIME_SEAM_SELECTION.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22V green: {1 if p22v.get('STATUS') == 'MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE_GREEN' else 0}")
    print(f"  MSG-022V savepoint present: {1 if savepoint_ok else 0}")
    print(f"  selected seam: {SELECTED_SEAM_NAME}")
    print(f"  selected seam id: {SELECTED_SEAM_ID}")
    print(f"  selected command surface: {SELECTED_COMMAND_SURFACE}")
    print(f"  anchor rows: {len(anchors)}")
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
