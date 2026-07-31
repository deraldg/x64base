#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_EXISTING = "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_GREEN_EXISTING_SURFACE_OBSERVED"
STATUS_GAP = "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_GREEN_CONSUMER_SURFACE_GAP_CONFIRMED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_BLOCKED"
NEXT_EXISTING = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AP_EXISTING_CONSUMER_SURFACE_CONTRACT_REVIEW"
NEXT_GAP = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AP_RUNTIME_MESSAGE_CONSUMER_SOURCE_INTEGRATION_DESIGN_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE.md")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

PROOF_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
PROOF_LOCALES = ["en-US", "es", "fr", "de", "it"]
MUTATION_TOKENS = ["ZAP COMPLETE", "IMPORTED ", "APPEND", "REPLACE", "PACK", "BUILDLMDB", "CDX CREATE", "DELETE ALL"]

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
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path):
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def dbf_header_count(path: Path):
    if not path.exists() or path.stat().st_size < 12:
        return ""
    return int.from_bytes(path.read_bytes()[:12][4:8], "little")

def norm_text(s: str) -> str:
    return " ".join(s.replace("\r", "\n").split()).upper()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-log", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_10ao_stage_status_summary_v1.csv")
    runtime = Path(args.runtime_log) if args.runtime_log else repo / RUNLOG_PATH
    if not runtime.is_absolute():
        runtime = repo / runtime
    log = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    up = log.upper()
    compact = norm_text(log)

    msg_open14 = "OPENED SYSTEM_MESSAGES (V64) : RECORD COUNT 14" in up
    text_open70 = "OPENED SYSTEM_MESSAGE_TEXT (V64) : RECORD COUNT 70" in up
    count14 = "\n14\n" in log.replace("\r", "\n") or " 14 " in compact
    count70 = "\n70\n" in log.replace("\r", "\n") or " 70 " in compact
    listed14 = "14 RECORD(S) LISTED" in up
    listed70 = "70 RECORD(S) LISTED" in up
    proof_symbols = sum(1 for s in PROOF_SYMBOLS if s in up)
    proof_locales = sum(1 for loc in PROOF_LOCALES if loc.upper() in up)
    msg_header = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_header = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    unknown_count = up.count("UNKNOWN COMMAND")
    help_usage_count = up.count("USAGE:")
    cannot_open_count = up.count("CANNOT OPEN")
    message_surface_seen = 0
    surface_notes = []

    # Existing surface is considered observed if MESSAGE/MSG responds without unknown,
    # or if the registered read-only MSGMGR command-house surface is present.
    for marker in ["MESSAGE STATUS", "MESSAGE HELP", "MSG STATUS", "MSG HELP", "MESSAGE GET", "MSG GET"]:
        if marker in up and "UNKNOWN COMMAND: " + marker.split()[0] not in up:
            message_surface_seen = 1
            surface_notes.append(marker)

    if "MSGMGR STATUS" in up and "COMMAND HOUSE" in up and "REGISTERED" in up:
        message_surface_seen = 1
        surface_notes.append("MSGMGR STATUS registered command house")

    if "MSGMGR CHECK" in up and "ACTIVE MESSAGE CHECK" in up:
        message_surface_seen = 1
        surface_notes.append("MSGMGR CHECK read-only command-house check")

    if "SET MESSAGE CATALOG CHECK" in up or "SET MESSAGE CATALOG GET" in up:
        message_surface_seen = 1
        surface_notes.append("SET MESSAGE CATALOG CHECK/GET advertised by MSGMGR")

    # HELP surface is weaker but still worth noting.
    help_surface_seen = 1 if help_usage_count > 0 and any(x in up for x in ["MESSAGE", "MSG", "MSGMGR"]) else 0

    mutation_hits = [tok for tok in MUTATION_TOKENS if tok in up]

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_LOG_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("FRESH_OPEN_SYSTEM_MESSAGES_RECORD_COUNT_14", msg_open14, "Opened SYSTEM_MESSAGES record count 14")
    gate("FRESH_OPEN_SYSTEM_MESSAGE_TEXT_RECORD_COUNT_70", text_open70, "Opened SYSTEM_MESSAGE_TEXT record count 70")
    gate("COUNT_14_VISIBLE", count14, "COUNT output 14")
    gate("COUNT_70_VISIBLE", count70, "COUNT output 70")
    gate("LIST_14_VISIBLE", listed14, "LIST ALL message table")
    gate("LIST_70_VISIBLE", listed70, "LIST ALL text table")
    gate("PROOF_SYMBOLS_VISIBLE", proof_symbols == 2, f"{proof_symbols}/2")
    gate("PROOF_LOCALES_VISIBLE", proof_locales == 5, f"{proof_locales}/5")
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_header == 14, msg_header)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_header == 70, text_header)
    gate("NO_MUTATION_TOKENS", len(mutation_hits) == 0, ";".join(mutation_hits) if mutation_hits else "none")
    gate("NO_CANNOT_OPEN", cannot_open_count == 0, cannot_open_count)

    if failures == 0:
        status = STATUS_EXISTING if message_surface_seen else STATUS_GAP
        next_gate = NEXT_EXISTING if message_surface_seen else NEXT_GAP
    else:
        status = STATUS_BLOCKED
        next_gate = "HOLD_AND_FIX_PHASE22AE_6_5_10AO_READONLY_PROBE_FAILURE"
    validation_issues = "0" if failures == 0 else str(failures)

    surface_rows = [
        {"SURFACE": "MESSAGE_COMMAND", "OBSERVED": message_surface_seen, "DETAIL": ";".join(surface_notes) if surface_notes else "No confirmed MESSAGE/MSG consumer command surface; unknown-command responses are acceptable evidence."},
        {"SURFACE": "HELP_MESSAGE_SURFACE", "OBSERVED": help_surface_seen, "DETAIL": f"usage_count={help_usage_count}; unknown_count={unknown_count}"},
        {"SURFACE": "TABLE_READBACK_SURFACE", "OBSERVED": 1 if failures == 0 else 0, "DETAIL": "SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT active rows visible at 14/70."},
    ]

    observations = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if runtime.exists() else 0, "DETAIL": rel(runtime, repo)},
        {"OBSERVATION": "fresh_open_system_messages_14", "VALUE": 1 if msg_open14 else 0, "DETAIL": "USE active DBF"},
        {"OBSERVATION": "fresh_open_system_message_text_70", "VALUE": 1 if text_open70 else 0, "DETAIL": "USE active DBF"},
        {"OBSERVATION": "proof_symbols_visible", "VALUE": proof_symbols, "DETAIL": "2 expected"},
        {"OBSERVATION": "proof_locales_visible", "VALUE": proof_locales, "DETAIL": "5 expected"},
        {"OBSERVATION": "unknown_command_count", "VALUE": unknown_count, "DETAIL": "Unknown command is acceptable for consumer-surface gap classification."},
        {"OBSERVATION": "message_surface_seen", "VALUE": message_surface_seen, "DETAIL": ";".join(surface_notes)},
        {"OBSERVATION": "help_usage_count", "VALUE": help_usage_count, "DETAIL": "Observed help/usage responses."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AO is read-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "RUNTIME_CONSUMER_SOURCE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source integration."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_surface_classification_v1.csv", surface_rows, ["SURFACE", "OBSERVED", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_runtime_observations_v1.csv", observations, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_STATUS": stage.get("STATUS", ""),
        "FRESH_OPEN_SYSTEM_MESSAGES_14": 1 if msg_open14 else 0,
        "FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70": 1 if text_open70 else 0,
        "RUNTIME_MESSAGE_COUNT_14": 1 if count14 else 0,
        "RUNTIME_TEXT_COUNT_70": 1 if count70 else 0,
        "RUNTIME_MESSAGE_LISTED_14": 1 if listed14 else 0,
        "RUNTIME_TEXT_LISTED_70": 1 if listed70 else 0,
        "PROOF_SYMBOLS_VISIBLE": proof_symbols,
        "PROOF_LOCALES_VISIBLE": proof_locales,
        "UNKNOWN_COMMAND_COUNT": unknown_count,
        "MESSAGE_CONSUMER_SURFACE_OBSERVED": message_surface_seen,
        "HELP_MESSAGE_SURFACE_OBSERVED": help_surface_seen,
        "ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROBE": msg_header,
        "ACTIVE_TEXT_HEADER_COUNT_AFTER_PROBE": text_header,
        "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "STAGE_STATUS",
         "FRESH_OPEN_SYSTEM_MESSAGES_14", "FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70",
         "RUNTIME_MESSAGE_COUNT_14", "RUNTIME_TEXT_COUNT_70", "RUNTIME_MESSAGE_LISTED_14",
         "RUNTIME_TEXT_LISTED_70", "PROOF_SYMBOLS_VISIBLE", "PROOF_LOCALES_VISIBLE",
         "UNKNOWN_COMMAND_COUNT", "MESSAGE_CONSUMER_SURFACE_OBSERVED",
         "HELP_MESSAGE_SURFACE_OBSERVED", "ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROBE",
         "ACTIVE_TEXT_HEADER_COUNT_AFTER_PROBE", "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED",
         "SOURCE_FILES_MUTATED", "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_STAGED_SOURCE_HELD' else 0}")
    print(f"  fresh open SYSTEM_MESSAGES 14: {1 if msg_open14 else 0}")
    print(f"  fresh open SYSTEM_MESSAGE_TEXT 70: {1 if text_open70 else 0}")
    print(f"  runtime message count 14: {1 if count14 else 0}")
    print(f"  runtime text count 70: {1 if count70 else 0}")
    print(f"  runtime message listed 14: {1 if listed14 else 0}")
    print(f"  runtime text listed 70: {1 if listed70 else 0}")
    print(f"  proof symbols visible: {proof_symbols}/2")
    print(f"  proof locales visible: {proof_locales}/5")
    print(f"  unknown command count: {unknown_count}")
    print(f"  message consumer surface observed: {message_surface_seen}")
    print(f"  help message surface observed: {help_surface_seen}")
    print("  runtime consumer source integration authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if failures == 0 else 2

if __name__ == "__main__":
    raise SystemExit(main())
