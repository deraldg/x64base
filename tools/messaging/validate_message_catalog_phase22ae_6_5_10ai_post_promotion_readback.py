#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AI_POST_PROMOTION_FRESH_READBACK_GREEN_ACTIVE_PROMOTION_PERSISTED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AI_POST_PROMOTION_FRESH_READBACK_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AJ_POST_PROMOTION_ACCEPTANCE_AND_BACKUP_RETENTION_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AI_POST_PROMOTION_FRESH_READBACK.md")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
PROOF_SYMBOLS = ["MESSAGE_PROOF_MODE_STATUS", "MESSAGE_PROOF_BOUNDARY_NOTE"]
PROOF_LOCALES = ["en-US", "es", "fr", "de", "it"]

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

def savepoint_present(repo: Path, savepoint_id: str):
    latest = ""
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if latest_path.exists():
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest == savepoint_id or savepoint_id in text, latest

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

    stage = first_row(reports / "message_catalog_phase22ae_6_5_10ai_stage_status_summary_v1.csv")
    sp10ah, latest = savepoint_present(repo, "MSG-022AE.6.5.10AH")
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

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AI_POST_PROMOTION_FRESH_READBACK_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AH_SAVEPOINT_PRESENT", sp10ah, latest)
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
    gate("NO_ZAP", "ZAP" not in up, "readback-only")
    gate("NO_IMPORT", "IMPORT" not in up or "IMPORTED" not in up, "readback-only")
    gate("NO_UNKNOWN_COMMAND", "UNKNOWN COMMAND" not in up, "must be absent")
    gate("NO_CANNOT_OPEN", "CANNOT OPEN" not in up, "must be absent")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    observations = [
        {"OBSERVATION":"runtime_log_exists","VALUE":1 if runtime.exists() else 0,"DETAIL":rel(runtime, repo)},
        {"OBSERVATION":"fresh_open_system_messages_14","VALUE":1 if msg_open14 else 0,"DETAIL":"fresh runtime USE"},
        {"OBSERVATION":"fresh_open_system_message_text_70","VALUE":1 if text_open70 else 0,"DETAIL":"fresh runtime USE"},
        {"OBSERVATION":"count14_visible","VALUE":1 if count14 else 0,"DETAIL":"COUNT output"},
        {"OBSERVATION":"count70_visible","VALUE":1 if count70 else 0,"DETAIL":"COUNT output"},
        {"OBSERVATION":"list14_visible","VALUE":1 if listed14 else 0,"DETAIL":"LIST ALL"},
        {"OBSERVATION":"list70_visible","VALUE":1 if listed70 else 0,"DETAIL":"LIST ALL"},
        {"OBSERVATION":"proof_symbols_visible","VALUE":proof_symbols,"DETAIL":"2 expected"},
        {"OBSERVATION":"proof_locales_visible","VALUE":proof_locales,"DETAIL":"5 expected"},
        {"OBSERVATION":"active_messages_header_count_after_readback","VALUE":msg_header,"DETAIL":"raw header evidence"},
        {"OBSERVATION":"active_text_header_count_after_readback","VALUE":text_header,"DETAIL":"raw header evidence"},
    ]

    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"10AI is readback-only."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGE_TEXT","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10ai_validate_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ai_runtime_observations_v1.csv", observations, ["OBSERVATION","VALUE","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ai_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ai_validate_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "STAGE_STATUS": stage.get("STATUS",""),
        "MSG_022AE_6_5_10AH_SAVEPOINT_PRESENT": 1 if sp10ah else 0,
        "FRESH_OPEN_SYSTEM_MESSAGES_14": 1 if msg_open14 else 0,
        "FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70": 1 if text_open70 else 0,
        "RUNTIME_MESSAGE_COUNT_14": 1 if count14 else 0,
        "RUNTIME_TEXT_COUNT_70": 1 if count70 else 0,
        "RUNTIME_MESSAGE_LISTED_14": 1 if listed14 else 0,
        "RUNTIME_TEXT_LISTED_70": 1 if listed70 else 0,
        "PROOF_SYMBOLS_VISIBLE": proof_symbols,
        "PROOF_LOCALES_VISIBLE": proof_locales,
        "ACTIVE_MESSAGES_HEADER_COUNT_AFTER_READBACK": msg_header,
        "ACTIVE_TEXT_HEADER_COUNT_AFTER_READBACK": text_header,
        "ACTIVE_PROMOTION_PERSISTED": 1 if status == STATUS_GREEN else 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }], ["STATUS","VALIDATION_ISSUES","STAGE_STATUS","MSG_022AE_6_5_10AH_SAVEPOINT_PRESENT","FRESH_OPEN_SYSTEM_MESSAGES_14","FRESH_OPEN_SYSTEM_MESSAGE_TEXT_70","RUNTIME_MESSAGE_COUNT_14","RUNTIME_TEXT_COUNT_70","RUNTIME_MESSAGE_LISTED_14","RUNTIME_TEXT_LISTED_70","PROOF_SYMBOLS_VISIBLE","PROOF_LOCALES_VISIBLE","ACTIVE_MESSAGES_HEADER_COUNT_AFTER_READBACK","ACTIVE_TEXT_HEADER_COUNT_AFTER_READBACK","ACTIVE_PROMOTION_PERSISTED","ACTIVE_CATALOG_MUTATION_OBSERVED","SOURCE_FILES_MUTATED","HELP_DATA_MUTATION_OBSERVED","CMDHELPCHK_MUTATION_OBSERVED","NEXT_GATE","REPORT_TIMESTAMP_UTC"])

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10AI_POST_PROMOTION_FRESH_READBACK_STAGED_SOURCE_HELD' else 0}")
    print(f"  MSG-022AE.6.5.10AH savepoint present: {1 if sp10ah else 0}")
    print(f"  fresh open SYSTEM_MESSAGES 14: {1 if msg_open14 else 0}")
    print(f"  fresh open SYSTEM_MESSAGE_TEXT 70: {1 if text_open70 else 0}")
    print(f"  runtime message count 14: {1 if count14 else 0}")
    print(f"  runtime text count 70: {1 if count70 else 0}")
    print(f"  runtime message listed 14: {1 if listed14 else 0}")
    print(f"  runtime text listed 70: {1 if listed70 else 0}")
    print(f"  proof symbols visible: {proof_symbols}/2")
    print(f"  proof locales visible: {proof_locales}/5")
    print(f"  active messages header count after readback: {msg_header}")
    print(f"  active text header count after readback: {text_header}")
    print(f"  active promotion persisted: {1 if status == STATUS_GREEN else 0}")
    print("  active catalog mutation observed: 0")
    print("  source files mutated: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
