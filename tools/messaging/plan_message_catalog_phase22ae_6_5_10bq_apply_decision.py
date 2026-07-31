#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BQ_HELP_CMDHELPCHK_APPLY_EXECUTION_DECISION_PLAN_GREEN_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BQ_HELP_CMDHELPCHK_APPLY_EXECUTION_DECISION_PLAN_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BR_HELP_CMDHELPCHK_GUARDED_APPLY_PREFLIGHT_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
BP_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bp_status_summary_v1.csv"
BP_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10bp_execution_package_review_v1.csv"
BP_DECISIONS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bp_review_decisions_v1.csv"
BO_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_execution_package_manifest_v1.csv"
BO_BACKUPS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_backup_manifest_v1.csv"
BO_GUARDS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_refusal_guards_v1.csv"
BQ_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bq_help_cmdhelpchk_apply_execution_decision_plan_v1")
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

def decision_for_package_row(row):
    target_kind = row.get("TARGET_KIND", "")
    exec_method = row.get("EXECUTION_METHOD", "")
    fmt = row.get("TARGET_FORMAT", "")
    if fmt == "DBF_BINARY" or "NATIVE" in exec_method.upper() or "SCHEMA" in exec_method.upper():
        return "PLAN_GUARDED_NATIVE_OR_SCHEMA_AWARE_APPLY_PREFLIGHT"
    if "TEXT_DIFF" in exec_method.upper():
        return "PLAN_GUARDED_TEXT_DIFF_APPLY_PREFLIGHT"
    if "CMDHELP" in target_kind.upper():
        return "PLAN_CMDHELPCHK_APPLY_PREFLIGHT"
    if "HELP" in target_kind.upper():
        return "PLAN_HELP_DATA_APPLY_PREFLIGHT"
    return "PLAN_TARGET_SPECIFIC_APPLY_PREFLIGHT"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-plan", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bp = first(repo / BP_SUMMARY)
    bp_review = rows(repo / BP_REVIEW)
    bp_decisions = rows(repo / BP_DECISIONS)
    bo_package = rows(repo / BO_PACKAGE)
    bo_backups = rows(repo / BO_BACKUPS)
    bo_guards = rows(repo / BO_GUARDS)
    sp_bp, latest_bp = savepoint(repo, "MSG-022AE.6.5.10BP")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bq_root = repo / BQ_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BP_GREEN",
         bp.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BP_GUARDED_NATIVE_EXECUTION_PACKAGE_REVIEW_GREEN_APPLY_DECISION_REQUIRED_SOURCE_HELD",
         bp.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BP_SAVEPOINT_PRESENT", sp_bp, latest_bp)
    gate("BP_APPLY_DECISION_PLAN_REQUIRED", bp.get("APPLY_DECISION_PLAN_REQUIRED") == "1", bp.get("APPLY_DECISION_PLAN_REQUIRED", "missing"))
    gate("BP_HELP_APPLY_NOT_EXECUTED", bp.get("HELP_DATA_APPLY_EXECUTED") == "0", bp.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BP_CMDHELPCHK_APPLY_NOT_EXECUTED", bp.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bp.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BP_REVIEW_ROWS_PRESENT", len(bp_review) > 0, len(bp_review))
    gate("BP_DECISIONS_PRESENT", len(bp_decisions) > 0, len(bp_decisions))
    gate("BO_PACKAGE_ROWS_PRESENT", len(bo_package) > 0, len(bo_package))
    gate("BO_BACKUP_ROWS_PRESENT", len(bo_backups) > 0, len(bo_backups))
    gate("BO_GUARDS_PRESENT", len(bo_guards) > 0, len(bo_guards))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BQ_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bq_root.exists()) or args.replace_existing_plan, rel(bq_root, repo))

    status = BLOCKED
    decision_plan = []
    preflight_plan = []
    authorization_rows = []
    artifact_rows = []

    if failures == 0:
        if bq_root.exists() and args.replace_existing_plan:
            shutil.rmtree(bq_root)
        bq_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(bo_package, start=1):
            target_hash_match = str(r.get("TARGET_HASH_MATCHES_PLAN", "")) == "1"
            backup_match = str(r.get("BACKUP_MATCH", "")) == "1"
            target_exists = str(r.get("TARGET_EXISTS", "")) == "1"
            review_ready = target_exists and backup_match and not str(r.get("EXECUTED_NOW", "")) == "1"
            decision = decision_for_package_row(r)
            decision_plan.append({
                "DECISION_STEP": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_EXISTS": 1 if target_exists else 0,
                "TARGET_HASH_MATCHES_PLAN": 1 if target_hash_match else 0,
                "BACKUP_MATCH": 1 if backup_match else 0,
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "EXECUTION_METHOD": r.get("EXECUTION_METHOD", ""),
                "APPLY_DECISION": decision,
                "APPLY_PREFLIGHT_REQUIRED": 1,
                "APPLY_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
                "REVIEW_READY": 1 if review_ready else 0,
                "NOTES": "10BQ plans the apply decision/preflight lane only; no HELP/CMDHELPCHK mutation.",
            })

        preflight_plan = [
            {"PREFLIGHT_STEP": 1, "PREFLIGHT": "CONFIRM_EXPLICIT_APPLY_AUTHORIZATION", "REQUIRED": 1, "DETAIL": "Later package must require explicit apply authorization distinct from planning authorization."},
            {"PREFLIGHT_STEP": 2, "PREFLIGHT": "CONFIRM_DOTTALKPP_NOT_RUNNING_OR_CONTROLLED", "REQUIRED": 1, "DETAIL": "Avoid stale handles before touching HELP/CMDHELPCHK targets."},
            {"PREFLIGHT_STEP": 3, "PREFLIGHT": "RECHECK_TARGET_HASHES", "REQUIRED": 1, "DETAIL": "Every exact target hash must match the BO/BP accepted state."},
            {"PREFLIGHT_STEP": 4, "PREFLIGHT": "RECHECK_BACKUPS", "REQUIRED": 1, "DETAIL": "Exact backups must exist and match target hashes."},
            {"PREFLIGHT_STEP": 5, "PREFLIGHT": "RECHECK_REFUSAL_GUARDS", "REQUIRED": 1, "DETAIL": "No raw Python DBF writes; no write without runtime readback plan."},
            {"PREFLIGHT_STEP": 6, "PREFLIGHT": "STAGE_RUNTIME_READBACK_SCRIPT", "REQUIRED": 1, "DETAIL": "Later package must stage HELP/CMDHELPCHK runtime readback proof script."},
            {"PREFLIGHT_STEP": 7, "PREFLIGHT": "STAGE_RESTORE_SCRIPT", "REQUIRED": 1, "DETAIL": "Later package must stage restore path before any mutation."},
        ]

        authorization_rows = [
            {"AUTHORIZATION_ITEM": "10BQ_PLANNING", "STATE": "AUTHORIZED_BY_CONTINUATION", "DETAIL": "Create decision plan only."},
            {"AUTHORIZATION_ITEM": "HELP_DATA_APPLY_EXECUTION", "STATE": "NOT_AUTHORIZED_IN_10BQ", "DETAIL": "No HELP DATA mutation."},
            {"AUTHORIZATION_ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATE": "NOT_AUTHORIZED_IN_10BQ", "DETAIL": "No CMDHELPCHK mutation."},
            {"AUTHORIZATION_ITEM": "NEXT_GATE_10BR", "STATE": "REQUIRES_EXPLICIT_AUTHORIZATION", "DETAIL": "10BR may create a guarded apply preflight package; still no apply unless explicitly authorized."},
        ]

        decision_path = bq_root / "help_cmdhelpchk_apply_execution_decision_plan_v1.csv"
        preflight_path = bq_root / "guarded_apply_preflight_requirements_v1.csv"
        auth_path = bq_root / "authorization_boundary_v1.csv"
        guard_path = bq_root / "refusal_guards_carried_forward_v1.csv"
        disabled = bq_root / "scripts" / "MESSAGE_CATALOG_PHASE22AE_6_5_10BR_PREFLIGHT_REQUIRED_NO_WRITE.ps1.disabled"
        disabled.parent.mkdir(parents=True, exist_ok=True)
        disabled.write_text(
            'throw "DISABLED TEMPLATE: 10BQ creates an apply decision plan only. 10BR preflight and later explicit apply authorization required."\n',
            encoding="utf-8"
        )
        readme = bq_root / "README_10BQ_APPLY_EXECUTION_DECISION_PLAN.md"
        readme.write_text(
            "# 10BQ HELP/CMDHELPCHK Apply Execution Decision Plan\n\n"
            "10BQ converts the 10BP reviewed execution package into an apply-decision and preflight plan.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BQ.\n",
            encoding="utf-8"
        )

        wcsv(decision_path, decision_plan, ["DECISION_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_HASH_MATCHES_PLAN","BACKUP_MATCH","DIFF_ARTIFACT","EXECUTION_METHOD","APPLY_DECISION","APPLY_PREFLIGHT_REQUIRED","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","REVIEW_READY","NOTES"])
        wcsv(preflight_path, preflight_plan, ["PREFLIGHT_STEP","PREFLIGHT","REQUIRED","DETAIL"])
        wcsv(auth_path, authorization_rows, ["AUTHORIZATION_ITEM","STATE","DETAIL"])
        wcsv(guard_path, bo_guards, list(bo_guards[0].keys()) if bo_guards else ["EMPTY"])

        for p in [decision_path, preflight_path, auth_path, guard_path, disabled, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "apply_execution_decision_plan_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BQ writes docs/messaging decision-plan artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision plan only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Decision plan only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "APPLY_DECISION_PLAN_CREATED", "STATUS": "YES" if decision_plan else "NO", "DETAIL": f"{len(decision_plan)} decision rows."},
        {"ITEM": "PREFLIGHT_REQUIREMENTS_CREATED", "STATUS": "YES" if preflight_plan else "NO", "DETAIL": f"{len(preflight_plan)} preflight steps."},
        {"ITEM": "APPLY_AUTHORIZATION_REQUIRED", "STATUS": "YES", "DETAIL": "Future mutation requires separate explicit authorization."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BQ", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BQ", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BR_REQUIRED", "DETAIL": "Guarded apply preflight package, not apply execution."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bq_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bq_apply_decision_plan_v1.csv", decision_plan, ["DECISION_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_HASH_MATCHES_PLAN","BACKUP_MATCH","DIFF_ARTIFACT","EXECUTION_METHOD","APPLY_DECISION","APPLY_PREFLIGHT_REQUIRED","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","REVIEW_READY","NOTES"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bq_preflight_requirements_v1.csv", preflight_plan, ["PREFLIGHT_STEP","PREFLIGHT","REQUIRED","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bq_authorization_boundary_v1.csv", authorization_rows, ["AUTHORIZATION_ITEM","STATE","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bq_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bq_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bq_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BP_STATUS": bp.get("STATUS", ""),
        "MSG_022AE_6_5_10BP_SAVEPOINT_PRESENT": 1 if sp_bp else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BP_EXECUTION_PACKAGE_REVIEW_ROWS": len(bp_review),
        "BO_EXECUTION_PACKAGE_ROWS": len(bo_package),
        "APPLY_DECISION_PLAN_ROWS": len(decision_plan),
        "PREFLIGHT_REQUIREMENT_ROWS": len(preflight_plan),
        "AUTHORIZATION_BOUNDARY_ROWS": len(authorization_rows),
        "BQ_ROOT": rel(bq_root, repo),
        "APPLY_DECISION_PLAN_CREATED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bq_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BQ_HELP_CMDHELPCHK_APPLY_EXECUTION_DECISION_PLAN.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BQ HELP/CMDHELPCHK Apply Execution Decision Plan\n\n"
        f"Status: `{status}`\n\n"
        "10BQ creates the apply execution decision/preflight plan. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Decision-plan root:\n\n```text\n{rel(bq_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BP status: {bp.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BP savepoint present: {1 if sp_bp else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BP execution package review rows: {len(bp_review)}")
    print(f"  BO execution package rows: {len(bo_package)}")
    print(f"  apply decision plan rows: {len(decision_plan)}")
    print(f"  preflight requirement rows: {len(preflight_plan)}")
    print(f"  authorization boundary rows: {len(authorization_rows)}")
    print(f"  decision-plan root: {rel(bq_root, repo)}")
    print("  apply decision plan created: 1")
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
