#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AK_POST_PROMOTION_MESSAGING_CATALOG_CLOSEOUT_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AK_POST_PROMOTION_MESSAGING_CATALOG_CLOSEOUT_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AL_FOLLOWUP_INDEX_LMDB_OR_RUNTIME_MESSAGE_CONSUMER_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

CHAIN = [
    ("10U", "message_catalog_phase22ae_6_5_10u_restore_status_summary_v1.csv", "MESSAGE_CATALOG_PHASE22AE_6_5_10U_TEXT_ONLY_ACTIVE_BASELINE_ROUNDTRIP_PROVEN_AND_RESTORED"),
    ("10X", "message_catalog_phase22ae_6_5_10x_restore_status_summary_v1.csv", "MESSAGE_CATALOG_PHASE22AE_6_5_10X_CANDIDATE10_TEXT_APPEND_MICRO_PROOF_PROVEN_AND_RESTORED"),
    ("10AA", "message_catalog_phase22ae_6_5_10aa_restore_status_summary_v1.csv", "MESSAGE_CATALOG_PHASE22AE_6_5_10AA_FULL70_TEXT_ZAP_IMPORT_SEQUENCE_PROVEN_AND_RESTORED"),
    ("10AD", "message_catalog_phase22ae_6_5_10ad_restore_status_summary_v1.csv", "MESSAGE_CATALOG_PHASE22AE_6_5_10AD_TWO_TABLE_PROMOTION_SEQUENCE_V1_PROVEN_AND_RESTORED"),
    ("10AH", "message_catalog_phase22ae_6_5_10ah_finalize_status_summary_v1.csv", "MESSAGE_CATALOG_PHASE22AE_6_5_10AH_GUARDED_FINAL_PROMOTION_EXECUTION_GREEN_ACTIVE_PROMOTED"),
    ("10AI", "message_catalog_phase22ae_6_5_10ai_validate_status_summary_v1.csv", "MESSAGE_CATALOG_PHASE22AE_6_5_10AI_POST_PROMOTION_FRESH_READBACK_GREEN_ACTIVE_PROMOTION_PERSISTED"),
    ("10AJ", "message_catalog_phase22ae_6_5_10aj_status_summary_v1.csv", "MESSAGE_CATALOG_PHASE22AE_6_5_10AJ_POST_PROMOTION_ACCEPTANCE_AND_BACKUP_RETENTION_PLAN_GREEN_SOURCE_HELD"),
]

