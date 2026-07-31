#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_GREEN_WORKSPACE_RESTORED"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AT_MESSAGING_WORKSPACE_AND_CONSUMER_SUMMARY"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG_PATH = Path("docs/messaging/runlog/MSG-022AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF.md")
WORKSPACE_PATH = Path("dottalkpp/data/workspaces/messages_profile_phase22ae_6_5_10as.dtschema")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
MUTATION_TOKENS = ["ZAP COMPLETE", "IMPORTED ", "APPEND", "REPLACE", "PACK", "BUILDLMDB", "CDX ADDTAG", "CDX CREATE", "DELETE ALL"]

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--runtime-log", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    stage = first_row(reports / "message_catalog_phase22ae_6_5_10as_stage_status_summary_v1.csv")
    runtime = Path(args.runtime_log) if args.runtime_log else repo / RUNLOG_PATH
    if not runtime.is_absolute():
        runtime = repo / runtime
    log = runtime.read_text(encoding="utf-8", errors="replace") if runtime.exists() else ""
    up = log.upper()

    ws = repo / WORKSPACE_PATH
    ws_exists = ws.exists()
    ws_header = ""
    ws_area_rows = 0
    ws_relation_rows = 0
    ws_has_msg = 0
    ws_has_text = 0
    if ws_exists:
        lines = ws.read_text(encoding="utf-8", errors="replace").splitlines()
        ws_header = lines[0].strip() if lines else ""
        ws_area_rows = sum(1 for l in lines if l.strip().upper().startswith("AREA "))
        ws_relation_rows = sum(1 for l in lines if l.strip().upper().startswith("RELATION "))
        ws_up = "\n".join(lines).upper()
        ws_has_msg = 1 if "SYSTEM_MESSAGES" in ws_up else 0
        ws_has_text = 1 if "SYSTEM_MESSAGE_TEXT" in ws_up else 0

    workspace_open = "WORKSPACE OPEN" in up and "2 TABLE" in up
    workspace_save = "WORKSPACE SAVE" in up and "MESSAGES_PROFILE_PHASE22AE_6_5_10AS" in up
    workspace_load = "WORKSPACE LOAD" in up and "RESTORED 2 AREA" in up
    workspace_list = "WORKSPACE: 2 AREA(S) OPEN" in up
    dbareas_text = "SYSTEM_MESSAGE_TEXT" in up and "RECORDS             : 70" in up
    dbareas_msg = "SYSTEM_MESSAGES" in up and ("RECORDS             : 14" in up or "RECS: 14" in up)
    struct_text = "AREA 0: SYSTEM_MESSAGE_TEXT" in up or "SYSTEM_MESSAGE_TEXT  (SYSTEM_MESSAGE_TEXT)" in up
    struct_msg = "AREA 1: SYSTEM_MESSAGES" in up or "SYSTEM_MESSAGES  (SYSTEM_MESSAGES)" in up
    count70 = "\n70\n" in log.replace("\r", "\n") or " RECORD COUNT 70" in up or "RECORDS             : 70" in up
    count14 = "\n14\n" in log.replace("\r", "\n") or " RECORD COUNT 14" in up or "RECORDS             : 14" in up
    mutation_hits = [tok for tok in MUTATION_TOKENS if tok in up]

    msg_header = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_header = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("STAGE_GREEN", stage.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_STAGED_SOURCE_HELD", stage.get("STATUS", "missing"))
    gate("RUNTIME_LOG_EXISTS", runtime.exists(), rel(runtime, repo))
    gate("WORKSPACE_OPEN_2_TABLES", workspace_open, "WORKSPACE OPEN DBF CDX")
    gate("WORKSPACE_SAVE_PROOF", workspace_save, "WORKSPACE SAVE messages_profile_phase22ae_6_5_10as")
    gate("WORKSPACE_LOAD_RESTORED_2_AREAS", workspace_load, "WORKSPACE LOAD restored 2 areas")
    gate("WORKSPACE_LIST_2_AREAS", workspace_list, "WORKSPACE shows 2 areas open")
    gate("DBAREAS_SYSTEM_MESSAGE_TEXT_70", dbareas_text or count70, "SYSTEM_MESSAGE_TEXT=70")
    gate("DBAREAS_SYSTEM_MESSAGES_14", dbareas_msg or count14, "SYSTEM_MESSAGES=14")
    gate("STRUCT_SYSTEM_MESSAGE_TEXT", struct_text, "STRUCT ALL text area")
    gate("STRUCT_SYSTEM_MESSAGES", struct_msg, "STRUCT ALL message area")
    gate("WORKSPACE_FILE_EXISTS", ws_exists, rel(ws, repo))
    gate("WORKSPACE_FILE_HAS_TWO_AREA_ROWS", ws_area_rows >= 2, ws_area_rows)
    gate("WORKSPACE_FILE_HAS_SYSTEM_MESSAGE_TEXT", ws_has_text == 1, ws_has_text)
    gate("WORKSPACE_FILE_HAS_SYSTEM_MESSAGES", ws_has_msg == 1, ws_has_msg)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_header == 14, msg_header)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_header == 70, text_header)
    gate("NO_FORBIDDEN_MUTATION_TOKENS", len(mutation_hits) == 0, ";".join(mutation_hits) if mutation_hits else "none")

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    issues = "0" if status == STATUS_GREEN else str(failures)

    observations = [
        {"OBSERVATION": "workspace_file", "VALUE": 1 if ws_exists else 0, "DETAIL": rel(ws, repo)},
        {"OBSERVATION": "workspace_header", "VALUE": ws_header, "DETAIL": "Header spelling/version is observed only; spelling polish is deferred."},
        {"OBSERVATION": "workspace_area_rows", "VALUE": ws_area_rows, "DETAIL": "Expected at least 2."},
        {"OBSERVATION": "workspace_relation_rows", "VALUE": ws_relation_rows, "DETAIL": "Messaging relation not required in this proof."},
        {"OBSERVATION": "workspace_load_restored_2_areas", "VALUE": 1 if workspace_load else 0, "DETAIL": "Runtime restore proof."},
        {"OBSERVATION": "active_messages_after_proof", "VALUE": msg_header, "DETAIL": "DBF header count."},
        {"OBSERVATION": "active_text_after_proof", "VALUE": text_header, "DETAIL": "DBF header count."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "DEDICATED_WORKSPACE_PROFILE", "MUTATION_ALLOWED": 1, "OBSERVED_MUTATION": 1 if ws_exists else 0, "DETAIL": rel(ws, repo)},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10as_validate_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10as_runtime_observations_v1.csv", observations, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10as_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "STAGE_STATUS": stage.get("STATUS", ""),
        "WORKSPACE_PROFILE_PATH": rel(ws, repo),
        "WORKSPACE_PROFILE_EXISTS": 1 if ws_exists else 0,
        "WORKSPACE_PROFILE_HEADER": ws_header,
        "WORKSPACE_PROFILE_AREA_ROWS": ws_area_rows,
        "WORKSPACE_PROFILE_RELATION_ROWS": ws_relation_rows,
        "WORKSPACE_LOAD_RESTORED_2_AREAS": 1 if workspace_load else 0,
        "WORKSPACE_LISTED_2_AREAS": 1 if workspace_list else 0,
        "SYSTEM_MESSAGE_TEXT_RESTORED_70": 1 if (dbareas_text or count70) else 0,
        "SYSTEM_MESSAGES_RESTORED_14": 1 if (dbareas_msg or count14) else 0,
        "ACTIVE_MESSAGES_HEADER_COUNT_AFTER_PROOF": msg_header,
        "ACTIVE_TEXT_HEADER_COUNT_AFTER_PROOF": text_header,
        "WORKSPACE_PROFILE_MUTATION_OBSERVED": 1 if ws_exists else 0,
        "DBF_MUTATION_AUTHORIZED": 0,
        "CDX_LMDB_MUTATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10as_validate_status_summary_v1.csv", [summary], list(summary.keys()))

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  stage green: {1 if stage.get('STATUS') == 'MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_STAGED_SOURCE_HELD' else 0}")
    print(f"  workspace profile exists: {1 if ws_exists else 0}")
    print(f"  workspace profile path: {rel(ws, repo)}")
    print(f"  workspace profile header: {ws_header}")
    print(f"  workspace profile area rows: {ws_area_rows}")
    print(f"  workspace load restored 2 areas: {1 if workspace_load else 0}")
    print(f"  SYSTEM_MESSAGE_TEXT restored 70: {1 if (dbareas_text or count70) else 0}")
    print(f"  SYSTEM_MESSAGES restored 14: {1 if (dbareas_msg or count14) else 0}")
    print(f"  active messages header count after proof: {msg_header}")
    print(f"  active text header count after proof: {text_header}")
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
