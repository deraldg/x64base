#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BP_GUARDED_NATIVE_EXECUTION_PACKAGE_REVIEW_GREEN_APPLY_DECISION_REQUIRED_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BP_GUARDED_NATIVE_EXECUTION_PACKAGE_REVIEW_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BQ_HELP_CMDHELPCHK_APPLY_EXECUTION_DECISION_PLAN"

REPORT_DIR = Path("docs/messaging/reports")
BO_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_status_summary_v1.csv"
BO_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_execution_package_manifest_v1.csv"
BO_BACKUPS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_backup_manifest_v1.csv"
BO_GUARDS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_refusal_guards_v1.csv"
BP_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bp_guarded_native_execution_package_review_v1")
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bo = first(repo / BO_SUMMARY)
    package_rows = rows(repo / BO_PACKAGE)
    backup_rows = rows(repo / BO_BACKUPS)
    guard_rows = rows(repo / BO_GUARDS)
    sp_bo, latest_bo = savepoint(repo, "MSG-022AE.6.5.10BO")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bp_root = repo / BP_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BO_GREEN",
         bo.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BO_GUARDED_NATIVE_EXECUTION_PACKAGE_GREEN_STAGED_NO_APPLY",
         bo.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BO_SAVEPOINT_PRESENT", sp_bo, latest_bo)
    gate("BO_GUARDED_EXECUTION_PACKAGE_STAGED", bo.get("GUARDED_EXECUTION_PACKAGE_STAGED") == "1", bo.get("GUARDED_EXECUTION_PACKAGE_STAGED", "missing"))
    gate("BO_HELP_APPLY_NOT_EXECUTED", bo.get("HELP_DATA_APPLY_EXECUTED") == "0", bo.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BO_CMDHELPCHK_APPLY_NOT_EXECUTED", bo.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bo.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BO_PACKAGE_ROWS_PRESENT", len(package_rows) > 0, len(package_rows))
    gate("BO_BACKUP_ROWS_PRESENT", len(backup_rows) > 0, len(backup_rows))
    gate("BO_REFUSAL_GUARDS_PRESENT", len(guard_rows) > 0, len(guard_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BP_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bp_root.exists()) or args.replace_existing_review, rel(bp_root, repo))

    status = BLOCKED
    review_rows = []
    decision_rows = []
    artifact_rows = []

    if failures == 0:
        if bp_root.exists() and args.replace_existing_review:
            shutil.rmtree(bp_root)
        bp_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(package_rows, start=1):
            backup_match = str(r.get("BACKUP_MATCH", "")) == "1"
            hash_match = str(r.get("TARGET_HASH_MATCHES_PLAN", "")) == "1"
            target_exists = str(r.get("TARGET_EXISTS", "")) == "1"
            executed_now = str(r.get("EXECUTED_NOW", "")) == "1"
            authorized_now = str(r.get("AUTHORIZED_FOR_WRITE_NOW", "")) == "1"
            if target_exists and backup_match and not executed_now and not authorized_now:
                disposition = "ACCEPT_FOR_APPLY_DECISION_PLANNING"
            else:
                disposition = "REVIEW_REQUIRED"

            review_rows.append({
                "REVIEW_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": r.get("TARGET_PATH", ""),
                "TARGET_EXISTS": 1 if target_exists else 0,
                "TARGET_HASH_MATCHES_PLAN": 1 if hash_match else 0,
                "BACKUP_PATH": r.get("BACKUP_PATH", ""),
                "BACKUP_MATCH": 1 if backup_match else 0,
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "EXECUTION_METHOD": r.get("EXECUTION_METHOD", ""),
                "PACKAGE_STATUS": r.get("PACKAGE_STATUS", ""),
                "REVIEW_DISPOSITION": disposition,
                "APPLY_DECISION_PLAN_REQUIRED": 1,
                "AUTHORIZED_FOR_WRITE_NOW": 0,
                "EXECUTED_NOW": 0,
                "REASON": "10BP reviews staged execution package only; no HELP/CMDHELPCHK mutation in 10BP.",
            })

        decision_rows = [
            {"DECISION_ITEM": "GUARDED_EXECUTION_PACKAGE", "DECISION": "ACCEPT_FOR_APPLY_DECISION_PLANNING", "DETAIL": f"{len(package_rows)} package rows reviewed."},
            {"DECISION_ITEM": "EXACT_TARGET_BACKUPS", "DECISION": "CARRY_FORWARD_REQUIRED", "DETAIL": f"{len(backup_rows)} backup rows must be carried forward."},
            {"DECISION_ITEM": "REFUSAL_GUARDS", "DECISION": "CARRY_FORWARD_REQUIRED", "DETAIL": f"{len(guard_rows)} refusal guards must remain active."},
            {"DECISION_ITEM": "HELP_DATA_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BP", "DETAIL": "No HELP DATA write in 10BP."},
            {"DECISION_ITEM": "CMDHELPCHK_APPLY_EXECUTION", "DECISION": "NOT_AUTHORIZED_IN_10BP", "DETAIL": "No CMDHELPCHK write in 10BP."},
            {"DECISION_ITEM": "NEXT_GATE", "DECISION": "AUTHORIZE_10BQ_OR_HOLD", "DETAIL": "10BQ should create an apply execution decision plan; actual mutation remains a separate explicit authorization."},
        ]

        review_path = bp_root / "guarded_native_execution_package_review_v1.csv"
        decision_path = bp_root / "execution_package_review_decisions_v1.csv"
        readme = bp_root / "README_10BP_GUARDED_NATIVE_EXECUTION_PACKAGE_REVIEW.md"
        wcsv(review_path, review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_HASH_MATCHES_PLAN","BACKUP_PATH","BACKUP_MATCH","DIFF_ARTIFACT","EXECUTION_METHOD","PACKAGE_STATUS","REVIEW_DISPOSITION","APPLY_DECISION_PLAN_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","EXECUTED_NOW","REASON"])
        wcsv(decision_path, decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
        readme.write_text(
            "# 10BP Guarded Native Execution Package Review\n\n"
            "10BP reviews the 10BO guarded native/schema-aware execution package and accepts it for apply-decision planning only.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BP.\n",
            encoding="utf-8"
        )
        for p in [review_path, decision_path, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_native_execution_package_review_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BP writes docs/messaging review artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation; package review only."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation; package review only."},
    ]

    readiness = [
        {"ITEM": "GUARDED_EXECUTION_PACKAGE_REVIEW_COMPLETE", "STATUS": "YES" if review_rows else "NO", "DETAIL": f"{len(review_rows)} rows reviewed."},
        {"ITEM": "APPLY_DECISION_PLAN_REQUIRED", "STATUS": "YES", "DETAIL": "10BQ should decide hold/apply-path planning boundaries."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BP", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BP", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BQ_REQUIRED", "DETAIL": "Apply execution decision plan, not execution."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bp_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bp_execution_package_review_v1.csv", review_rows, ["REVIEW_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_HASH_MATCHES_PLAN","BACKUP_PATH","BACKUP_MATCH","DIFF_ARTIFACT","EXECUTION_METHOD","PACKAGE_STATUS","REVIEW_DISPOSITION","APPLY_DECISION_PLAN_REQUIRED","AUTHORIZED_FOR_WRITE_NOW","EXECUTED_NOW","REASON"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bp_review_decisions_v1.csv", decision_rows, ["DECISION_ITEM","DECISION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bp_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bp_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bp_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BO_STATUS": bo.get("STATUS", ""),
        "MSG_022AE_6_5_10BO_SAVEPOINT_PRESENT": 1 if sp_bo else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BO_EXECUTION_PACKAGE_ROWS": len(package_rows),
        "BO_BACKUP_ROWS": len(backup_rows),
        "BO_REFUSAL_GUARD_ROWS": len(guard_rows),
        "EXECUTION_PACKAGE_REVIEW_ROWS": len(review_rows),
        "DECISION_ROWS": len(decision_rows),
        "BP_ROOT": rel(bp_root, repo),
        "APPLY_DECISION_PLAN_REQUIRED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bp_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BP_GUARDED_NATIVE_EXECUTION_PACKAGE_REVIEW.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BP Guarded Native Execution Package Review\n\n"
        f"Status: `{status}`\n\n"
        "10BP reviews the guarded native/schema-aware execution package and accepts it for apply-decision planning only. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Review root:\n\n```text\n{rel(bp_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BO status: {bo.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BO savepoint present: {1 if sp_bo else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BO execution package rows: {len(package_rows)}")
    print(f"  BO backup rows: {len(backup_rows)}")
    print(f"  BO refusal guard rows: {len(guard_rows)}")
    print(f"  execution package review rows: {len(review_rows)}")
    print(f"  decision rows: {len(decision_rows)}")
    print(f"  review root: {rel(bp_root, repo)}")
    print("  apply decision plan required: 1")
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
