#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AP_EXISTING_CONSUMER_SURFACE_CONTRACT_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AP_EXISTING_CONSUMER_SURFACE_CONTRACT_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AQ_SET_MESSAGE_CATALOG_READONLY_CONTRACT_PROOF_PACKAGE"
REPORT_DIR = Path("docs/messaging/reports")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path):
    r = read_csv(path)
    return r[0] if r else {}

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ao = first_row(reports / "message_catalog_phase22ae_6_5_10ao_validate_status_summary_v1.csv")
    sp_ao, latest_ao = savepoint_present(repo, "MSG-022AE.6.5.10AO")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    gates, failures = [], 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AO_EXISTING_SURFACE_OBSERVED",
         ao.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AO_RUNTIME_MESSAGE_CONSUMER_READONLY_PROBE_GREEN_EXISTING_SURFACE_OBSERVED",
         ao.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AO_SAVEPOINT_PRESENT", sp_ao, latest_ao)
    gate("10AO_MESSAGE_CONSUMER_SURFACE_OBSERVED", ao.get("MESSAGE_CONSUMER_SURFACE_OBSERVED") == "1", ao.get("MESSAGE_CONSUMER_SURFACE_OBSERVED", "missing"))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AO_NO_SOURCE_MUTATION", ao.get("SOURCE_FILES_MUTATED") == "0", ao.get("SOURCE_FILES_MUTATED", "missing"))
    gate("10AO_NO_ACTIVE_CATALOG_MUTATION", ao.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0", ao.get("ACTIVE_CATALOG_MUTATION_OBSERVED", "missing"))
    gate("10AO_NO_HELP_DATA_MUTATION", ao.get("HELP_DATA_MUTATION_OBSERVED") == "0", ao.get("HELP_DATA_MUTATION_OBSERVED", "missing"))
    gate("10AO_NO_CMDHELPCHK_MUTATION", ao.get("CMDHELPCHK_MUTATION_OBSERVED") == "0", ao.get("CMDHELPCHK_MUTATION_OBSERVED", "missing"))

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    issues = "0" if status == STATUS_GREEN else str(failures)

    command_contract = [
        {"CONTRACT_ITEM":"CANONICAL_COMMAND","VALUE":"MSGMGR","DETAIL":"MSGMGR is the canonical runtime command-house name for Message Manager.","STATUS":"ACCEPTED" if status == STATUS_GREEN else "REVIEW"},
        {"CONTRACT_ITEM":"DISPLAY_NAME","VALUE":"Message Manager","DETAIL":"User-facing long name expands MSGMGR as Message Manager.","STATUS":"ACCEPTED" if status == STATUS_GREEN else "REVIEW"},
        {"CONTRACT_ITEM":"READ_MODE","VALUE":"read-only","DETAIL":"MSGMGR exposes read-only usage/status/check and must not write DBF/CDX/LMDB/runtime state.","STATUS":"ACCEPTED" if status == STATUS_GREEN else "REVIEW"},
        {"CONTRACT_ITEM":"PROVIDER_MODE","VALUE":"active_dbf","DETAIL":"MSGMGR status identifies active DBF provider roots for message catalog readback.","STATUS":"ACCEPTED" if status == STATUS_GREEN else "REVIEW"},
        {"CONTRACT_ITEM":"LOW_LEVEL_CHECK_SURFACE","VALUE":"SET MESSAGE CATALOG CHECK","DETAIL":"Advertised low-level runtime message catalog proof/check surface.","STATUS":"ACCEPTED" if status == STATUS_GREEN else "REVIEW"},
        {"CONTRACT_ITEM":"LOW_LEVEL_GET_SURFACE","VALUE":"SET MESSAGE CATALOG GET","DETAIL":"Advertised low-level get/read surface; next gate should prove exact behavior read-only.","STATUS":"REVIEW_NEXT_GATE"},
    ]
    alias_policy = [
        {"ALIAS":"MSGMGR","TYPE":"canonical","STATUS":"ACCEPTED","REASON":"Short xBase-style command name for Message Manager; runtime-proven registered.","MUTATION_AUTHORIZED":0},
        {"ALIAS":"MESSAGE_MANAGER","TYPE":"possible_future_alias","STATUS":"DEFERRED","REASON":"Readable expansion, not runtime-proven and not alias-policy authorized.","MUTATION_AUTHORIZED":0},
        {"ALIAS":"MESSAGE MANAGER","TYPE":"possible_future_alias","STATUS":"DEFERRED","REASON":"Phrase-style alias deferred until HELP/alias policy is explicit.","MUTATION_AUTHORIZED":0},
        {"ALIAS":"MESSAGE","TYPE":"reserved_or_possible_future_surface","STATUS":"DEFERRED","REASON":"Currently not canonical; may conflict with SET MESSAGE grammar.","MUTATION_AUTHORIZED":0},
        {"ALIAS":"MSG","TYPE":"reserved_or_possible_future_surface","STATUS":"DEFERRED","REASON":"Keep distinct from MSGMGR until alias policy is explicit.","MUTATION_AUTHORIZED":0},
    ]
    surfaces = [
        {"SURFACE":"MSGMGR","OBSERVED_IN_10AO":1,"ROLE":"Canonical command-house usage surface.","NEXT_PROOF":"Accepted as command-house facade."},
        {"SURFACE":"MSGMGR STATUS","OBSERVED_IN_10AO":1,"ROLE":"Reports provider mode, roots, schemas, and boundary.","NEXT_PROOF":"Contract accepted."},
        {"SURFACE":"MSGMGR CHECK","OBSERVED_IN_10AO":1,"ROLE":"Read-only command-house check.","NEXT_PROOF":"Contract accepted."},
        {"SURFACE":"SET MESSAGE CATALOG CHECK","OBSERVED_IN_10AO":1,"ROLE":"Advertised low-level proof surface.","NEXT_PROOF":"10AQ direct read-only proof."},
        {"SURFACE":"SET MESSAGE CATALOG GET","OBSERVED_IN_10AO":1,"ROLE":"Advertised low-level get/read surface.","NEXT_PROOF":"10AQ exact get probes."},
    ]
    next_probe = [
        {"STEP":1,"ACTION":"RUN_SET_MESSAGE_CATALOG_CHECK","DETAIL":"Fresh session; run SET MESSAGE CATALOG CHECK and capture provider/count/boundary evidence.","MUTATES_ACTIVE":0},
        {"STEP":2,"ACTION":"RUN_SET_MESSAGE_CATALOG_GET_FOR_PROOF_SYMBOLS","DETAIL":"Probe proof symbols/locales if GET syntax is available.","MUTATES_ACTIVE":0},
        {"STEP":3,"ACTION":"CLASSIFY_GET_SYNTAX","DETAIL":"Classify exact accepted GET grammar/output or report gap without treating it as catalog failure.","MUTATES_ACTIVE":0},
        {"STEP":4,"ACTION":"DECIDE_SOURCE_INTEGRATION_OR_HELP_HANDOFF","DETAIL":"Only after CHECK/GET proof decide whether source integration or HELP/CMDHELPCHK alias work comes next.","MUTATES_ACTIVE":0},
    ]
    boundary = [
        {"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"10AP is contract-review/report-only."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No DBF mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_SYSTEM_MESSAGE_TEXT","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No DBF mutation."},
        {"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM":"COMMAND_ALIAS_REGISTRY","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No alias mutation; alias policy deferred."},
        {"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},
        {"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},
    ]

    write_csv(reports/"message_catalog_phase22ae_6_5_10ap_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports/"message_catalog_phase22ae_6_5_10ap_command_contract_v1.csv", command_contract, ["CONTRACT_ITEM","VALUE","DETAIL","STATUS"])
    write_csv(reports/"message_catalog_phase22ae_6_5_10ap_alias_policy_v1.csv", alias_policy, ["ALIAS","TYPE","STATUS","REASON","MUTATION_AUTHORIZED"])
    write_csv(reports/"message_catalog_phase22ae_6_5_10ap_low_level_surfaces_v1.csv", surfaces, ["SURFACE","OBSERVED_IN_10AO","ROLE","NEXT_PROOF"])
    write_csv(reports/"message_catalog_phase22ae_6_5_10ap_next_probe_plan_v1.csv", next_probe, ["STEP","ACTION","DETAIL","MUTATES_ACTIVE"])
    write_csv(reports/"message_catalog_phase22ae_6_5_10ap_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])

    summary = {
        "STATUS": status, "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10AO_STATUS": ao.get("STATUS",""),
        "MSG_022AE_6_5_10AO_SAVEPOINT_PRESENT": 1 if sp_ao else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count, "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "CANONICAL_COMMAND": "MSGMGR", "CANONICAL_COMMAND_EXPANSION": "Message Manager",
        "MESSAGE_CONSUMER_SURFACE_OBSERVED": ao.get("MESSAGE_CONSUMER_SURFACE_OBSERVED",""),
        "LOW_LEVEL_CHECK_SURFACE": "SET MESSAGE CATALOG CHECK",
        "LOW_LEVEL_GET_SURFACE": "SET MESSAGE CATALOG GET",
        "ALIASES_AUTHORIZED": 0, "RUNTIME_CONSUMER_SOURCE_INTEGRATION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0, "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0, "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
    }
    write_csv(reports/"message_catalog_phase22ae_6_5_10ap_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo/"docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AP_EXISTING_CONSUMER_SURFACE_CONTRACT_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AP Existing Consumer Surface Contract Review\n\nStatus: `{status}`\n\n10AP is report-only. It accepts `MSGMGR` as the canonical Message Manager command-house surface and defers aliases/source integration until later explicit gates.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10AO status: {ao.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AO savepoint present: {1 if sp_ao else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print("  canonical command: MSGMGR")
    print("  canonical command expansion: Message Manager")
    print(f"  message consumer surface observed: {ao.get('MESSAGE_CONSUMER_SURFACE_OBSERVED','')}")
    print("  low-level check surface: SET MESSAGE CATALOG CHECK")
    print("  low-level get surface: SET MESSAGE CATALOG GET")
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
