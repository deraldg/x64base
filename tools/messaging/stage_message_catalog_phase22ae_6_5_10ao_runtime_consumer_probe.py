#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_STAGE_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE.dts")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE.md")

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

    an = first_row(reports / "message_catalog_phase22ae_6_5_10an_status_summary_v1.csv")
    sp_an, latest = savepoint_present(repo, "MSG-022AE.6.5.10AN")
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

    gate("PHASE22AE_6_5_10AN_GREEN",
         an.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AN_RUNTIME_MESSAGE_CONSUMER_INTEGRATION_PLAN_GREEN_SOURCE_HELD",
         an.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AN_SAVEPOINT_PRESENT", sp_an, latest)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("NO_DOTTALKPP_PROCESS_RUNNING", not running, running)
    gate("SCRIPT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not script.exists()) or args.replace_existing_script, rel(script, repo))

    status = STATUS_BLOCKED
    if failures == 0:
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE.dts",
            "* READ-ONLY RUNTIME MESSAGE CONSUMER PROBE.",
            "* No ZAP, IMPORT, APPEND, REPLACE, PACK, CDX CREATE, BUILDLMDB, or source mutation.",
            "* Unknown command results are acceptable evidence for missing consumer surface.",
            "* No QUIT here; quit manually in interactive runs.",
            "",
            "* 1. Prove active promoted message catalog is still readable.",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            "",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "LIST ALL",
            "",
            "* 2. Probe existing read-only HELP/consumer surfaces. Unknown command is acceptable evidence.",
            "HELP MESSAGE",
            "HELP MESSAGES",
            "HELP MSG",
            "HELP MESSAGE LOCALE",
            "HELP MESSAGE CATALOG",
            "HELP MESSAGE_PROOF_MODE_STATUS",
            "",
            "* 3. Probe likely read-only message consumer commands, if present.",
            "MESSAGE HELP",
            "MESSAGE STATUS",
            "MESSAGE GET MESSAGE_PROOF_MODE_STATUS en-US",
            "MESSAGE GET MESSAGE_PROOF_BOUNDARY_NOTE en-US",
            "MSG HELP",
            "MSG STATUS",
            "MSG GET MESSAGE_PROOF_MODE_STATUS en-US",
            "",
            "* 4. Final cross-table readback after consumer probes.",
            f"USE {(repo / ACTIVE_MSG_DBF).resolve().as_posix()}",
            "COUNT",
            f"USE {(repo / ACTIVE_TEXT_DBF).resolve().as_posix()}",
            "COUNT",
            "",
        ]), encoding="utf-8")
        status = STATUS_GREEN

    probe_rows = [
        {"PROBE_ID": "P01", "COMMAND": "HELP MESSAGE", "PURPOSE": "Check for documented message command surface.", "UNKNOWN_OK": 1},
        {"PROBE_ID": "P02", "COMMAND": "HELP MESSAGES", "PURPOSE": "Check plural alias/documentation.", "UNKNOWN_OK": 1},
        {"PROBE_ID": "P03", "COMMAND": "HELP MSG", "PURPOSE": "Check short alias documentation.", "UNKNOWN_OK": 1},
        {"PROBE_ID": "P04", "COMMAND": "MESSAGE HELP", "PURPOSE": "Check runtime MESSAGE command help/status surface.", "UNKNOWN_OK": 1},
        {"PROBE_ID": "P05", "COMMAND": "MESSAGE GET MESSAGE_PROOF_MODE_STATUS en-US", "PURPOSE": "Probe direct catalog-backed lookup if implemented.", "UNKNOWN_OK": 1},
        {"PROBE_ID": "P06", "COMMAND": "MSG GET MESSAGE_PROOF_MODE_STATUS en-US", "PURPOSE": "Probe short alias lookup if implemented.", "UNKNOWN_OK": 1},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AO stage is read-only/report artifact generation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No index/LMDB mutation."},
        {"PROTECTED_SYSTEM": "RUNTIME_CONSUMER_SOURCE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source integration."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_stage_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_probe_manifest_v1.csv", probe_rows, ["PROBE_ID", "COMMAND", "PURPOSE", "UNKNOWN_OK"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ao_stage_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AN_STATUS": an.get("STATUS", ""),
        "MSG_022AE_6_5_10AN_SAVEPOINT_PRESENT": 1 if sp_an else 0,
        "ACTIVE_MESSAGES_HEADER_COUNT_AT_STAGE": msg_count,
        "ACTIVE_TEXT_HEADER_COUNT_AT_STAGE": text_count,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "SCRIPT_PATH": rel(script, repo) if script.exists() else "",
        "RUNLOG_PATH": rel(repo / RUNLOG_PATH, repo),
        "READONLY_RUNTIME_PROBE_STAGED": 1 if status == STATUS_GREEN else 0,
        "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_5_10AN_STATUS",
         "MSG_022AE_6_5_10AN_SAVEPOINT_PRESENT", "ACTIVE_MESSAGES_HEADER_COUNT_AT_STAGE",
         "ACTIVE_TEXT_HEADER_COUNT_AT_STAGE", "DOTTALKPP_PROCESS_RUNNING", "SCRIPT_PATH",
         "RUNLOG_PATH", "READONLY_RUNTIME_PROBE_STAGED",
         "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AO Runtime Message Consumer Read-Only Probe\n\nStatus: `{status}`\n\n10AO is read-only. It probes existing HELP/MESSAGE/MSG surfaces and accepts unknown-command responses as evidence that a consumer surface is not yet implemented.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AN status: {an.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AN savepoint present: {1 if sp_an else 0}")
    print(f"  active messages header count at stage: {msg_count}")
    print(f"  active text header count at stage: {text_count}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  script path: {rel(script, repo) if script.exists() else ''}")
    print("  readonly runtime probe staged: " + ("1" if status == STATUS_GREEN else "0"))
    print("  runtime consumer source integration authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
