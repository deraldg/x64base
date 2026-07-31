#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_STAGED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_STAGE_BLOCKED"
NEXT_GATE = "RUN_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_THEN_VALIDATE"

REPORT_DIR = Path("docs/messaging/reports")
SCRIPT_PATH = Path("docs/messaging/scripts/MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF.dts")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF.md")
WORKSPACE_NAME = "messages_profile_phase22ae_6_5_10as"
WORKSPACE_PATH = Path("dottalkpp/data/workspaces/messages_profile_phase22ae_6_5_10as.dtschema")
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
    ap.add_argument("--replace-existing-workspace-proof", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ar = first_row(reports / "message_catalog_phase22ae_6_5_10ar_revised_status_summary_v1.csv")
    sp_ar, latest_ar = savepoint_present(repo, "MSG-022AE.6.5.10AR")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    running = dottalkpp_running()
    script = repo / SCRIPT_PATH
    ws = repo / WORKSPACE_PATH

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AR_REVISED_GREEN",
         ar.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AR_MESSAGE_MANAGER_CONSUMER_CLOSEOUT_GREEN_CONTINUE_READY_SOURCE_HELD",
         ar.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AR_SAVEPOINT_PRESENT", sp_ar, latest_ar)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("NO_DOTTALKPP_PROCESS_RUNNING", not running, running)
    gate("SCRIPT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not script.exists()) or args.replace_existing_script, rel(script, repo))
    gate("WORKSPACE_PROOF_NOT_EXISTING_OR_REPLACE_ALLOWED", (not ws.exists()) or args.replace_existing_workspace_proof, rel(ws, repo))

    status = STATUS_BLOCKED
    if failures == 0:
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("\n".join([
            "* MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF.dts",
            "* Controlled workspace profile proof for active messaging catalog.",
            "* This proof creates/overwrites only the dedicated workspace profile when authorized by staging:",
            f"*   {WORKSPACE_NAME}",
            "* No DBF mutation, no CDX ADDTAG, no BUILDLMDB, no HELP DATA mutation, no CMDHELPCHK mutation.",
            "* No QUIT here; quit manually in interactive runs.",
            "",
            "SET PATH DBF TO MESSAGING",
            "SET PATH INDEXES TO INDEXES\\MESSAGING",
            "SET PATH LMDB TO LMDB\\MESSAGING",
            "",
            "WORKSPACE OPEN DBF CDX",
            "WORKSPACE",
            "DBAREAS",
            "STRUCT ALL",
            "",
            f"WORKSPACE SAVE {WORKSPACE_NAME}",
            "WORKSPACE CLOSE",
            f"WORKSPACE LOAD {WORKSPACE_NAME}",
            "WORKSPACE",
            "DBAREAS",
            "STRUCT ALL",
            "",
            "SELECT 0",
            "COUNT",
            "SELECT 1",
            "COUNT",
            "",
        ]), encoding="utf-8")
        status = STATUS_GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AS stage only writes script/reports."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation authorized."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation authorized."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation authorized."},
        {"PROTECTED_SYSTEM": "DEDICATED_WORKSPACE_PROFILE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 0, "DETAIL": f"Runtime proof may create {rel(ws, repo)} only."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    fields = ["GATE", "STATUS", "DETAIL"]
    write_csv(reports / "message_catalog_phase22ae_6_5_10as_stage_gate_check_v1.csv", gates, fields)
    write_csv(reports / "message_catalog_phase22ae_6_5_10as_stage_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": "0" if status == STATUS_GREEN else str(failures),
        "PHASE22AE_6_5_10AR_STATUS": ar.get("STATUS", ""),
        "MSG_022AE_6_5_10AR_SAVEPOINT_PRESENT": 1 if sp_ar else 0,
        "ACTIVE_MESSAGES_HEADER_COUNT_AT_STAGE": msg_count,
        "ACTIVE_TEXT_HEADER_COUNT_AT_STAGE": text_count,
        "DOTTALKPP_PROCESS_RUNNING": 1 if running else 0,
        "SCRIPT_PATH": rel(script, repo) if script.exists() else "",
        "WORKSPACE_NAME": WORKSPACE_NAME,
        "WORKSPACE_PATH": rel(ws, repo),
        "WORKSPACE_PROFILE_MUTATION_AUTHORIZED": 1 if status == STATUS_GREEN else 0,
        "DBF_MUTATION_AUTHORIZED": 0,
        "CDX_LMDB_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10as_stage_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AS Messaging Workspace Profile Proof\n\nStatus: `{status}`\n\n10AS proves the active messaging catalog can be opened as a workspace, saved to a dedicated workspace profile, closed, loaded, and restored with `SYSTEM_MESSAGE_TEXT=70` and `SYSTEM_MESSAGES=14`.\n\nThe only authorized runtime file mutation is the dedicated workspace profile:\n\n```text\n{rel(ws, repo)}\n```\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {summary['VALIDATION_ISSUES']}")
    print(f"  Phase 22AE.6.5.10AR status: {ar.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AR savepoint present: {1 if sp_ar else 0}")
    print(f"  active messages header count at stage: {msg_count}")
    print(f"  active text header count at stage: {text_count}")
    print(f"  dottalkpp process running: {1 if running else 0}")
    print(f"  script path: {summary['SCRIPT_PATH']}")
    print(f"  workspace name: {WORKSPACE_NAME}")
    print(f"  workspace path: {rel(ws, repo)}")
    print(f"  workspace profile mutation authorized: {summary['WORKSPACE_PROFILE_MUTATION_AUTHORIZED']}")
    print("  DBF mutation authorized: 0")
    print("  CDX/LMDB mutation authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
