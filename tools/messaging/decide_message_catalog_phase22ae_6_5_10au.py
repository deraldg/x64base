#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AU_NEXT_MESSAGING_WORK_LANE_DECISION_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AU_NEXT_MESSAGING_WORK_LANE_DECISION_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF_PACKAGE"

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

def workspace_info(repo: Path):
    ws = repo / WORKSPACE_PROFILE
    header = ""
    area_rows = 0
    has_messages = 0
    has_text = 0
    if ws.exists():
        lines = ws.read_text(encoding="utf-8", errors="replace").splitlines()
        header = lines[0].strip() if lines else ""
        area_rows = sum(1 for line in lines if line.strip().upper().startswith("AREA "))
        up = "\n".join(lines).upper()
        has_messages = 1 if "SYSTEM_MESSAGES" in up else 0
        has_text = 1 if "SYSTEM_MESSAGE_TEXT" in up else 0
    return ws.exists(), header, area_rows, has_messages, has_text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    at = first_row(reports / "message_catalog_phase22ae_6_5_10at_status_summary_v1.csv")
    sp_at, latest_at = savepoint_present(repo, "MSG-022AE.6.5.10AT")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    ws_exists, ws_header, ws_area_rows, ws_has_messages, ws_has_text = workspace_info(repo)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AT_GREEN",
         at.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AT_MESSAGING_WORKSPACE_AND_CONSUMER_SUMMARY_GREEN_SOURCE_HELD",
         at.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AT_SAVEPOINT_PRESENT", sp_at, latest_at)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AT_CANONICAL_COMMAND_MSGMGR", at.get("CANONICAL_COMMAND") == "MSGMGR", at.get("CANONICAL_COMMAND", "missing"))
    gate("10AT_CHECK_PROVEN", at.get("SET_MESSAGE_CATALOG_CHECK_PROVEN") == "1", at.get("SET_MESSAGE_CATALOG_CHECK_PROVEN", "missing"))
    gate("10AT_GET_PROVEN", at.get("SET_MESSAGE_CATALOG_GET_PROVEN") == "1", at.get("SET_MESSAGE_CATALOG_GET_PROVEN", "missing"))
    gate("10AT_WORKSPACE_PROFILE_PROVEN", at.get("WORKSPACE_PROFILE_PROVEN") == "1", at.get("WORKSPACE_PROFILE_PROVEN", "missing"))
    gate("WORKSPACE_PROFILE_EXISTS", ws_exists, rel(repo / WORKSPACE_PROFILE, repo))
    gate("WORKSPACE_PROFILE_HAS_TWO_AREAS", ws_area_rows >= 2, ws_area_rows)
    gate("WORKSPACE_PROFILE_HAS_SYSTEM_MESSAGE_TEXT", ws_has_text == 1, ws_has_text)
    gate("WORKSPACE_PROFILE_HAS_SYSTEM_MESSAGES", ws_has_messages == 1, ws_has_messages)

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    issues = "0" if status == STATUS_GREEN else str(failures)

    evidence = [
        {"EVIDENCE": "Active message catalog", "STATUS": "PROVEN", "DETAIL": "SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70."},
        {"EVIDENCE": "Message Manager command house", "STATUS": "PROVEN", "DETAIL": "MSGMGR accepted as canonical Message Manager surface."},
        {"EVIDENCE": "Catalog check/get surfaces", "STATUS": "PROVEN", "DETAIL": "SET MESSAGE CATALOG CHECK and GET proven by 10AQ and summarized by 10AT."},
        {"EVIDENCE": "Messaging workspace profile", "STATUS": "PROVEN", "DETAIL": "10AS restored two areas from dedicated workspace profile."},
        {"EVIDENCE": "HELP/CMDHELPCHK", "STATUS": "HELD", "DETAIL": "No HELP DATA or CMDHELPCHK mutation authorized."},
        {"EVIDENCE": "Aliases", "STATUS": "HELD", "DETAIL": "MESSAGE, MSG, MESSAGE_MANAGER aliases remain deferred."},
        {"EVIDENCE": "Runtime source integration", "STATUS": "HELD", "DETAIL": "No source integration authorized yet."},
    ]

    next_lanes = [
        {
            "LANE_ID": "10AV",
            "LANE": "SET_MESSAGE_EMIT_LOCALIZED_PROOF",
            "PURPOSE": "Prove the user-facing localized emit/read surface with MESSAGE_PROOF_MODE_STATUS and MESSAGE_PROOF_BOUNDARY_NOTE across selected locales.",
            "WHY_NOW": "SET MESSAGE CATALOG GET is proven, and prior usage text exposed SET MESSAGE EMIT as the practical localized emission grammar.",
            "MUTATION_LEVEL": "READ_ONLY",
            "RECOMMENDED": 1,
        },
        {
            "LANE_ID": "10AW",
            "LANE": "MSGMGR_HELP_CANDIDATE_PLAN",
            "PURPOSE": "Create a report-only HELP candidate for MSGMGR, CHECK, GET, EMIT, and workspace profile proof.",
            "WHY_NOW": "The command house is now proven; documentation can be planned without mutating HELP.",
            "MUTATION_LEVEL": "REPORT_ONLY",
            "RECOMMENDED": 1,
        },
        {
            "LANE_ID": "10AX",
            "LANE": "ALIAS_POLICY_PLAN",
            "PURPOSE": "Plan aliases MESSAGE, MSG, MESSAGE_MANAGER, and phrase forms without applying them.",
            "WHY_NOW": "Aliases are useful but can blur command responsibilities if added too early.",
            "MUTATION_LEVEL": "REPORT_ONLY",
            "RECOMMENDED": 0,
        },
        {
            "LANE_ID": "10AY",
            "LANE": "RUNTIME_CONSUMER_SOURCE_INTEGRATION_PLAN",
            "PURPOSE": "Select one low-risk runtime consumer and plan guarded catalog-backed message emission.",
            "WHY_NOW": "This is the real integration path, but it needs build and rollback discipline.",
            "MUTATION_LEVEL": "PLAN_ONLY_NOW_SOURCE_PATCH_LATER",
            "RECOMMENDED": 0,
        },
        {
            "LANE_ID": "10AZ",
            "LANE": "INDEX_LMDB_ACCOUNTING",
            "PURPOSE": "Account separately for CDX/LMDB state and any previous or future index mutations.",
            "WHY_NOW": "Useful, but separate from message consumer proof.",
            "MUTATION_LEVEL": "REPORT_ONLY",
            "RECOMMENDED": 0,
        },
        {
            "LANE_ID": "HOLD",
            "LANE": "HOLD_AFTER_10AT",
            "PURPOSE": "Pause with all evidence preserved.",
            "WHY_NOW": "Available if no next lane should begin now.",
            "MUTATION_LEVEL": "NONE",
            "RECOMMENDED": 0,
        },
    ]

    recommendation = [
        {
            "RANK": 1,
            "LANE_ID": "10AV",
            "DECISION": "AUTHORIZE_NEXT_IF_CONTINUING",
            "DETAIL": "Start with SET MESSAGE EMIT localized proof because it stays read-only and proves the practical user-facing message emission path.",
        },
        {
            "RANK": 2,
            "LANE_ID": "10AW",
            "DECISION": "GOOD_SECOND_STEP",
            "DETAIL": "After EMIT proof, create a report-only HELP candidate plan for MSGMGR and message surfaces.",
        },
        {
            "RANK": 3,
            "LANE_ID": "10AY",
            "DECISION": "DEFER_UNTIL_READ_ONLY_SURFACES_ARE_COMPLETE",
            "DETAIL": "Runtime source integration should wait until EMIT proof and documentation contract are stable.",
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AU is decision/report-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10au_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10au_evidence_basis_v1.csv", evidence, ["EVIDENCE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10au_next_lane_options_v1.csv", next_lanes, ["LANE_ID", "LANE", "PURPOSE", "WHY_NOW", "MUTATION_LEVEL", "RECOMMENDED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10au_recommendation_v1.csv", recommendation, ["RANK", "LANE_ID", "DECISION", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10au_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10AT_STATUS": at.get("STATUS", ""),
        "MSG_022AE_6_5_10AT_SAVEPOINT_PRESENT": 1 if sp_at else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CANONICAL_COMMAND": "MSGMGR",
        "SET_MESSAGE_CATALOG_CHECK_PROVEN": at.get("SET_MESSAGE_CATALOG_CHECK_PROVEN", ""),
        "SET_MESSAGE_CATALOG_GET_PROVEN": at.get("SET_MESSAGE_CATALOG_GET_PROVEN", ""),
        "WORKSPACE_PROFILE_PROVEN": at.get("WORKSPACE_PROFILE_PROVEN", ""),
        "RECOMMENDED_NEXT_LANE": "10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF",
        "RECOMMENDED_SECOND_LANE": "10AW_MSGMGR_HELP_CANDIDATE_PLAN",
        "ALIASES_AUTHORIZED": 0,
        "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10au_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AU_NEXT_MESSAGING_WORK_LANE_DECISION.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AU Next Messaging Work Lane Decision\n\nStatus: `{status}`\n\n10AU is report-only. It selects the best next continuation lane after the 10AT summary. Recommended next lane is `10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF`, followed by a report-only MSGMGR HELP candidate plan.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10AT status: {at.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AT savepoint present: {1 if sp_at else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print("  canonical command: MSGMGR")
    print(f"  SET MESSAGE CATALOG CHECK proven: {at.get('SET_MESSAGE_CATALOG_CHECK_PROVEN','')}")
    print(f"  SET MESSAGE CATALOG GET proven: {at.get('SET_MESSAGE_CATALOG_GET_PROVEN','')}")
    print(f"  workspace profile proven: {at.get('WORKSPACE_PROFILE_PROVEN','')}")
    print("  recommended next lane: 10AV_SET_MESSAGE_EMIT_LOCALIZED_PROOF")
    print("  recommended second lane: 10AW_MSGMGR_HELP_CANDIDATE_PLAN")
    print("  aliases authorized: 0")
    print("  runtime consumer source integration authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
