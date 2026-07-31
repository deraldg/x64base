#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22V_REGRESSION_PACK_SCRIPT_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22V_REGRESSION_PACK_SCRIPT_STAGING_BLOCKED"
NEXT_GATE = "RUN_PHASE22V_RUNTIME_REGRESSION_SMOKE_THEN_VALIDATE"
REPORT_DIR = Path("docs/messaging/reports")
SMOKE_SCRIPT = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE.dts")

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22u = first_row(reports / "message_catalog_phase22u_status_summary_v1.csv")
    messages = p22u.get("MESSAGES", "12")
    text_rows = p22u.get("TEXT_ROWS", "60")
    locales = p22u.get("LOCALES", "de;en-US;es;fr;it")
    savepoint_ok, latest_id = savepoint_present(repo, "MSG-022U")

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    gate("PHASE22U_PLAN_GREEN",
         p22u.get("STATUS") == "MESSAGE_CATALOG_PHASE22U_REGRESSION_PACK_PLAN_GREEN_SOURCE_HELD",
         p22u.get("STATUS", "missing"))
    gate("MSG_022U_SAVEPOINT_PRESENT", savepoint_ok, latest_id)

    status = STATUS_BLOCKED
    script_rel = str(SMOKE_SCRIPT).replace("\\", "/")
    script_rows = []
    if failures == 0:
        script_path = repo / SMOKE_SCRIPT
        script_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "* MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE.dts",
            "* Regression pack for first-wave active message catalog runtime routing.",
            "* Covers provider status, MESSAGE_LOCALE_SET, UNSUPPORTED_MESSAGE_LOCALE, HELP_HINT_COMMAND, proof gating, placeholders, fallback bypass, boundaries.",
            "SET MESSAGE PROOF OFF",
            "SET MESSAGE CATALOG CHECK",
            "SET MESSAGE PROOF ON",
            "SET LANGUAGE es",
            "SET LANGUAGE zz",
            "HELP __MSG22V_UNKNOWN__",
            "SET MESSAGE PROOF OFF",
            "SET LANGUAGE es",
            "HELP __MSG22V_UNKNOWN__",
            "SET MESSAGE CATALOG CHECK",
            "SET MESSAGE PROOF CHECK",
            "",
        ]
        script_path.write_text("\n".join(lines), encoding="utf-8")
        script_rows.append({
            "ARTIFACT": script_rel,
            "ROLE": "combined runtime routing regression smoke",
            "CREATED_OR_UPDATED": 1,
            "BYTES": script_path.stat().st_size,
            "SHA256": sha256_file(script_path),
        })
        status = STATUS_GREEN

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22v_staged_artifacts_v1.csv", script_rows,
              ["ARTIFACT", "ROLE", "CREATED_OR_UPDATED", "BYTES", "SHA256"])

    cases = [
        {"CASE_ID": "REG-001", "SCRIPT_COMMAND": "SET MESSAGE CATALOG CHECK", "EXPECTED": "active_dbf provider status, active catalog loaded yes"},
        {"CASE_ID": "REG-002", "SCRIPT_COMMAND": "SET MESSAGE PROOF ON; SET LANGUAGE es", "EXPECTED": "MESSAGE_LOCALE_SET proof and Spanish locale message"},
        {"CASE_ID": "REG-003", "SCRIPT_COMMAND": "SET LANGUAGE zz", "EXPECTED": "UNSUPPORTED_MESSAGE_LOCALE proof and Spanish unsupported-locale message"},
        {"CASE_ID": "REG-004", "SCRIPT_COMMAND": "HELP __MSG22V_UNKNOWN__", "EXPECTED": "HELP_HINT_COMMAND Spanish hint, placeholder substituted, FOXHELP fallback bypassed"},
        {"CASE_ID": "REG-005", "SCRIPT_COMMAND": "SET MESSAGE PROOF OFF; HELP __MSG22V_UNKNOWN__", "EXPECTED": "localized hint with no proof line"},
        {"CASE_ID": "REG-006", "SCRIPT_COMMAND": "SET MESSAGE CATALOG CHECK; SET MESSAGE PROOF CHECK", "EXPECTED": "boundary lines and compiled fallback availability"},
    ]
    write_csv(reports / "message_catalog_phase22v_regression_case_map_v1.csv", cases,
              ["CASE_ID", "SCRIPT_COMMAND", "EXPECTED"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22V staging creates a docs/messaging script artifact only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22v_staging_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22v_staging_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22v_staging_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22U_GREEN": 1 if p22u.get("STATUS") == "MESSAGE_CATALOG_PHASE22U_REGRESSION_PACK_PLAN_GREEN_SOURCE_HELD" else 0,
        "MSG_022U_SAVEPOINT_PRESENT": 1 if savepoint_ok else 0,
        "SCRIPT_STAGED": 1 if status == STATUS_GREEN else 0,
        "SCRIPT_PATH": script_rel,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "RUNTIME_SMOKE_EXECUTED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22U_GREEN", "MSG_022U_SAVEPOINT_PRESENT", "SCRIPT_STAGED", "SCRIPT_PATH",
         "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "RUNTIME_SMOKE_EXECUTED", "NEXT_GATE",
         "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22U green: {1 if p22u.get('STATUS') == 'MESSAGE_CATALOG_PHASE22U_REGRESSION_PACK_PLAN_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022U savepoint present: {1 if savepoint_ok else 0}")
    print(f"  script staged: {1 if status == STATUS_GREEN else 0}")
    print(f"  script path: {script_rel}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  runtime smoke executed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