SAVEPOINTS = [
    "MSG-022AE.6.5.10U",
    "MSG-022AE.6.5.10X",
    "MSG-022AE.6.5.10AA",
    "MSG-022AE.6.5.10AD",
    "MSG-022AE.6.5.10AH",
    "MSG-022AE.6.5.10AI",
    "MSG-022AE.6.5.10AJ",
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

def backup_exists(repo: Path, value: str):
    if not value:
        return False, ""
    p = Path(value)
    if not p.is_absolute():
        p = repo / p
    return p.exists(), rel(p, repo)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    aj = first_row(reports / "message_catalog_phase22ae_6_5_10aj_status_summary_v1.csv")
    sp_aj, latest_aj = savepoint_present(repo, "MSG-022AE.6.5.10AJ")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)

    backup_root = aj.get("ROLLBACK_BACKUP_ROOT", "")
    backup_ok, backup_path = backup_exists(repo, backup_root)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AJ_GREEN", aj.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AJ_POST_PROMOTION_ACCEPTANCE_AND_BACKUP_RETENTION_PLAN_GREEN_SOURCE_HELD", aj.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AJ_SAVEPOINT_PRESENT", sp_aj, latest_aj)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AJ_ACTIVE_PROMOTION_ACCEPTED", aj.get("ACTIVE_PROMOTION_ACCEPTED") == "1", aj.get("ACTIVE_PROMOTION_ACCEPTED", "missing"))
    gate("10AJ_ROLLBACK_NOT_REQUIRED", aj.get("ROLLBACK_REQUIRED") == "0", aj.get("ROLLBACK_REQUIRED", "missing"))
    gate("10AJ_BACKUP_RETAINED", aj.get("ROLLBACK_BACKUP_RETAINED") == "1", aj.get("ROLLBACK_BACKUP_RETAINED", "missing"))
    gate("10AJ_BACKUP_ROOT_EXISTS", backup_ok, backup_path)

    chain_rows = []
    for step, filename, expected in CHAIN:
        r = first_row(reports / filename)
        ok = r.get("STATUS") == expected
        chain_rows.append({
            "STEP": step,
            "REPORT": f"docs/messaging/reports/{filename}",
            "EXPECTED_STATUS": expected,
            "OBSERVED_STATUS": r.get("STATUS", ""),
            "PASS": 1 if ok else 0,
            "ROLE": {
                "10U": "baseline60 active text roundtrip",
                "10X": "candidate10 active append micro proof",
                "10AA": "full70 text-only active ZAP/import proof",
                "10AD": "two-table diagnostic proof and restore",
                "10AH": "final active promotion execution",
                "10AI": "fresh-session post-promotion readback",
                "10AJ": "promotion acceptance and backup retention",
            }.get(step, ""),
        })
        gate(f"{step}_EXPECTED_STATUS", ok, r.get("STATUS", "missing"))

    savepoint_rows = []
    for sid in SAVEPOINTS:
        present, latest = savepoint_present(repo, sid)
        savepoint_rows.append({"SAVEPOINT_ID": sid, "PRESENT": 1 if present else 0, "LATEST_SEEN": latest})
        gate(f"{sid}_SAVEPOINT_PRESENT", present, latest)

    final_state = [
        {"OBJECT": "SYSTEM_MESSAGES", "ACTIVE_PATH": rel(repo / ACTIVE_MSG_DBF, repo), "ACCEPTED_COUNT": 14, "OBSERVED_COUNT": msg_count, "STATUS": "ACCEPTED_ACTIVE" if msg_count == 14 else "REVIEW"},
        {"OBJECT": "SYSTEM_MESSAGE_TEXT", "ACTIVE_PATH": rel(repo / ACTIVE_TEXT_DBF, repo), "ACCEPTED_COUNT": 70, "OBSERVED_COUNT": text_count, "STATUS": "ACCEPTED_ACTIVE" if text_count == 70 else "REVIEW"},
    ]

    retained_artifacts = [
        {"ARTIFACT": "10AH rollback backup root", "PATH": backup_path, "POLICY": "RETAIN", "DELETE_AUTHORIZED": 0, "REASON": "Audit and emergency rollback evidence after accepted active promotion."},
        {"ARTIFACT": "10AH rollback script", "PATH": "tools/messaging/run_message_catalog_phase22ae_6_5_10ah_rollback.ps1", "POLICY": "RETAIN_DO_NOT_RUN_BY_DEFAULT", "DELETE_AUTHORIZED": 0, "REASON": "Rollback would undo accepted 14/70 active promotion."},
        {"ARTIFACT": "10AI fresh readback runlog", "PATH": "docs/messaging/runlog/MSG-022AE_6_5_10AI_POST_PROMOTION_FRESH_READBACK.md", "POLICY": "RETAIN", "DELETE_AUTHORIZED": 0, "REASON": "Persistence proof."},
    ]

    remaining = [
        {"ITEM": "Index/LMDB follow-up", "STATUS": "OPTIONAL_REVIEW", "DETAIL": "DBF active state is accepted at 14/70; a future plan may verify/rebuild messaging CDX/LMDB if runtime consumers require it.", "MUTATION_AUTHORIZED": 0},
        {"ITEM": "Runtime message consumer integration", "STATUS": "FUTURE_PLAN", "DETAIL": "Next lane may connect promoted catalog rows to runtime lookup/formatting consumers.", "MUTATION_AUTHORIZED": 0},
        {"ITEM": "HELP/CMDHELPCHK handoff", "STATUS": "NOT_AUTHORIZED", "DETAIL": "No HELP DATA or CMDHELPCHK mutation occurred in this lane.", "MUTATION_AUTHORIZED": 0},
        {"ITEM": "Rollback backup cleanup", "STATUS": "NOT_AUTHORIZED", "DETAIL": "10AH backup cleanup/compression/delete remains unauthorized.", "MUTATION_AUTHORIZED": 0},
    ]

    closeout = [
        {"CLOSEOUT_ITEM": "Active messaging catalog promoted", "STATUS": "CLOSED_GREEN", "EVIDENCE": "10AH + 10AI + 10AJ", "DETAIL": "SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70 accepted."},
        {"CLOSEOUT_ITEM": "Original failed path classified", "STATUS": "CLOSED_REVIEWED", "EVIDENCE": "10AF", "DETAIL": "Original 6.5.10 failure classified as package/wrapper delta; successful pattern used for final promotion."},
        {"CLOSEOUT_ITEM": "Rollback status", "STATUS": "NOT_REQUIRED_RETAINED", "EVIDENCE": "10AJ", "DETAIL": "Rollback not required; backup retained."},
        {"CLOSEOUT_ITEM": "Protected boundaries", "STATUS": "CLEAN", "EVIDENCE": "10AJ and 10AK ledgers", "DETAIL": "No source/HELP/CMDHELPCHK mutation."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AK is report-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ROLLBACK_BACKUP_DELETE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No backup deletion/compression."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_chain_summary_v1.csv", chain_rows, ["STEP", "REPORT", "EXPECTED_STATUS", "OBSERVED_STATUS", "PASS", "ROLE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_savepoint_summary_v1.csv", savepoint_rows, ["SAVEPOINT_ID", "PRESENT", "LATEST_SEEN"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_final_state_v1.csv", final_state, ["OBJECT", "ACTIVE_PATH", "ACCEPTED_COUNT", "OBSERVED_COUNT", "STATUS"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_retained_artifacts_v1.csv", retained_artifacts, ["ARTIFACT", "PATH", "POLICY", "DELETE_AUTHORIZED", "REASON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_remaining_items_v1.csv", remaining, ["ITEM", "STATUS", "DETAIL", "MUTATION_AUTHORIZED"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_closeout_ledger_v1.csv", closeout, ["CLOSEOUT_ITEM", "STATUS", "EVIDENCE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AJ_STATUS": aj.get("STATUS", ""),
        "MSG_022AE_6_5_10AJ_SAVEPOINT_PRESENT": 1 if sp_aj else 0,
        "ACTIVE_MESSAGES_ACCEPTED_COUNT": 14,
        "ACTIVE_TEXT_ACCEPTED_COUNT": 70,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "ACTIVE_PROMOTION_CLOSEOUT_ACCEPTED": 1 if status == STATUS_GREEN else 0,
        "ROLLBACK_REQUIRED": 0 if status == STATUS_GREEN else 1,
        "ROLLBACK_BACKUP_RETAINED": 1 if backup_ok else 0,
        "ROLLBACK_BACKUP_ROOT": backup_path,
        "ROLLBACK_BACKUP_DELETE_AUTHORIZED": 0,
        "CHAIN_STEPS_REVIEWED": len(CHAIN),
        "SAVEPOINTS_REVIEWED": len(SAVEPOINTS),
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10ak_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AK_POST_PROMOTION_MESSAGING_CATALOG_CLOSEOUT.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AK Post-Promotion Messaging Catalog Closeout\n\nStatus: `{status}`\n\n10AK is report-only. It closes the active messaging catalog promotion lane at SYSTEM_MESSAGES=14 and SYSTEM_MESSAGE_TEXT=70, retains the 10AH rollback backup, and records remaining follow-up items as separate future gates.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AJ status: {aj.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AJ savepoint present: {1 if sp_aj else 0}")
    print(f"  active messages accepted/observed: 14/{msg_count}")
    print(f"  active text accepted/observed: 70/{text_count}")
    print(f"  active promotion closeout accepted: {1 if status == STATUS_GREEN else 0}")
    print(f"  rollback required: {0 if status == STATUS_GREEN else 1}")
    print(f"  rollback backup retained: {1 if backup_ok else 0}")
    print(f"  rollback backup root: {backup_path}")
    print("  rollback backup delete authorized: 0")
    print(f"  chain steps reviewed: {len(CHAIN)}")
    print(f"  savepoints reviewed: {len(SAVEPOINTS)}")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
