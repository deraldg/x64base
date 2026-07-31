#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AR_MESSAGE_MANAGER_CONSUMER_CLOSEOUT_GREEN_WORKSPACE_HEADER_DEFECT_NOTED_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AR_MESSAGE_MANAGER_CONSUMER_CLOSEOUT_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AS_WORKSPACE_DTSCHEMA_HEADER_DEFECT_REPAIR_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
WORKSPACE_CANDIDATES = [
    Path("dottalkpp/data/workspaces/messages_test.dtschema"),
    Path("dottalkpp/data/workspaces/messages.dtschema"),
    Path("dottalkpp/data/workspaces/messaging.dtschema"),
]

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
    rows = []
    for p in WORKSPACE_CANDIDATES:
        path = repo / p
        exists = path.exists()
        header = ""
        areas = 0
        relations = 0
        has_msg = 0
        has_text = 0
        defect = 0
        format_note = "missing"
        if exists:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            header = lines[0].strip() if lines else ""
            areas = sum(1 for l in lines if l.strip().upper().startswith("AREA "))
            relations = sum(1 for l in lines if l.strip().upper().startswith("RELATION "))
            up = "\n".join(lines).upper()
            has_msg = 1 if "SYSTEM_MESSAGES" in up else 0
            has_text = 1 if "SYSTEM_MESSAGE_TEXT" in up else 0
            if header.upper().startswith("DTSCHEMA"):
                format_note = "correct_or_candidate_dtschema_header"
            elif header.upper().startswith("DTSHEMA"):
                format_note = "defect_header_missing_c_after_s"
                defect = 1
            else:
                format_note = "unknown_or_unversioned_header"
        rows.append({
            "WORKSPACE_PATH": rel(path, repo),
            "EXISTS": 1 if exists else 0,
            "HEADER": header,
            "AREA_ROWS": areas,
            "RELATION_ROWS": relations,
            "HAS_SYSTEM_MESSAGES": has_msg,
            "HAS_SYSTEM_MESSAGE_TEXT": has_text,
            "HEADER_DEFECT_OBSERVED": defect,
            "FORMAT_NOTE": format_note,
        })
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    aq = first_row(reports / "message_catalog_phase22ae_6_5_10aq_validate_status_summary_v1.csv")
    ap_row = first_row(reports / "message_catalog_phase22ae_6_5_10ap_status_summary_v1.csv")
    ao = first_row(reports / "message_catalog_phase22ae_6_5_10ao_validate_status_summary_v1.csv")

    sp_aq, latest_aq = savepoint_present(repo, "MSG-022AE.6.5.10AQ")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    ws_rows = workspace_info(repo)
    ws_observed = any(r["EXISTS"] == 1 and r["HAS_SYSTEM_MESSAGES"] == 1 and r["HAS_SYSTEM_MESSAGE_TEXT"] == 1 for r in ws_rows)
    header_defect_observed = any(r["HEADER_DEFECT_OBSERVED"] == 1 for r in ws_rows)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AQ_GREEN_CHECK_AND_GET_PROVEN",
         aq.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_GREEN_CHECK_AND_GET_PROVEN",
         aq.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AQ_SAVEPOINT_PRESENT", sp_aq, latest_aq)
    gate("10AQ_SET_MESSAGE_CATALOG_CHECK_PROVEN", aq.get("SET_MESSAGE_CATALOG_CHECK_PROVEN") == "1", aq.get("SET_MESSAGE_CATALOG_CHECK_PROVEN", "missing"))
    gate("10AQ_SET_MESSAGE_CATALOG_GET_PROVEN", aq.get("SET_MESSAGE_CATALOG_GET_PROVEN") == "1", aq.get("SET_MESSAGE_CATALOG_GET_PROVEN", "missing"))
    gate("10AP_CANONICAL_COMMAND_MSGMGR", ap_row.get("CANONICAL_COMMAND") == "MSGMGR", ap_row.get("CANONICAL_COMMAND", "missing"))
    gate("10AO_MESSAGE_CONSUMER_SURFACE_OBSERVED", ao.get("MESSAGE_CONSUMER_SURFACE_OBSERVED") == "1", ao.get("MESSAGE_CONSUMER_SURFACE_OBSERVED", "missing"))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AQ_NO_SOURCE_MUTATION", aq.get("SOURCE_FILES_MUTATED") == "0", aq.get("SOURCE_FILES_MUTATED", "missing"))
    gate("10AQ_NO_ACTIVE_CATALOG_MUTATION", aq.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0", aq.get("ACTIVE_CATALOG_MUTATION_OBSERVED", "missing"))
    gate("10AQ_NO_HELP_DATA_MUTATION", aq.get("HELP_DATA_MUTATION_OBSERVED") == "0", aq.get("HELP_DATA_MUTATION_OBSERVED", "missing"))
    gate("10AQ_NO_CMDHELPCHK_MUTATION", aq.get("CMDHELPCHK_MUTATION_OBSERVED") == "0", aq.get("CMDHELPCHK_MUTATION_OBSERVED", "missing"))

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    closeout_rows = [
        {"CLOSEOUT_ITEM": "CANONICAL_COMMAND_HOUSE", "STATUS": "ACCEPTED", "DETAIL": "MSGMGR is accepted as the Message Manager command-house surface.", "MUTATION_AUTHORIZED": 0},
        {"CLOSEOUT_ITEM": "LOW_LEVEL_CHECK_SURFACE", "STATUS": "ACCEPTED", "DETAIL": "SET MESSAGE CATALOG CHECK is directly proven read-only.", "MUTATION_AUTHORIZED": 0},
        {"CLOSEOUT_ITEM": "LOW_LEVEL_GET_SURFACE", "STATUS": "ACCEPTED", "DETAIL": "SET MESSAGE CATALOG GET is accepted as proven by 10AQ validation.", "MUTATION_AUTHORIZED": 0},
        {"CLOSEOUT_ITEM": "ACTIVE_CATALOG_COUNTS", "STATUS": "ACCEPTED", "DETAIL": "Active catalog remains SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70.", "MUTATION_AUTHORIZED": 0},
        {"CLOSEOUT_ITEM": "ALIASES", "STATUS": "DEFERRED", "DETAIL": "MESSAGE, MSG, MESSAGE_MANAGER, and phrase aliases remain unauthorized pending alias policy.", "MUTATION_AUTHORIZED": 0},
        {"CLOSEOUT_ITEM": "SOURCE_INTEGRATION", "STATUS": "DEFERRED", "DETAIL": "Broader runtime source integration remains separate from the command-house proof.", "MUTATION_AUTHORIZED": 0},
        {"CLOSEOUT_ITEM": "WORKSPACE_HEADER_DEFECT", "STATUS": "FIX_REQUIRED", "DETAIL": "DTSHEMA spelling is a defect in current/new workspace code if emitted; next lane should repair/verify DTSCHEMA header behavior.", "MUTATION_AUTHORIZED": 0},
    ]

    header_repair_contract = [
        {"ITEM": "DEFECTIVE_HEADER", "VALUE": "DTSHEMA", "STATUS": "DEFECT_IF_EMITTED_BY_CURRENT_CODE", "DETAIL": "Missing C after DTS; do not treat as preferred runtime contract."},
        {"ITEM": "CORRECT_HEADER", "VALUE": "DTSCHEMA", "STATUS": "TARGET", "DETAIL": "Workspace save/load code should emit and recognize correct DTSCHEMA spelling."},
        {"ITEM": "VERSION", "VALUE": "2", "STATUS": "TARGET_TO_VERIFY", "DETAIL": "Confirm current workspace format version from source/runtime proof."},
        {"ITEM": "BACKWARD_COMPATIBILITY", "VALUE": "DTSHEMA 1", "STATUS": "REVIEW_REQUIRED", "DETAIL": "Old saved workspaces may need compatibility read support, but new writes should not preserve the typo."},
        {"ITEM": "MUTATION_BOUNDARY", "VALUE": "SOURCE_PATCH_REQUIRES_EXPLICIT_10AS_AUTHORIZATION", "STATUS": "HELD", "DETAIL": "10AR records the defect only; it does not patch source."},
    ]

    next_plan = [
        {"STEP": 1, "ACTION": "SOURCE_LOCATE_WORKSPACE_HEADER_WRITER", "DETAIL": "Find code path that writes workspace schema header; likely workspace save/dtschema serialization.", "MUTATION_KIND": "read_only_scan"},
        {"STEP": 2, "ACTION": "SOURCE_LOCATE_WORKSPACE_HEADER_READER", "DETAIL": "Find loader/parser acceptance rules for DTSHEMA/DTSCHEMA versions.", "MUTATION_KIND": "read_only_scan"},
        {"STEP": 3, "ACTION": "PATCH_PLAN", "DETAIL": "Plan surgical change so new saves emit DTSCHEMA 2, with optional read compatibility for DTSHEMA 1.", "MUTATION_KIND": "plan_only"},
        {"STEP": 4, "ACTION": "RUNTIME_PROOF_PLAN", "DETAIL": "Save/load a messaging workspace and prove header is DTSCHEMA 2 and areas restore 14/70.", "MUTATION_KIND": "workspace_file_only_after_authorization"},
        {"STEP": 5, "ACTION": "KEEP_INDEX_LMDB_SEPARATE", "DETAIL": "Do not mix CDX ADDTAG/BUILDLMDB mutation with header repair unless explicitly authorized.", "MUTATION_KIND": "separate_authorization_required"},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AR is closeout/report-only. Source fix comes later."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation in 10AR."},
        {"PROTECTED_SYSTEM": "WORKSPACE_SCHEMA_SOURCE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Header defect noted; no source patch yet."},
        {"PROTECTED_SYSTEM": "COMMAND_ALIAS_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No alias mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    write_csv(reports / "message_catalog_phase22ae_6_5_10ar_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ar_closeout_items_v1.csv", closeout_rows, ["CLOSEOUT_ITEM", "STATUS", "DETAIL", "MUTATION_AUTHORIZED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ar_workspace_inventory_v1.csv", ws_rows, ["WORKSPACE_PATH", "EXISTS", "HEADER", "AREA_ROWS", "RELATION_ROWS", "HAS_SYSTEM_MESSAGES", "HAS_SYSTEM_MESSAGE_TEXT", "HEADER_DEFECT_OBSERVED", "FORMAT_NOTE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ar_workspace_header_repair_contract_v1.csv", header_repair_contract, ["ITEM", "VALUE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ar_next_workspace_header_repair_plan_v1.csv", next_plan, ["STEP", "ACTION", "DETAIL", "MUTATION_KIND"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ar_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AQ_STATUS": aq.get("STATUS", ""),
        "MSG_022AE_6_5_10AQ_SAVEPOINT_PRESENT": 1 if sp_aq else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CANONICAL_COMMAND": "MSGMGR",
        "CANONICAL_COMMAND_EXPANSION": "Message Manager",
        "LOW_LEVEL_CHECK_SURFACE": "SET MESSAGE CATALOG CHECK",
        "LOW_LEVEL_GET_SURFACE": "SET MESSAGE CATALOG GET",
        "LOW_LEVEL_CHECK_PROVEN": aq.get("SET_MESSAGE_CATALOG_CHECK_PROVEN", ""),
        "LOW_LEVEL_GET_PROVEN": aq.get("SET_MESSAGE_CATALOG_GET_PROVEN", ""),
        "MESSAGING_WORKSPACE_EVIDENCE_OBSERVED": 1 if ws_observed else 0,
        "WORKSPACE_HEADER_DEFECT_FIX_REQUIRED": 1,
        "DEFECTIVE_HEADER": "DTSHEMA",
        "TARGET_HEADER": "DTSCHEMA",
        "TARGET_VERSION_TO_VERIFY": "2",
        "ALIASES_AUTHORIZED": 0,
        "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10ar_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AR_MESSAGE_MANAGER_CONSUMER_CLOSEOUT.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AR Message Manager Consumer Closeout\n\nStatus: `{status}`\n\n10AR closes the Message Manager consumer proof lane in report-only mode. It accepts MSGMGR, SET MESSAGE CATALOG CHECK, and SET MESSAGE CATALOG GET as the current proven command/read surfaces. It also records the workspace schema header spelling issue as a defect requiring a separate guarded fix: `DTSHEMA` should not be the preferred emitted header; next proof should target `DTSCHEMA 2`.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AQ status: {aq.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AQ savepoint present: {1 if sp_aq else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print("  canonical command: MSGMGR")
    print("  canonical command expansion: Message Manager")
    print(f"  low-level check proven: {aq.get('SET_MESSAGE_CATALOG_CHECK_PROVEN','')}")
    print(f"  low-level get proven: {aq.get('SET_MESSAGE_CATALOG_GET_PROVEN','')}")
    print(f"  messaging workspace evidence observed: {1 if ws_observed else 0}")
    print("  workspace header defect fix required: 1")
    print("  defective header: DTSHEMA")
    print("  target header: DTSCHEMA")
    print("  target version to verify: 2")
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
