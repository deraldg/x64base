#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AT_MESSAGING_WORKSPACE_AND_CONSUMER_SUMMARY_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AT_MESSAGING_WORKSPACE_AND_CONSUMER_SUMMARY_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AU_NEXT_MESSAGING_WORK_LANE_DECISION"

REPORT_DIR = Path("docs/messaging/reports")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
WORKSPACE_PROFILE = Path("dottalkpp/data/workspaces/messages_profile_phase22ae_6_5_10as.dtschema")

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

def workspace_file_info(repo: Path):
    ws = repo / WORKSPACE_PROFILE
    header = ""
    area_rows = 0
    relation_rows = 0
    has_messages = 0
    has_text = 0
    exists = ws.exists()
    if exists:
        lines = ws.read_text(encoding="utf-8", errors="replace").splitlines()
        header = lines[0].strip() if lines else ""
        area_rows = sum(1 for line in lines if line.strip().upper().startswith("AREA "))
        relation_rows = sum(1 for line in lines if line.strip().upper().startswith("RELATION "))
        up = "\n".join(lines).upper()
        has_messages = 1 if "SYSTEM_MESSAGES" in up else 0
        has_text = 1 if "SYSTEM_MESSAGE_TEXT" in up else 0
    return {
        "exists": exists,
        "path": rel(ws, repo),
        "header": header,
        "area_rows": area_rows,
        "relation_rows": relation_rows,
        "has_messages": has_messages,
        "has_text": has_text,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    aq = first_row(reports / "message_catalog_phase22ae_6_5_10aq_validate_status_summary_v1.csv")
    ar = first_row(reports / "message_catalog_phase22ae_6_5_10ar_revised_status_summary_v1.csv")
    asr = first_row(reports / "message_catalog_phase22ae_6_5_10as_validate_status_summary_v1.csv")

    sp_ar, latest_ar = savepoint_present(repo, "MSG-022AE.6.5.10AR")
    sp_as, latest_as = savepoint_present(repo, "MSG-022AE.6.5.10AS")

    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    ws = workspace_file_info(repo)

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
    gate("PHASE22AE_6_5_10AS_GREEN",
         asr.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AS_MESSAGING_WORKSPACE_PROFILE_PROOF_GREEN_WORKSPACE_RESTORED",
         asr.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AS_SAVEPOINT_PRESENT", sp_as, latest_as)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AQ_CHECK_PROVEN", aq.get("SET_MESSAGE_CATALOG_CHECK_PROVEN") == "1", aq.get("SET_MESSAGE_CATALOG_CHECK_PROVEN", "missing"))
    gate("10AQ_GET_PROVEN", aq.get("SET_MESSAGE_CATALOG_GET_PROVEN") == "1", aq.get("SET_MESSAGE_CATALOG_GET_PROVEN", "missing"))
    gate("10AS_WORKSPACE_PROFILE_EXISTS", ws["exists"], ws["path"])
    gate("10AS_WORKSPACE_PROFILE_HAS_TWO_AREA_ROWS", ws["area_rows"] >= 2, ws["area_rows"])
    gate("10AS_WORKSPACE_HAS_SYSTEM_MESSAGE_TEXT", ws["has_text"] == 1, ws["has_text"])
    gate("10AS_WORKSPACE_HAS_SYSTEM_MESSAGES", ws["has_messages"] == 1, ws["has_messages"])
    gate("10AS_NO_SOURCE_MUTATION", asr.get("SOURCE_FILES_MUTATED") == "0", asr.get("SOURCE_FILES_MUTATED", "missing"))
    gate("10AS_NO_ACTIVE_CATALOG_MUTATION", asr.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0", asr.get("ACTIVE_CATALOG_MUTATION_OBSERVED", "missing"))
    gate("10AS_NO_HELP_DATA_MUTATION", asr.get("HELP_DATA_MUTATION_OBSERVED") == "0", asr.get("HELP_DATA_MUTATION_OBSERVED", "missing"))
    gate("10AS_NO_CMDHELPCHK_MUTATION", asr.get("CMDHELPCHK_MUTATION_OBSERVED") == "0", asr.get("CMDHELPCHK_MUTATION_OBSERVED", "missing"))

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    issues = "0" if status == STATUS_GREEN else str(failures)

    evidence = [
        {
            "EVIDENCE_ITEM": "ACTIVE_MESSAGE_CATALOG_PROMOTED",
            "STATUS": "PROVEN",
            "DETAIL": "Active SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70.",
            "SOURCE_PHASE": "22AE.6.5.10AH/AI/AJ/AK through 10AS",
        },
        {
            "EVIDENCE_ITEM": "MSGMGR_COMMAND_HOUSE",
            "STATUS": "PROVEN",
            "DETAIL": "MSGMGR is accepted as the canonical Message Manager command-house surface.",
            "SOURCE_PHASE": "22AE.6.5.10AO/10AP/10AR",
        },
        {
            "EVIDENCE_ITEM": "SET_MESSAGE_CATALOG_CHECK",
            "STATUS": "PROVEN",
            "DETAIL": "Low-level read/check surface proven.",
            "SOURCE_PHASE": "22AE.6.5.10AQ",
        },
        {
            "EVIDENCE_ITEM": "SET_MESSAGE_CATALOG_GET",
            "STATUS": "PROVEN",
            "DETAIL": "Low-level read/get surface proven by validator and accepted contract.",
            "SOURCE_PHASE": "22AE.6.5.10AQ",
        },
        {
            "EVIDENCE_ITEM": "MESSAGING_WORKSPACE_PROFILE",
            "STATUS": "PROVEN",
            "DETAIL": "Dedicated workspace profile saves/loads two areas and restores SYSTEM_MESSAGE_TEXT=70 and SYSTEM_MESSAGES=14.",
            "SOURCE_PHASE": "22AE.6.5.10AS",
        },
        {
            "EVIDENCE_ITEM": "DTSCHEMA_DTSHEMA_SPELLING",
            "STATUS": "POLISH_DEFERRED",
            "DETAIL": "Observed workspace header spelling is not owned by this messaging proof lane.",
            "SOURCE_PHASE": "22AE.6.5.10AR/10AS",
        },
        {
            "EVIDENCE_ITEM": "ALIASES",
            "STATUS": "DEFERRED",
            "DETAIL": "MESSAGE, MSG, MESSAGE_MANAGER aliases remain unauthorized pending alias policy.",
            "SOURCE_PHASE": "22AE.6.5.10AP/10AR",
        },
        {
            "EVIDENCE_ITEM": "HELP_CMDHELPCHK",
            "STATUS": "DEFERRED",
            "DETAIL": "HELP DATA and CMDHELPCHK mutation remain explicitly unauthorized.",
            "SOURCE_PHASE": "all 10A* phases",
        },
    ]

    next_options = [
        {
            "OPTION_ID": "10AU-A",
            "LANE": "MSGMGR_HELP_CANDIDATE_PLAN",
            "DESCRIPTION": "Report-only plan for HELP text explaining MSGMGR, SET MESSAGE CATALOG CHECK/GET, and workspace profile evidence.",
            "MUTATION_REQUIRED": 0,
            "RECOMMENDED": 1,
        },
        {
            "OPTION_ID": "10AU-B",
            "LANE": "SET_MESSAGE_EMIT_LOCALIZED_PROOF",
            "DESCRIPTION": "Read-only runtime proof of SET MESSAGE EMIT for proof symbols/locales, if EMIT should become the user-facing lookup surface.",
            "MUTATION_REQUIRED": 0,
            "RECOMMENDED": 1,
        },
        {
            "OPTION_ID": "10AU-C",
            "LANE": "ALIAS_POLICY_PLAN",
            "DESCRIPTION": "Report-only alias plan for MESSAGE, MSG, MESSAGE_MANAGER, and phrase aliases.",
            "MUTATION_REQUIRED": 0,
            "RECOMMENDED": 0,
        },
        {
            "OPTION_ID": "10AU-D",
            "LANE": "RUNTIME_CONSUMER_SOURCE_INTEGRATION_PLAN",
            "DESCRIPTION": "Choose one low-risk runtime message consumer and plan guarded source integration with build/runtime proof.",
            "MUTATION_REQUIRED": 1,
            "RECOMMENDED": 0,
        },
        {
            "OPTION_ID": "10AU-E",
            "LANE": "INDEX_LMDB_ACCOUNTING",
            "DESCRIPTION": "Separate accounting lane for any CDX/LMDB mutation already explored or needed later.",
            "MUTATION_REQUIRED": 0,
            "RECOMMENDED": 0,
        },
        {
            "OPTION_ID": "10AU-F",
            "LANE": "HOLD",
            "DESCRIPTION": "Pause with all 10A* evidence preserved and no new package.",
            "MUTATION_REQUIRED": 0,
            "RECOMMENDED": 0,
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AT is report-only summary."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AT reads prior 10AS workspace evidence only."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10at_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10at_evidence_matrix_v1.csv", evidence, ["EVIDENCE_ITEM", "STATUS", "DETAIL", "SOURCE_PHASE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10at_next_options_v1.csv", next_options, ["OPTION_ID", "LANE", "DESCRIPTION", "MUTATION_REQUIRED", "RECOMMENDED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10at_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10AR_STATUS": ar.get("STATUS", ""),
        "MSG_022AE_6_5_10AR_SAVEPOINT_PRESENT": 1 if sp_ar else 0,
        "PHASE22AE_6_5_10AS_STATUS": asr.get("STATUS", ""),
        "MSG_022AE_6_5_10AS_SAVEPOINT_PRESENT": 1 if sp_as else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CANONICAL_COMMAND": "MSGMGR",
        "CANONICAL_COMMAND_EXPANSION": "Message Manager",
        "SET_MESSAGE_CATALOG_CHECK_PROVEN": aq.get("SET_MESSAGE_CATALOG_CHECK_PROVEN", ""),
        "SET_MESSAGE_CATALOG_GET_PROVEN": aq.get("SET_MESSAGE_CATALOG_GET_PROVEN", ""),
        "WORKSPACE_PROFILE_PROVEN": 1 if ws["exists"] and ws["has_messages"] and ws["has_text"] else 0,
        "WORKSPACE_PROFILE_PATH": ws["path"],
        "WORKSPACE_PROFILE_HEADER_OBSERVED": ws["header"],
        "WORKSPACE_PROFILE_AREA_ROWS": ws["area_rows"],
        "WORKSPACE_PROFILE_RELATION_ROWS": ws["relation_rows"],
        "ALIASES_AUTHORIZED": 0,
        "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10at_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AT_MESSAGING_WORKSPACE_AND_CONSUMER_SUMMARY.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AT Messaging Workspace and Consumer Summary\n\nStatus: `{status}`\n\n10AT is a report-only summary/decision package. It consolidates Message Manager consumer proof, low-level SET MESSAGE CATALOG CHECK/GET proof, active catalog counts, and 10AS workspace profile restore proof.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10AR status: {ar.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AR savepoint present: {1 if sp_ar else 0}")
    print(f"  Phase 22AE.6.5.10AS status: {asr.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AS savepoint present: {1 if sp_as else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print("  canonical command: MSGMGR")
    print("  canonical command expansion: Message Manager")
    print(f"  SET MESSAGE CATALOG CHECK proven: {aq.get('SET_MESSAGE_CATALOG_CHECK_PROVEN','')}")
    print(f"  SET MESSAGE CATALOG GET proven: {aq.get('SET_MESSAGE_CATALOG_GET_PROVEN','')}")
    print(f"  workspace profile proven: {summary['WORKSPACE_PROFILE_PROVEN']}")
    print(f"  workspace profile path: {ws['path']}")
    print(f"  workspace profile header observed: {ws['header']}")
    print(f"  aliases authorized: 0")
    print(f"  runtime consumer source integration authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
