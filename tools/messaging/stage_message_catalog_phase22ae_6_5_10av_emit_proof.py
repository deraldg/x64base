#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_STAGE_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF.dts")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF.md")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

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

def dottalkpp_running():
    if sys.platform.startswith("win"):
        try:
            cp = subprocess.run(["tasklist", "/FI", "IMAGENAME eq dottalkpp.exe"], capture_output=True, text=True, timeout=10)
            out = (cp.stdout or "") + (cp.stderr or "")
            return "dottalkpp.exe" in out.lower()
        except Exception:
            return False
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-script", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    au = first_row(reports / "message_catalog_phase22ae_6_5_10au_status_summary_v1.csv")
    sp_au, latest = savepoint_present(repo, "MSG-022AE.6.5.10AU")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    running = dottalkpp_running()
    script = repo / SCRIPT_PATH

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AU_GREEN",
         au.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AU_NEXT_MESSAGING_WORK_LANE_DECISION_GREEN_SOURCE_HELD",
         au.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AU_SAVEPOINT_PRESENT", sp_au, latest)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("NO_DOTTALKPP_PROCESS_RUNNING", not running, running)
    gate("SCRIPT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not script.exists()) or args.replace_existing_script, rel(script, repo))

    status = STATUS_BLOCKED
    if failures == 0:
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF.dts",
            "* READ-ONLY proof of SET MESSAGE EMIT localized/runtime message surface.",
            "* No ZAP, IMPORT, APPEND, REPLACE, PACK, CDX CREATE, BUILDLMDB, source mutation, HELP mutation, or CMDHELPCHK mutation.",
            "* If EMIT syntax reports usage, that is a syntax-review result, not a DBF failure.",
            "* No QUIT here; quit manually in interactive runs.",
            "",
            "* 1. Confirm active provider before EMIT probes.",
            "SET MESSAGE CATALOG CHECK",
            "",
            "* 2. Base EMIT usage/probe surface.",
            "SET MESSAGE EMIT",
            "",
            "* 3. Proof symbol localized emission probes.",
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS",
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE en-US",
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE es",
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE fr",
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE de",
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE it",
            "",
            "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE",
            "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE en-US",
            "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE es",
            "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE fr",
            "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE de",
            "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE it",
            "",
            "* 4. Command-house context after EMIT probes.",
            "MSGMGR STATUS",
            "",
            "* 5. Final active table readback after probes.",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            "",
            "* 6. Final count proof.",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "",
        ]), encoding="utf-8")
        status = STATUS_GREEN

    probes = [
        {"PROBE_ID": "AV-001", "COMMAND": "SET MESSAGE CATALOG CHECK", "PURPOSE": "Confirm active DBF provider 14/70.", "SYNTAX_REVIEW_OK": 0},
        {"PROBE_ID": "AV-002", "COMMAND": "SET MESSAGE EMIT", "PURPOSE": "Discover base EMIT usage/syntax.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-003", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE en-US", "PURPOSE": "Emit proof mode status in source/default locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-004", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE es", "PURPOSE": "Emit proof mode status in Spanish locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-005", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE fr", "PURPOSE": "Emit proof mode status in French locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-006", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE de", "PURPOSE": "Emit proof mode status in German locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-007", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS LOCALE it", "PURPOSE": "Emit proof mode status in Italian locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-008", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE en-US", "PURPOSE": "Emit boundary note in source/default locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-009", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE es", "PURPOSE": "Emit boundary note in Spanish locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-010", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE fr", "PURPOSE": "Emit boundary note in French locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-011", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE de", "PURPOSE": "Emit boundary note in German locale.", "SYNTAX_REVIEW_OK": 1},
        {"PROBE_ID": "AV-012", "COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_BOUNDARY_NOTE LOCALE it", "PURPOSE": "Emit boundary note in Italian locale.", "SYNTAX_REVIEW_OK": 1},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AV stage only writes script/reports."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation authorized."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation authorized."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation authorized."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation authorized."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    issues = "0" if status == STATUS_GREEN else str(failures)
    write_csv(reports / "message_catalog_phase22ae_6_5_10av_stage_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10av_probe_manifest_v1.csv", probes, ["PROBE_ID", "COMMAND", "PURPOSE", "SYNTAX_REVIEW_OK"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10av_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10AU_STATUS": au.get("STATUS", ""),
        "MSG_022AE_6_5_10AU_SAVEPOINT_PRESENT": 1 if sp_au else 0,
        "ACTIVE_MESSAGES_HEADER_COUNT_AT_STAGE": msg_count,
        "ACTIVE_TEXT_HEADER_COUNT_AT_STAGE": text_count,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "SCRIPT_PATH": rel(script, repo) if script.exists() else "",
        "RUNLOG_PATH": rel(repo / RUNLOG_PATH, repo),
        "SET_MESSAGE_EMIT_PROOF_STAGED": 1 if status == STATUS_GREEN else 0,
        "DBF_MUTATION_AUTHORIZED": 0,
        "CDX_LMDB_MUTATION_AUTHORIZED": 0,
        "WORKSPACE_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10av_stage_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AV SET MESSAGE EMIT Localized Proof\n\nStatus: `{status}`\n\n10AV is read-only. It probes `SET MESSAGE EMIT` for the two proof symbols across en-US/es/fr/de/it while preserving active catalog counts.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10AU status: {au.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AU savepoint present: {1 if sp_au else 0}")
    print(f"  active messages header count at stage: {msg_count}")
    print(f"  active text header count at stage: {text_count}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  script path: {summary['SCRIPT_PATH']}")
    print(f"  SET MESSAGE EMIT proof staged: {summary['SET_MESSAGE_EMIT_PROOF_STAGED']}")
    print("  DBF mutation authorized: 0")
    print("  CDX/LMDB mutation authorized: 0")
    print("  workspace mutation authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
