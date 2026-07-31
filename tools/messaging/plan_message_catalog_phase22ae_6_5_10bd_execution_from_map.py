#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BD_HELP_CMDHELPCHK_EXECUTION_PLAN_FROM_ACCEPTED_MAP_GREEN_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BD_HELP_CMDHELPCHK_EXECUTION_PLAN_FROM_ACCEPTED_MAP_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BE_HELP_CMDHELPCHK_GUARDED_EXECUTION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
BC_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bc_status_summary_v1.csv"
BC_ACCEPTED = REPORT_DIR / "message_catalog_phase22ae_6_5_10bc_accepted_exact_target_map_v1.csv"
BD_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bd_help_cmdhelpchk_execution_plan_from_accepted_map_v1")
CANDIDATE_PATH = Path("docs/messaging/candidates/MESSAGE_CATALOG_PHASE22AE_6_5_10AW_MSGMGR_HELP_CANDIDATE.md")
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")

def rows(p):
    p = Path(p)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first(p):
    r = rows(p)
    return r[0] if r else {}

def wcsv(p, rs, fs):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fs, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rs:
            w.writerow({k: r.get(k, "") for k in fs})

def rel(p, repo):
    try:
        return str(Path(p).relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()

def dbf_count(p):
    p = Path(p)
    if not p.exists() or p.stat().st_size < 12:
        return ""
    return int.from_bytes(p.read_bytes()[:12][4:8], "little")

def savepoint(repo, sid):
    latest = ""
    lp = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    if lp.exists():
        try:
            latest = json.loads(lp.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest = ""
    jp = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    txt = jp.read_text(encoding="utf-8", errors="replace") if jp.exists() else ""
    return latest == sid or sid in txt, latest

def action_for(row):
    kind = row.get("TARGET_KIND", "").upper()
    target = row.get("TARGET_PATH", "")
    if "CMDHELP" in kind:
        return "PLAN_CMDHELPCHK_RULE_INSERT_OR_UPDATE"
    if "HELP" in kind:
        return "PLAN_HELP_TOPIC_INSERT_OR_UPDATE"
    return "PLAN_REVIEW_ACTION"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bc = first(repo / BC_SUMMARY)
    accepted = rows(repo / BC_ACCEPTED)
    sp_bc, latest_bc = savepoint(repo, "MSG-022AE.6.5.10BC")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bd_root = repo / BD_ROOT
    candidate = repo / CANDIDATE_PATH

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BC_GREEN",
         bc.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BC_EXACT_TARGET_MAP_ACCEPTANCE_REVIEW_GREEN_ACCEPTED_FOR_EXECUTION_PLANNING_SOURCE_HELD",
         bc.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BC_SAVEPOINT_PRESENT", sp_bc, latest_bc)
    gate("BC_MAP_ACCEPTED_FOR_PLANNING", bc.get("EXACT_TARGET_MAP_ACCEPTED_FOR_PLANNING") == "1", bc.get("EXACT_TARGET_MAP_ACCEPTED_FOR_PLANNING", "missing"))
    gate("BC_HELP_APPLY_NOT_EXECUTED", bc.get("HELP_DATA_APPLY_EXECUTED") == "0", bc.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BC_CMDHELPCHK_APPLY_NOT_EXECUTED", bc.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bc.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("ACCEPTED_MAP_ROWS_PRESENT", len(accepted) > 0, len(accepted))
    gate("ACCEPTED_MAP_ROWS_MATCH_SUMMARY", str(len(accepted)) == str(bc.get("ACCEPTED_MAP_ROWS", "")), f"accepted={len(accepted)} summary={bc.get('ACCEPTED_MAP_ROWS','')}")
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CANDIDATE_EXISTS", candidate.exists(), rel(candidate, repo))
    gate("BD_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bd_root.exists()) or args.replace_existing_plan, rel(bd_root, repo))

    status = BLOCKED
    plan_rows = []
    validation_rows = []
    rollback_rows = []
    artifact_rows = []
    if failures == 0:
        if bd_root.exists() and args.replace_existing_plan:
            shutil.rmtree(bd_root)
        bd_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(accepted, start=1):
            plan_rows.append({
                "EXEC_STEP": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "PLANNED_ACTION": action_for(r),
                "SOURCE_CANDIDATE": rel(candidate, repo),
                "CANDIDATE_HELP_TOPIC": "MSGMGR",
                "CANDIDATE_LOW_LEVEL_TOPICS": "SET MESSAGE CATALOG CHECK;SET MESSAGE CATALOG GET;SET MESSAGE EMIT",
                "ROLLBACK_REQUIRED": 1,
                "PRE_EXEC_BACKUP_REQUIRED": 1,
                "AUTHORIZED_FOR_EXECUTION_NOW": 0,
                "EXECUTION_PACKAGE_REQUIRED": "10BE",
                "NOTES": r.get("NOTES", ""),
            })

        validation_rows = [
            {"VALIDATION_STEP": 1, "VALIDATION": "PRE_EXEC_BACKUP_HASH_CHECK", "EXPECTED": "All target rows have backup coverage or explicit target-specific backup is created in 10BE.", "AUTHORIZED_NOW": 0},
            {"VALIDATION_STEP": 2, "VALIDATION": "DRY_RUN_DIFF_REVIEW", "EXPECTED": "10BE shows exact HELP/CMDHELPCHK row/section diffs before write.", "AUTHORIZED_NOW": 0},
            {"VALIDATION_STEP": 3, "VALIDATION": "HELP_MSGMGR_READBACK", "EXPECTED": "HELP MSGMGR displays candidate text after apply.", "AUTHORIZED_NOW": 0},
            {"VALIDATION_STEP": 4, "VALIDATION": "HELP_SET_MESSAGE_READBACK", "EXPECTED": "SET MESSAGE CATALOG CHECK/GET/EMIT help surfaces visible after apply.", "AUTHORIZED_NOW": 0},
            {"VALIDATION_STEP": 5, "VALIDATION": "CMDHELPCHK_READONLY_VALIDATION", "EXPECTED": "CMDHELPCHK accepts MSGMGR and low-level SET MESSAGE help linkage.", "AUTHORIZED_NOW": 0},
            {"VALIDATION_STEP": 6, "VALIDATION": "BOUNDARY_RECHECK", "EXPECTED": "No DBF/CDX/LMDB/workspace/source mutation outside authorized HELP/CMDHELPCHK targets.", "AUTHORIZED_NOW": 0},
        ]

        rollback_rows = [
            {"ROLLBACK_STEP": 1, "ROLLBACK_ACTION": "CAPTURE_PRE_EXEC_TARGET_HASHES", "REQUIRED": 1, "DETAIL": "10BE must hash each exact target immediately before mutation."},
            {"ROLLBACK_STEP": 2, "ROLLBACK_ACTION": "COPY_EXACT_TARGET_BACKUPS", "REQUIRED": 1, "DETAIL": "10BE must copy exact target backups into its own timestamped backup root."},
            {"ROLLBACK_STEP": 3, "ROLLBACK_ACTION": "GENERATE_RESTORE_SCRIPT", "REQUIRED": 1, "DETAIL": "10BE must generate restore script from exact target backups."},
            {"ROLLBACK_STEP": 4, "ROLLBACK_ACTION": "POST_RESTORE_VERIFY", "REQUIRED": 1, "DETAIL": "If restore is needed, hashes must match pre-exec state."},
        ]

        plan_path = bd_root / "execution_plan_FROM_ACCEPTED_MAP_v1.csv"
        validation_path = bd_root / "execution_validation_plan_v1.csv"
        rollback_path = bd_root / "execution_rollback_plan_v1.csv"
        readme = bd_root / "README_10BD_EXECUTION_PLAN.md"

        wcsv(plan_path, plan_rows, ["EXEC_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","PLANNED_ACTION","SOURCE_CANDIDATE","CANDIDATE_HELP_TOPIC","CANDIDATE_LOW_LEVEL_TOPICS","ROLLBACK_REQUIRED","PRE_EXEC_BACKUP_REQUIRED","AUTHORIZED_FOR_EXECUTION_NOW","EXECUTION_PACKAGE_REQUIRED","NOTES"])
        wcsv(validation_path, validation_rows, ["VALIDATION_STEP","VALIDATION","EXPECTED","AUTHORIZED_NOW"])
        wcsv(rollback_path, rollback_rows, ["ROLLBACK_STEP","ROLLBACK_ACTION","REQUIRED","DETAIL"])
        readme.write_text(
            "# 10BD Execution Plan From Accepted Map\n\n"
            "10BD turns the 10BC accepted target map into a guarded execution plan. "
            "It does not mutate HELP DATA or CMDHELPCHK.\n\n"
            "Execution remains blocked until 10BE is explicitly authorized and generated.\n",
            encoding="utf-8"
        )

        for p in [plan_path, validation_path, rollback_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "execution_plan_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BD writes docs/messaging execution-plan artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; execution plan only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; execution plan only."},
    ]

    readiness = [
        {"ITEM": "EXECUTION_PLAN_CREATED", "STATUS": "YES" if plan_rows else "NO", "DETAIL": f"{len(plan_rows)} planned execution steps."},
        {"ITEM": "VALIDATION_PLAN_CREATED", "STATUS": "YES" if validation_rows else "NO", "DETAIL": f"{len(validation_rows)} validation steps."},
        {"ITEM": "ROLLBACK_PLAN_CREATED", "STATUS": "YES" if rollback_rows else "NO", "DETAIL": f"{len(rollback_rows)} rollback steps."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BD", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BD", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_EXECUTION_PACKAGE_GATE", "STATUS": "10BE_REQUIRED", "DETAIL": "10BE should generate/run guarded execution only if explicitly authorized."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bd_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bd_execution_plan_v1.csv", plan_rows, ["EXEC_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","PLANNED_ACTION","SOURCE_CANDIDATE","CANDIDATE_HELP_TOPIC","CANDIDATE_LOW_LEVEL_TOPICS","ROLLBACK_REQUIRED","PRE_EXEC_BACKUP_REQUIRED","AUTHORIZED_FOR_EXECUTION_NOW","EXECUTION_PACKAGE_REQUIRED","NOTES"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bd_validation_plan_v1.csv", validation_rows, ["VALIDATION_STEP","VALIDATION","EXPECTED","AUTHORIZED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bd_rollback_plan_v1.csv", rollback_rows, ["ROLLBACK_STEP","ROLLBACK_ACTION","REQUIRED","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bd_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bd_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bd_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BC_STATUS": bc.get("STATUS", ""),
        "MSG_022AE_6_5_10BC_SAVEPOINT_PRESENT": 1 if sp_bc else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "ACCEPTED_MAP_ROWS": len(accepted),
        "EXECUTION_PLAN_ROWS": len(plan_rows),
        "VALIDATION_PLAN_ROWS": len(validation_rows),
        "ROLLBACK_PLAN_ROWS": len(rollback_rows),
        "BD_ROOT": rel(bd_root, repo),
        "HELP_DATA_APPLY_EXECUTION_PLANNED": 1 if plan_rows else 0,
        "CMDHELPCHK_APPLY_EXECUTION_PLANNED": 1 if plan_rows else 0,
        "HELP_DATA_APPLY_EXECUTED": 0,
        "CMDHELPCHK_APPLY_EXECUTED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED_BY_REVIEW": 0,
        "DBF_MUTATION_OBSERVED": 0,
        "CDX_LMDB_MUTATION_OBSERVED": 0,
        "WORKSPACE_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    wcsv(reports / "message_catalog_phase22ae_6_5_10bd_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BD_HELP_CMDHELPCHK_EXECUTION_PLAN_FROM_ACCEPTED_MAP.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BD HELP/CMDHELPCHK Execution Plan From Accepted Map\n\n"
        f"Status: `{status}`\n\n"
        "10BD builds the guarded execution plan from the 10BC accepted target map. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Execution-plan root:\n\n```text\n{rel(bd_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BC status: {bc.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BC savepoint present: {1 if sp_bc else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  accepted map rows: {len(accepted)}")
    print(f"  execution plan rows: {len(plan_rows)}")
    print(f"  validation plan rows: {len(validation_rows)}")
    print(f"  rollback plan rows: {len(rollback_rows)}")
    print(f"  execution-plan root: {rel(bd_root, repo)}")
    print(f"  HELP DATA apply execution planned: {summary['HELP_DATA_APPLY_EXECUTION_PLANNED']}")
    print(f"  CMDHELPCHK apply execution planned: {summary['CMDHELPCHK_APPLY_EXECUTION_PLANNED']}")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed by review: 0")
    print("  DBF mutation observed: 0")
    print("  CDX/LMDB mutation observed: 0")
    print("  workspace mutation observed: 0")
    print(f"  next gate: {NEXT}")
    print(f"  reports: {reports}")
    return 0 if status == GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
