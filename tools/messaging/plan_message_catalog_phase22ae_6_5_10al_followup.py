#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10AL_FOLLOWUP_INDEX_LMDB_OR_RUNTIME_MESSAGE_CONSUMER_PLAN_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10AL_FOLLOWUP_INDEX_LMDB_OR_RUNTIME_MESSAGE_CONSUMER_PLAN_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_PLAN"

REPORT_DIR = Path("docs/messaging/reports")

ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

ARTIFACTS = [
    ("SYSTEM_MESSAGES_DBF", ACTIVE_MSG_DBF),
    ("SYSTEM_MESSAGE_TEXT_DBF", ACTIVE_TEXT_DBF),
    ("SYSTEM_MESSAGES_MESSAGING_CDX", Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGES.cdx")),
    ("SYSTEM_MESSAGE_TEXT_MESSAGING_CDX", Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx")),
    ("SYSTEM_MESSAGES_MESSAGING_CDX_META", Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGES.cdx.meta")),
    ("SYSTEM_MESSAGE_TEXT_MESSAGING_CDX_META", Path("dottalkpp/data/indexes/messaging/SYSTEM_MESSAGE_TEXT.cdx.meta")),
    ("SYSTEM_MESSAGES_MESSAGING_LMDB", Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGES.cdx.d")),
    ("SYSTEM_MESSAGE_TEXT_MESSAGING_LMDB", Path("dottalkpp/data/lmdb/messaging/SYSTEM_MESSAGE_TEXT.cdx.d")),
    ("SYSTEM_MESSAGES_DEFAULT_CDX", Path("dottalkpp/data/indexes/SYSTEM_MESSAGES.cdx")),
    ("SYSTEM_MESSAGE_TEXT_DEFAULT_CDX", Path("dottalkpp/data/indexes/SYSTEM_MESSAGE_TEXT.cdx")),
    ("SYSTEM_MESSAGES_DEFAULT_LMDB", Path("dottalkpp/data/lmdb/SYSTEM_MESSAGES.cdx.d")),
    ("SYSTEM_MESSAGE_TEXT_DEFAULT_LMDB", Path("dottalkpp/data/lmdb/SYSTEM_MESSAGE_TEXT.cdx.d")),
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

def sha256_file(path: Path):
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def hash_dir(path: Path):
    if not path.exists() or not path.is_dir():
        return "", 0, 0
    files = sorted(p for p in path.rglob("*") if p.is_file())
    h = hashlib.sha256()
    total = 0
    for f in files:
        h.update(str(f.relative_to(path)).replace("\\", "/").encode("utf-8"))
        h.update(sha256_file(f).encode("ascii"))
        total += f.stat().st_size
    return h.hexdigest(), len(files), total

def inventory(repo: Path):
    rows = []
    for role, path in ARTIFACTS:
        p = repo / path
        if p.is_dir():
            h, count, size = hash_dir(p)
            rows.append({"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "dir", "BYTES": size, "FILES": count, "SHA256": h})
        elif p.is_file():
            rows.append({"ROLE": role, "PATH": rel(p, repo), "EXISTS": 1, "KIND": "file", "BYTES": p.stat().st_size, "FILES": 1, "SHA256": sha256_file(p)})
        else:
            rows.append({"ROLE": role, "PATH": rel(p, repo), "EXISTS": 0, "KIND": "missing", "BYTES": 0, "FILES": 0, "SHA256": ""})
    return rows

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

    ak = first_row(reports / "message_catalog_phase22ae_6_5_10ak_status_summary_v1.csv")
    sp_ak, latest_ak = savepoint_present(repo, "MSG-022AE.6.5.10AK")
    msg_count = dbf_header_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_header_count(repo / ACTIVE_TEXT_DBF)
    inv_rows = inventory(repo)

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10AK_GREEN",
         ak.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10AK_POST_PROMOTION_MESSAGING_CATALOG_CLOSEOUT_GREEN_SOURCE_HELD",
         ak.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10AK_SAVEPOINT_PRESENT", sp_ak, latest_ak)
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("10AK_CLOSEOUT_ACCEPTED", ak.get("ACTIVE_PROMOTION_CLOSEOUT_ACCEPTED") == "1", ak.get("ACTIVE_PROMOTION_CLOSEOUT_ACCEPTED", "missing"))
    gate("10AK_ROLLBACK_NOT_REQUIRED", ak.get("ROLLBACK_REQUIRED") == "0", ak.get("ROLLBACK_REQUIRED", "missing"))

    dbf_exists = {r["ROLE"]: r for r in inv_rows}
    gate("SYSTEM_MESSAGES_DBF_PRESENT", dbf_exists.get("SYSTEM_MESSAGES_DBF", {}).get("EXISTS") == 1, dbf_exists.get("SYSTEM_MESSAGES_DBF", {}).get("PATH", "missing"))
    gate("SYSTEM_MESSAGE_TEXT_DBF_PRESENT", dbf_exists.get("SYSTEM_MESSAGE_TEXT_DBF", {}).get("EXISTS") == 1, dbf_exists.get("SYSTEM_MESSAGE_TEXT_DBF", {}).get("PATH", "missing"))

    # Presence of CDX/LMDB is inventoried but not a blocker for 10AL, because this phase is deciding the follow-up lane.
    messaging_cdx_present = sum(1 for r in inv_rows if "MESSAGING_CDX" in r["ROLE"] and r["EXISTS"] == 1)
    messaging_lmdb_present = sum(1 for r in inv_rows if "MESSAGING_LMDB" in r["ROLE"] and r["EXISTS"] == 1)

    lane_rows = [
        {
            "LANE_ID": "10AM",
            "LANE": "READONLY_INDEX_LMDB_VERIFICATION",
            "RECOMMENDATION": "NEXT_PRIMARY",
            "REASON": "DBF promotion is accepted at 14/70; before runtime consumers depend on indexed lookup, verify CDX/LMDB state read-only.",
            "MUTATION_AUTHORIZED": 0,
            "NEXT_GATE": "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AM_READONLY_INDEX_LMDB_VERIFICATION_PLAN",
        },
        {
            "LANE_ID": "10AN",
            "LANE": "RUNTIME_MESSAGE_CONSUMER_INTEGRATION_PLAN",
            "RECOMMENDATION": "SECONDARY_AFTER_10AM_OR_PARALLEL_PLAN_ONLY",
            "REASON": "Runtime message lookup/formatting should consume the promoted catalog, but should not hide index/LMDB uncertainty.",
            "MUTATION_AUTHORIZED": 0,
            "NEXT_GATE": "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10AN_RUNTIME_MESSAGE_CONSUMER_INTEGRATION_PLAN",
        },
        {
            "LANE_ID": "10AO",
            "LANE": "HELP_CMDHELPCHK_HANDOFF_PLAN",
            "RECOMMENDATION": "DEFER",
            "REASON": "Messaging catalog promotion did not authorize HELP DATA or CMDHELPCHK mutation.",
            "MUTATION_AUTHORIZED": 0,
            "NEXT_GATE": "SEPARATE_EXPLICIT_AUTHORIZATION_REQUIRED",
        },
        {
            "LANE_ID": "10AP",
            "LANE": "ROLLBACK_BACKUP_CLEANUP_OR_ARCHIVE_COMPRESSION",
            "RECOMMENDATION": "DEFER",
            "REASON": "10AJ retained the rollback backup and did not authorize deletion/compression.",
            "MUTATION_AUTHORIZED": 0,
            "NEXT_GATE": "SEPARATE_EXPLICIT_AUTHORIZATION_REQUIRED",
        },
    ]

    index_plan = [
        {
            "STEP": 1,
            "ACTION": "INVENTORY_ACTIVE_MESSAGING_ARTIFACTS",
            "DETAIL": "Read-only inventory of SYSTEM_MESSAGES/SYSTEM_MESSAGE_TEXT DBF, CDX, CDX metadata, and LMDB dirs.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "FRESH_RUNTIME_INDEX_READBACK",
            "DETAIL": "Open active tables in DotTalk++; confirm valid indices and COUNT 14/70 without ZAP/IMPORT/BUILDLMDB.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "OPTIONAL_TAG_PROBE",
            "DETAIL": "If runtime commands support it, inspect TAGS/ORDER/SEEK behavior read-only for promoted proof symbols.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "CLASSIFY_REBUILD_NEED",
            "DETAIL": "If CDX/LMDB is missing/stale, create a separate guarded rebuild plan; do not rebuild in 10AM unless explicitly authorized.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    consumer_plan = [
        {
            "STEP": 1,
            "ACTION": "DEFINE_RUNTIME_MESSAGE_LOOKUP_CONTRACT",
            "DETAIL": "Map SYMBOL/MSGID + locale to SYSTEM_MESSAGE_TEXT row and fallback behavior.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "DEFINE_PLACEHOLDER_ARGUMENT_CONTRACT",
            "DETAIL": "Document argument interpolation and typed message severity/category fields before runtime mutation.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "ADD_CONSUMER_READBACK_TEST_PLAN",
            "DETAIL": "Plan commands/tests that prove catalog-backed messages are returned without changing HELP/CMDHELPCHK.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "DEFER_SOURCE_MUTATION",
            "DETAIL": "No runtime consumer source changes until the contract and index/LMDB status are accepted.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    decision = [
        {
            "QUESTION": "Do we verify index/LMDB before consumer integration?",
            "RECOMMENDED_ANSWER": "YES",
            "REASON": "The DBF promotion is proven, but runtime consumer performance/lookup may depend on index/LMDB health.",
        },
        {
            "QUESTION": "Should 10AM rebuild CDX/LMDB?",
            "RECOMMENDED_ANSWER": "NO, READONLY FIRST",
            "REASON": "10AL authorizes planning only. Rebuild should be a later explicit guarded mutation if read-only verification finds a need.",
        },
        {
            "QUESTION": "Should runtime message consumers be modified now?",
            "RECOMMENDED_ANSWER": "NO",
            "REASON": "Consumer integration is a separate source/runtime behavior change and should follow a stable contract.",
        },
        {
            "QUESTION": "Should rollback backup be deleted now?",
            "RECOMMENDED_ANSWER": "NO",
            "REASON": "10AJ retained the 10AH rollback backup as archive evidence.",
        },
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10AL is plan-only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB build or repair."},
        {"PROTECTED_SYSTEM": "ROLLBACK_BACKUP_DELETE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No backup deletion/compression."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = "0" if status == STATUS_GREEN else str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_5_10al_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10al_artifact_inventory_v1.csv", inv_rows, ["ROLE", "PATH", "EXISTS", "KIND", "BYTES", "FILES", "SHA256"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10al_lane_decision_v1.csv", lane_rows, ["LANE_ID", "LANE", "RECOMMENDATION", "REASON", "MUTATION_AUTHORIZED", "NEXT_GATE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10al_index_lmdb_verification_plan_v1.csv", index_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10al_runtime_consumer_plan_v1.csv", consumer_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10al_decision_questions_v1.csv", decision, ["QUESTION", "RECOMMENDED_ANSWER", "REASON"])
    write_csv(reports / "message_catalog_phase22ae_6_5_10al_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_5_10AK_STATUS": ak.get("STATUS", ""),
        "MSG_022AE_6_5_10AK_SAVEPOINT_PRESENT": 1 if sp_ak else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "ACTIVE_PROMOTION_CLOSEOUT_ACCEPTED": ak.get("ACTIVE_PROMOTION_CLOSEOUT_ACCEPTED", ""),
        "MESSAGING_CDX_PRESENT_COUNT": messaging_cdx_present,
        "MESSAGING_LMDB_PRESENT_COUNT": messaging_lmdb_present,
        "RECOMMENDED_NEXT_LANE": "10AM_READONLY_INDEX_LMDB_VERIFICATION_PLAN",
        "RUNTIME_CONSUMER_INTEGRATION_AUTHORIZED": 0,
        "INDEX_LMDB_REBUILD_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    write_csv(reports / "message_catalog_phase22ae_6_5_10al_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10AL_FOLLOWUP_INDEX_LMDB_OR_RUNTIME_MESSAGE_CONSUMER_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10AL Follow-up Index/LMDB or Runtime Message Consumer Plan\n\nStatus: `{status}`\n\n10AL is plan-only. It keeps the active catalog accepted at 14/70 and recommends the next primary lane as read-only index/LMDB verification before runtime consumer source integration.\n\nNext gate:\n\n```text\n{NEXT_GATE}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.5.10AK status: {ak.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10AK savepoint present: {1 if sp_ak else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  messaging CDX present count: {messaging_cdx_present}")
    print(f"  messaging LMDB present count: {messaging_lmdb_present}")
    print("  recommended next lane: 10AM_READONLY_INDEX_LMDB_VERIFICATION_PLAN")
    print("  runtime consumer integration authorized: 0")
    print("  index/LMDB rebuild authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
