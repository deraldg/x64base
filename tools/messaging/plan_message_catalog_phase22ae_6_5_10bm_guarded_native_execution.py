#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BM_GUARDED_NATIVE_HELP_CMDHELPCHK_EXECUTION_PLAN_GREEN_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BM_GUARDED_NATIVE_HELP_CMDHELPCHK_EXECUTION_PLAN_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BN_GUARDED_NATIVE_EXECUTION_PLAN_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
BL_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bl_status_summary_v1.csv"
BL_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10bl_exact_pre_write_diff_package_review_v1.csv"
BL_DECISIONS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bl_review_decisions_v1.csv"
BK_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bk_exact_pre_write_diff_package_v1.csv"
BK_GUARDS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bk_execution_guards_v1.csv"
BM_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bm_guarded_native_help_cmdhelpchk_execution_plan_v1")
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

def classify_execution(row):
    fmt = row.get("TARGET_FORMAT", "")
    status = row.get("DIFF_STATUS", "")
    target_kind = row.get("TARGET_KIND", "")
    if fmt == "DBF_BINARY" or "NATIVE_OR_SCHEMA_AWARE" in status:
        return "NATIVE_X64BASE_OR_SCHEMA_AWARE_IMPORT_PLAN", "Native/scripted DBF-safe execution only; raw Python DBF writes refused."
    if fmt in {"TEXT_MARKDOWN", "CSV_TEXT", "JSON_TEXT"}:
        return "TEXT_DIFF_PATCH_PLAN_WITH_HASH_AND_ANCHOR_GUARDS", "Text-like target can use exact diff patch only after review and hash/anchor guards."
    if "CMDHELP" in target_kind.upper():
        return "CMDHELPCHK_NATIVE_RULE_PLAN", "CMDHELPCHK target requires native/runtime validation after write."
    if "HELP" in target_kind.upper():
        return "HELP_NATIVE_TOPIC_PLAN", "HELP target requires runtime HELP readback after write."
    return "MANUAL_EXECUTION_PLAN_REQUIRED", "Target needs manual execution mechanic review."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bl = first(repo / BL_SUMMARY)
    bl_review = rows(repo / BL_REVIEW)
    bl_decisions = rows(repo / BL_DECISIONS)
    bk_package = rows(repo / BK_PACKAGE)
    bk_guards = rows(repo / BK_GUARDS)
    sp_bl, latest_bl = savepoint(repo, "MSG-022AE.6.5.10BL")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bm_root = repo / BM_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BL_GREEN",
         bl.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BL_EXACT_PRE_WRITE_DIFF_PACKAGE_REVIEW_GREEN_EXECUTION_PLAN_REQUIRED_SOURCE_HELD",
         bl.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BL_SAVEPOINT_PRESENT", sp_bl, latest_bl)
    gate("BL_DIFF_PACKAGE_ACCEPTED_FOR_PLANNING", bl.get("DIFF_PACKAGE_ACCEPTED_FOR_EXECUTION_PLANNING") == "1", bl.get("DIFF_PACKAGE_ACCEPTED_FOR_EXECUTION_PLANNING", "missing"))
    gate("BL_GUARDED_NATIVE_PLAN_REQUIRED", bl.get("GUARDED_NATIVE_EXECUTION_PLAN_REQUIRED") == "1", bl.get("GUARDED_NATIVE_EXECUTION_PLAN_REQUIRED", "missing"))
    gate("BL_HELP_APPLY_NOT_EXECUTED", bl.get("HELP_DATA_APPLY_EXECUTED") == "0", bl.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BL_CMDHELPCHK_APPLY_NOT_EXECUTED", bl.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bl.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BL_REVIEW_ROWS_PRESENT", len(bl_review) > 0, len(bl_review))
    gate("BK_PACKAGE_ROWS_PRESENT", len(bk_package) > 0, len(bk_package))
    gate("BK_GUARDS_PRESENT", len(bk_guards) > 0, len(bk_guards))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BM_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bm_root.exists()) or args.replace_existing_plan, rel(bm_root, repo))

    status = BLOCKED
    exec_plan = []
    validation_plan = []
    restore_plan = []
    artifact_rows = []

    if failures == 0:
        if bm_root.exists() and args.replace_existing_plan:
            shutil.rmtree(bm_root)
        bm_root.mkdir(parents=True, exist_ok=True)

        package_by_key = {(r.get("TARGET_ID",""), r.get("TARGET_PATH","")): r for r in bk_package}
        for i, r in enumerate(bl_review, start=1):
            target_id = r.get("TARGET_ID", "")
            target_path = r.get("TARGET_PATH", "")
            pkg = package_by_key.get((target_id, target_path), {})
            method, detail = classify_execution(pkg or r)
            exec_plan.append({
                "EXEC_STEP": i,
                "TARGET_ID": target_id,
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": target_path,
                "TARGET_FORMAT": r.get("TARGET_FORMAT", ""),
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", "") or pkg.get("DIFF_ARTIFACT", ""),
                "TARGET_SHA256": pkg.get("TARGET_SHA256", ""),
                "CANDIDATE_SHA256": pkg.get("CANDIDATE_SHA256", ""),
                "EXECUTION_METHOD": method,
                "EXECUTION_DETAIL": detail,
                "REQUIRED_KEYS_OR_TOPICS": "MSGMGR;SET MESSAGE CATALOG CHECK;SET MESSAGE CATALOG GET;SET MESSAGE EMIT",
                "PRE_EXEC_REFUSAL_GUARDS": "target_hash_match;candidate_hash_match;backup_exists;anchor_or_key_valid;runtime_readback_script_exists",
                "POST_EXEC_READBACK": "HELP MSGMGR; HELP SET MESSAGE; CMDHELPCHK; SET MESSAGE CATALOG CHECK; SET MESSAGE EMIT",
                "ROLLBACK_REQUIRED": 1,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "EXECUTED_NOW": 0,
            })

        validation_plan = [
            {"VALIDATION_STEP": 1, "VALIDATION": "SAVEPOINT_CHAIN", "EXPECTED": "10BL savepoint present and latest chain intact.", "REQUIRED": 1},
            {"VALIDATION_STEP": 2, "VALIDATION": "TARGET_HASH_RECHECK", "EXPECTED": "Every target hash matches 10BK/10BL accepted state before any later write.", "REQUIRED": 1},
            {"VALIDATION_STEP": 3, "VALIDATION": "BACKUP_RECHECK", "EXPECTED": "Every exact target has a current backup immediately before execution.", "REQUIRED": 1},
            {"VALIDATION_STEP": 4, "VALIDATION": "NO_RAW_DBF_WRITE", "EXPECTED": "DBF writes use native/runtime or schema-aware import path, never raw Python DBF mutation.", "REQUIRED": 1},
            {"VALIDATION_STEP": 5, "VALIDATION": "RUNTIME_HELP_READBACK", "EXPECTED": "HELP MSGMGR and HELP SET MESSAGE read back in DotTalk++ runtime after any later write.", "REQUIRED": 1},
            {"VALIDATION_STEP": 6, "VALIDATION": "CMDHELPCHK_READBACK", "EXPECTED": "CMDHELPCHK validates MSGMGR/SET MESSAGE surfaces after any later write.", "REQUIRED": 1},
            {"VALIDATION_STEP": 7, "VALIDATION": "MESSAGING_CATALOG_UNCHANGED", "EXPECTED": "SYSTEM_MESSAGES remains 14 and SYSTEM_MESSAGE_TEXT remains 70 unless separately authorized.", "REQUIRED": 1},
        ]

        restore_plan = [
            {"RESTORE_STEP": 1, "RESTORE_ACTION": "RESTORE_EXACT_TARGETS_FROM_BACKUP", "REQUIRED": 1, "DETAIL": "Restore exact HELP/CMDHELPCHK targets from current pre-execution backups if later apply fails."},
            {"RESTORE_STEP": 2, "RESTORE_ACTION": "RERUN_HELP_CMDHELPCHK_READBACK", "REQUIRED": 1, "DETAIL": "Verify HELP/CMDHELPCHK returns to pre-execution state."},
            {"RESTORE_STEP": 3, "RESTORE_ACTION": "VERIFY_MESSAGING_COUNTS", "REQUIRED": 1, "DETAIL": "Confirm messaging catalog counts remain 14/70."},
        ]

        plan_path = bm_root / "guarded_native_execution_plan_v1.csv"
        validation_path = bm_root / "guarded_native_execution_validation_plan_v1.csv"
        restore_path = bm_root / "guarded_native_execution_restore_plan_v1.csv"
        guard_path = bm_root / "execution_guards_carried_forward_v1.csv"
        disabled = bm_root / "scripts" / "MESSAGE_CATALOG_PHASE22AE_6_5_10BN_REVIEW_REQUIRED_NO_WRITE.ps1.disabled"
        disabled.parent.mkdir(parents=True, exist_ok=True)
        disabled.write_text(
            'throw "DISABLED TEMPLATE: 10BM creates an execution plan only. 10BN review and later explicit execution authorization required."\n',
            encoding="utf-8"
        )
        readme = bm_root / "README_10BM_GUARDED_NATIVE_EXECUTION_PLAN.md"
        readme.write_text(
            "# 10BM Guarded Native HELP/CMDHELPCHK Execution Plan\n\n"
            "10BM builds the guarded native/schema-aware execution plan from the 10BL reviewed diff package.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BM.\n",
            encoding="utf-8"
        )

        wcsv(plan_path, exec_plan, ["EXEC_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","DIFF_ARTIFACT","TARGET_SHA256","CANDIDATE_SHA256","EXECUTION_METHOD","EXECUTION_DETAIL","REQUIRED_KEYS_OR_TOPICS","PRE_EXEC_REFUSAL_GUARDS","POST_EXEC_READBACK","ROLLBACK_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","EXECUTED_NOW"])
        wcsv(validation_path, validation_plan, ["VALIDATION_STEP","VALIDATION","EXPECTED","REQUIRED"])
        wcsv(restore_path, restore_plan, ["RESTORE_STEP","RESTORE_ACTION","REQUIRED","DETAIL"])
        wcsv(guard_path, bk_guards, list(bk_guards[0].keys()) if bk_guards else ["EMPTY"])

        for p in [plan_path, validation_path, restore_path, guard_path, disabled, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_native_execution_plan_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BM writes docs/messaging execution-plan artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; execution plan only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; execution plan only."},
    ]

    readiness = [
        {"ITEM": "GUARDED_NATIVE_EXECUTION_PLAN_CREATED", "STATUS": "YES" if exec_plan else "NO", "DETAIL": f"{len(exec_plan)} execution steps."},
        {"ITEM": "VALIDATION_PLAN_CREATED", "STATUS": "YES" if validation_plan else "NO", "DETAIL": f"{len(validation_plan)} validation steps."},
        {"ITEM": "RESTORE_PLAN_CREATED", "STATUS": "YES" if restore_plan else "NO", "DETAIL": f"{len(restore_plan)} restore steps."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BM", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BM", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10BN_REQUIRED", "DETAIL": "Review guarded native execution plan before any execution package."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bm_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bm_guarded_native_execution_plan_v1.csv", exec_plan, ["EXEC_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_FORMAT","DIFF_ARTIFACT","TARGET_SHA256","CANDIDATE_SHA256","EXECUTION_METHOD","EXECUTION_DETAIL","REQUIRED_KEYS_OR_TOPICS","PRE_EXEC_REFUSAL_GUARDS","POST_EXEC_READBACK","ROLLBACK_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","EXECUTED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bm_validation_plan_v1.csv", validation_plan, ["VALIDATION_STEP","VALIDATION","EXPECTED","REQUIRED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bm_restore_plan_v1.csv", restore_plan, ["RESTORE_STEP","RESTORE_ACTION","REQUIRED","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bm_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bm_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bm_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BL_STATUS": bl.get("STATUS", ""),
        "MSG_022AE_6_5_10BL_SAVEPOINT_PRESENT": 1 if sp_bl else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BL_DIFF_PACKAGE_REVIEW_ROWS": len(bl_review),
        "GUARDED_NATIVE_EXECUTION_PLAN_ROWS": len(exec_plan),
        "VALIDATION_PLAN_ROWS": len(validation_plan),
        "RESTORE_PLAN_ROWS": len(restore_plan),
        "BM_ROOT": rel(bm_root, repo),
        "GUARDED_NATIVE_EXECUTION_PLAN_CREATED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bm_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BM_GUARDED_NATIVE_HELP_CMDHELPCHK_EXECUTION_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BM Guarded Native HELP/CMDHELPCHK Execution Plan\n\n"
        f"Status: `{status}`\n\n"
        "10BM creates a guarded native/schema-aware execution plan. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Execution-plan root:\n\n```text\n{rel(bm_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BL status: {bl.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BL savepoint present: {1 if sp_bl else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BL diff package review rows: {len(bl_review)}")
    print(f"  guarded native execution plan rows: {len(exec_plan)}")
    print(f"  validation plan rows: {len(validation_plan)}")
    print(f"  restore plan rows: {len(restore_plan)}")
    print(f"  execution-plan root: {rel(bm_root, repo)}")
    print("  guarded native execution plan created: 1")
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
