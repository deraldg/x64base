#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22U_REGRESSION_PACK_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22U_REGRESSION_PACK_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22V_REGRESSION_PACK_SCRIPT_STAGING"
REPORT_DIR = Path("docs/messaging/reports")

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

def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    p22t = first_row(reports / "message_catalog_phase22t_status_summary_v1.csv")
    s1 = first_row(reports / "message_catalog_phase22s1_runtime_status_summary_v1.csv")

    messages = p22t.get("MESSAGES", s1.get("MESSAGES", "12"))
    text_rows = p22t.get("TEXT_ROWS", s1.get("TEXT_ROWS", "60"))
    locales = p22t.get("LOCALES", s1.get("LOCALES", "de;en-US;es;fr;it"))

    savepoint_ok, latest_id = savepoint_present(repo, "MSG-022T")

    gates = []
    failures = 0

    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": detail})
        if not ok:
            failures += 1

    def review(name: str, ok: bool, detail: str):
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "REVIEW", "DETAIL": detail})

    gate("PHASE22T_CLOSEOUT_GREEN",
         p22t.get("STATUS") == "MESSAGE_CATALOG_PHASE22T_RUNTIME_ROUTING_CLOSEOUT_GREEN_SOURCE_HELD",
         p22t.get("STATUS", "missing"))
    gate("MSG_022T_SAVEPOINT_PRESENT", savepoint_ok, latest_id)
    gate("S1_RUNTIME_REPORT_GREEN",
         s1.get("STATUS") == "MESSAGE_CATALOG_PHASE22S1_HELP_HINT_RUNTIME_ROUTING_SMOKE_GREEN",
         s1.get("STATUS", "missing"))
    gate("S1_HELP_HINT_ROUTING_PROOF",
         s1.get("HELP_HINT_ROUTING_PROOF") == "1",
         s1.get("HELP_HINT_ROUTING_PROOF", ""))
    gate("S1_PROOF_LANE_GATED",
         s1.get("PROOF_LANE_GATED") == "1",
         s1.get("PROOF_LANE_GATED", ""))
    gate("S1_FOXHELP_FALLBACK_ZERO",
         s1.get("FOXHELP_FALLBACK_COUNT") == "0",
         s1.get("FOXHELP_FALLBACK_COUNT", ""))

    review("REGRESSION_PACK_REPORT_ONLY",
           True,
           "Phase 22U only designs the regression pack; it creates no runtime script and performs no source/catalog mutation.")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    regression_cases = [
        {
            "CASE_ID": "REG-001",
            "NAME": "Provider status active DBF loaded",
            "COMMAND_SEQUENCE": "SET MESSAGE CATALOG CHECK",
            "EXPECTED_PROOF": "mode active_dbf; active catalog present yes; active catalog loaded yes; message count 12; text row count 60",
            "SYMBOLS": "provider_status",
            "RISK": "LOW",
            "STAGE_IN_22V": 1,
        },
        {
            "CASE_ID": "REG-002",
            "NAME": "SET LANGUAGE success routing",
            "COMMAND_SEQUENCE": "SET MESSAGE PROOF ON; SET LANGUAGE es; SET MESSAGE PROOF OFF",
            "EXPECTED_PROOF": "Idioma de mensajes: es; Message routing proof: active_dbf MESSAGE_LOCALE_SET",
            "SYMBOLS": "MESSAGE_LOCALE_SET",
            "RISK": "LOW",
            "STAGE_IN_22V": 1,
        },
        {
            "CASE_ID": "REG-003",
            "NAME": "Unsupported locale rejection routing",
            "COMMAND_SEQUENCE": "SET MESSAGE PROOF ON; SET LANGUAGE zz; SET MESSAGE PROOF OFF",
            "EXPECTED_PROOF": "Configuracion regional de mensajes no admitida: zz; Message routing proof: active_dbf UNSUPPORTED_MESSAGE_LOCALE",
            "SYMBOLS": "UNSUPPORTED_MESSAGE_LOCALE",
            "RISK": "LOW",
            "STAGE_IN_22V": 1,
        },
        {
            "CASE_ID": "REG-004",
            "NAME": "HELP hint routing and placeholder substitution",
            "COMMAND_SEQUENCE": "SET LANGUAGE es; SET MESSAGE PROOF ON; HELP __MSG22U_UNKNOWN__; SET MESSAGE PROOF OFF",
            "EXPECTED_PROOF": "Escriba HELP __MSG22U_UNKNOWN__ para obtener mas informacion.; Message routing proof: active_dbf HELP_HINT_COMMAND; no Try FOXHELP fallback",
            "SYMBOLS": "HELP_HINT_COMMAND",
            "RISK": "MEDIUM_LOW",
            "STAGE_IN_22V": 1,
        },
        {
            "CASE_ID": "REG-005",
            "NAME": "Proof lane off remains quiet",
            "COMMAND_SEQUENCE": "SET MESSAGE PROOF OFF; SET LANGUAGE es; HELP __MSG22U_UNKNOWN__",
            "EXPECTED_PROOF": "localized text appears but no Message routing proof line",
            "SYMBOLS": "SET MESSAGE PROOF",
            "RISK": "LOW",
            "STAGE_IN_22V": 1,
        },
        {
            "CASE_ID": "REG-006",
            "NAME": "Placeholder token is not leaked",
            "COMMAND_SEQUENCE": "SET LANGUAGE es; HELP __MSG22U_UNKNOWN__",
            "EXPECTED_PROOF": "output contains __MSG22U_UNKNOWN__; output does not contain literal {command}",
            "SYMBOLS": "HELP_HINT_COMMAND placeholder command",
            "RISK": "LOW",
            "STAGE_IN_22V": 1,
        },
        {
            "CASE_ID": "REG-007",
            "NAME": "Boundary line preservation",
            "COMMAND_SEQUENCE": "SET MESSAGE CATALOG CHECK; SET MESSAGE PROOF CHECK",
            "EXPECTED_PROOF": "boundary lines report no DBF/CDX/LMDB mutation and no runtime writeback",
            "SYMBOLS": "boundary",
            "RISK": "LOW",
            "STAGE_IN_22V": 1,
        },
        {
            "CASE_ID": "REG-008",
            "NAME": "Compiled fallback availability stated",
            "COMMAND_SEQUENCE": "SET MESSAGE CATALOG CHECK",
            "EXPECTED_PROOF": "detail includes compiled fallback available",
            "SYMBOLS": "compiled_fallback",
            "RISK": "LOW",
            "STAGE_IN_22V": 1,
        },
    ]
    write_csv(reports / "message_catalog_phase22u_regression_cases_v1.csv", regression_cases,
              ["CASE_ID", "NAME", "COMMAND_SEQUENCE", "EXPECTED_PROOF", "SYMBOLS", "RISK", "STAGE_IN_22V"])

    pack_plan = [
        {
            "STEP": 1,
            "ACTION": "STAGE_COMBINED_RUNTIME_SMOKE_SCRIPT",
            "DETAIL": "Create docs/messaging/scripts/MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE.dts containing the selected regression cases.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": 2,
            "ACTION": "RUN_DOTTALK_SMOKE",
            "DETAIL": "Run the combined smoke through datarun after build is already green; do not mutate source/catalog/help.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": 3,
            "ACTION": "CAPTURE_CLEAN_RUNLOG",
            "DETAIL": "Capture normalized runlog at docs/messaging/runlog/MSG-022V_RUNTIME_ROUTING_REGRESSION_SMOKE.md.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": 4,
            "ACTION": "VALIDATE_COUNTS_AND_BOUNDARIES",
            "DETAIL": "Validate routed symbols, proof line gating, placeholder substitution, fallback bypass, active_dbf loaded, and no-writeback boundaries.",
            "AUTHORIZED_NOW": 0,
        },
        {
            "STEP": 5,
            "ACTION": "SAVEPOINT",
            "DETAIL": "Append MSG-022V only after the regression pack validates green.",
            "AUTHORIZED_NOW": 0,
        },
    ]
    write_csv(reports / "message_catalog_phase22u_regression_pack_plan_v1.csv", pack_plan,
              ["STEP", "ACTION", "DETAIL", "AUTHORIZED_NOW"])

    next_seams = [
        {
            "CANDIDATE_ID": "NEXT-001",
            "SEAM": "next read-only status/report message",
            "RECOMMENDATION": "AFTER_REGRESSION_PACK_GREEN",
            "RATIONALE": "Continue with a narrow, low-risk status/report message after regression pack protects the first-wave seams.",
            "BLOCKERS": "Phase 22V regression pack should be green first.",
        },
        {
            "CANDIDATE_ID": "NEXT-002",
            "SEAM": "additional SET validation/error messages",
            "RECOMMENDATION": "GOOD_CANDIDATE",
            "RATIONALE": "SET already has active message integration and localized language state; nearby error/status messages are natural next seams.",
            "BLOCKERS": "Need a specific symbol and source anchor plan.",
        },
        {
            "CANDIDATE_ID": "NEXT-003",
            "SEAM": "broad HELP DATA rendering",
            "RECOMMENDATION": "DEFER",
            "RATIONALE": "HELP DATA/CMDHELPCHK are protected; broad HELP localization should wait until multiple narrow seams and regression pack are stable.",
            "BLOCKERS": "Needs separate HELP/CMDHELPCHK preservation plan.",
        },
        {
            "CANDIDATE_ID": "NEXT-004",
            "SEAM": "central output router",
            "RECOMMENDATION": "DEFER",
            "RATIONALE": "Too broad; high blast radius across commands.",
            "BLOCKERS": "Needs more proven narrow seams.",
        },
    ]
    write_csv(reports / "message_catalog_phase22u_next_runtime_seam_recommendations_v1.csv", next_seams,
              ["CANDIDATE_ID", "SEAM", "RECOMMENDATION", "RATIONALE", "BLOCKERS"])

    artifacts = [
        {
            "ARTIFACT": "docs/messaging/scripts/MESSAGE_CATALOG_PHASE22V_RUNTIME_ROUTING_REGRESSION_SMOKE.dts",
            "ROLE": "candidate combined runtime smoke script",
            "CREATE_IN_22U": 0,
            "RECOMMEND_CREATE_IN_22V": 1,
        },
        {
            "ARTIFACT": "docs/messaging/runlog/MSG-022V_RUNTIME_ROUTING_REGRESSION_SMOKE.md",
            "ROLE": "candidate normalized runlog capture",
            "CREATE_IN_22U": 0,
            "RECOMMEND_CREATE_IN_22V": 1,
        },
        {
            "ARTIFACT": "docs/messaging/reports/message_catalog_phase22v_runtime_regression_status_summary_v1.csv",
            "ROLE": "candidate validation status summary",
            "CREATE_IN_22U": 0,
            "RECOMMEND_CREATE_IN_22V": 1,
        },
    ]
    write_csv(reports / "message_catalog_phase22u_candidate_artifacts_v1.csv", artifacts,
              ["ARTIFACT", "ROLE", "CREATE_IN_22U", "RECOMMEND_CREATE_IN_22V"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22U report-only regression pack plan; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22u_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22u_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    write_csv(reports / "message_catalog_phase22u_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22T_GREEN": 1 if p22t.get("STATUS") == "MESSAGE_CATALOG_PHASE22T_RUNTIME_ROUTING_CLOSEOUT_GREEN_SOURCE_HELD" else 0,
        "MSG_022T_SAVEPOINT_PRESENT": 1 if savepoint_ok else 0,
        "REGRESSION_CASES": len(regression_cases),
        "CANDIDATE_ARTIFACTS_CREATED": 0,
        "SOURCE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "PHASE22T_GREEN", "MSG_022T_SAVEPOINT_PRESENT", "REGRESSION_CASES",
         "CANDIDATE_ARTIFACTS_CREATED", "SOURCE_MUTATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    md = f"""# Message Catalog Phase 22U Regression Pack Plan

Status: `{status}`

Phase 22U is report-only. It plans the regression pack that should be staged in
Phase 22V before more runtime seams are patched.

## Regression coverage

- Provider status / active DBF loaded.
- `MESSAGE_LOCALE_SET`.
- `UNSUPPORTED_MESSAGE_LOCALE`.
- `HELP_HINT_COMMAND`.
- Proof lane off/on/off gating.
- Placeholder substitution.
- FOXHELP fallback bypass for active HELP hint.
- No-writeback boundary text.
- Compiled fallback availability.

## Next gate

`{NEXT_GATE}`

No source, active catalog, HELP DATA, CMDHELPCHK, command registry, manualgen, or
Data Dictionary/SelfDoc mutation occurs in Phase 22U.
"""
    (reports / "MESSAGE_CATALOG_PHASE22U_REGRESSION_PACK_PLAN.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22T green: {1 if p22t.get('STATUS') == 'MESSAGE_CATALOG_PHASE22T_RUNTIME_ROUTING_CLOSEOUT_GREEN_SOURCE_HELD' else 0}")
    print(f"  MSG-022T savepoint present: {1 if savepoint_ok else 0}")
    print(f"  regression cases planned: {len(regression_cases)}")
    print("  candidate artifacts created: 0")
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
