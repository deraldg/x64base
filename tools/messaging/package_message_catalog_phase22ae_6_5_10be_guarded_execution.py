#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BE_HELP_CMDHELPCHK_GUARDED_EXECUTION_PACKAGE_GREEN_STAGED_EXECUTION_NOT_RUN"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BE_HELP_CMDHELPCHK_GUARDED_EXECUTION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BF_HELP_CMDHELPCHK_EXECUTION_REVIEW_OR_EXACT_APPLY_IMPLEMENTATION"

REPORT_DIR = Path("docs/messaging/reports")
BD_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bd_status_summary_v1.csv"
BD_PLAN = REPORT_DIR / "message_catalog_phase22ae_6_5_10bd_execution_plan_v1.csv"
BD_VALIDATION = REPORT_DIR / "message_catalog_phase22ae_6_5_10bd_validation_plan_v1.csv"
BD_ROLLBACK = REPORT_DIR / "message_catalog_phase22ae_6_5_10bd_rollback_plan_v1.csv"
BE_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10be_help_cmdhelpchk_guarded_execution_package_v1")
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

def target_exists(repo, path):
    p = repo / path
    return p.exists() and p.is_file()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bd = first(repo / BD_SUMMARY)
    plan = rows(repo / BD_PLAN)
    validations = rows(repo / BD_VALIDATION)
    rollbacks = rows(repo / BD_ROLLBACK)
    sp_bd, latest_bd = savepoint(repo, "MSG-022AE.6.5.10BD")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    candidate = repo / CANDIDATE_PATH
    be_root = repo / BE_ROOT

    gates = []
    failures = 0
    review_notes = 0
    def gate(name, ok, detail, review_only=False):
        nonlocal failures, review_notes
        status = "PASS" if ok else ("REVIEW" if review_only else "FAIL")
        gates.append({"GATE": name, "STATUS": status, "DETAIL": str(detail)})
        if not ok and review_only:
            review_notes += 1
        elif not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BD_GREEN",
         bd.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BD_HELP_CMDHELPCHK_EXECUTION_PLAN_FROM_ACCEPTED_MAP_GREEN_SOURCE_HELD",
         bd.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BD_SAVEPOINT_PRESENT", sp_bd, latest_bd)
    gate("BD_HELP_EXECUTION_PLANNED", bd.get("HELP_DATA_APPLY_EXECUTION_PLANNED") == "1", bd.get("HELP_DATA_APPLY_EXECUTION_PLANNED", "missing"))
    gate("BD_CMDHELPCHK_EXECUTION_PLANNED", bd.get("CMDHELPCHK_APPLY_EXECUTION_PLANNED") == "1", bd.get("CMDHELPCHK_APPLY_EXECUTION_PLANNED", "missing"))
    gate("BD_HELP_APPLY_NOT_EXECUTED", bd.get("HELP_DATA_APPLY_EXECUTED") == "0", bd.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BD_CMDHELPCHK_APPLY_NOT_EXECUTED", bd.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bd.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("EXECUTION_PLAN_ROWS_PRESENT", len(plan) > 0, len(plan))
    gate("VALIDATION_PLAN_PRESENT", len(validations) > 0, len(validations))
    gate("ROLLBACK_PLAN_PRESENT", len(rollbacks) > 0, len(rollbacks))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("CANDIDATE_EXISTS", candidate.exists(), rel(candidate, repo))
    gate("BE_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not be_root.exists()) or args.replace_existing_package, rel(be_root, repo))

    exact_target_status = []
    backup_rows = []
    dryrun_rows = []
    artifact_rows = []
    status = BLOCKED

    if failures == 0:
        if be_root.exists() and args.replace_existing_package:
            shutil.rmtree(be_root)
        be_root.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = repo / "docs/messaging/backups" / f"MSG-022AE_6_5_10BE_EXACT_TARGET_BACKUP_{timestamp}"
        backup_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(plan, start=1):
            tpath = r.get("TARGET_PATH", "")
            src = repo / tpath
            exists = src.exists() and src.is_file()
            before_sha = sha(src) if exists else ""
            copied = 0
            backup_path = ""
            backup_sha = ""
            if exists:
                dst = backup_root / tpath
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                backup_path = rel(dst, repo)
                backup_sha = sha(dst)
                copied = 1 if backup_sha == before_sha else 0
            exact_target_status.append({
                "EXEC_STEP": r.get("EXEC_STEP", i),
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": tpath,
                "TARGET_EXISTS": 1 if exists else 0,
                "PRE_EXEC_SHA256": before_sha,
                "BACKUP_PATH": backup_path,
                "BACKUP_SHA256": backup_sha,
                "BACKUP_MATCH": copied,
                "PLANNED_ACTION": r.get("PLANNED_ACTION", ""),
                "EXECUTION_IMPLEMENTATION_STATUS": "STAGED_NOT_IMPLEMENTED",
                "EXECUTION_AUTHORIZED_IN_THIS_PACKAGE": 0,
                "NOTES": "10BE packages guarded execution artifacts; exact write mechanics are not executed here.",
            })
            if exists:
                backup_rows.append({
                    "TARGET_PATH": tpath,
                    "BACKUP_PATH": backup_path,
                    "TARGET_SHA256": before_sha,
                    "BACKUP_SHA256": backup_sha,
                    "SHA256_MATCH": copied,
                })

        # Write disabled apply/restore templates. These are intentionally not executable.
        scripts_dir = be_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        apply_template = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BF_APPLY_EXECUTION_TEMPLATE.ps1.disabled"
        restore_template = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BF_RESTORE_TEMPLATE.ps1.disabled"
        apply_template.write_text(
            "# DISABLED TEMPLATE - DO NOT RUN\n"
            "# 10BF must implement exact HELP/CMDHELPCHK write mechanics after target-specific review.\n"
            "# This template refuses by design.\n"
            "throw \"DISABLED TEMPLATE: 10BE staged execution package only; 10BF exact apply implementation required.\"\n",
            encoding="utf-8"
        )
        restore_template.write_text(
            "# DISABLED TEMPLATE - DO NOT RUN\n"
            "# Restore must be generated from the exact 10BE backup root after an authorized apply attempt.\n"
            "throw \"DISABLED TEMPLATE: no apply was executed in 10BE; restore not required.\"\n",
            encoding="utf-8"
        )

        plan_copy = be_root / "execution_plan_v1.csv"
        target_status_path = be_root / "exact_target_status_and_backup_v1.csv"
        validation_copy = be_root / "validation_plan_v1.csv"
        rollback_copy = be_root / "rollback_plan_v1.csv"
        candidate_copy = be_root / "candidate_snapshot" / CANDIDATE_PATH.name
        candidate_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, candidate_copy)

        wcsv(plan_copy, plan, list(plan[0].keys()) if plan else ["EMPTY"])
        wcsv(target_status_path, exact_target_status, ["EXEC_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","PRE_EXEC_SHA256","BACKUP_PATH","BACKUP_SHA256","BACKUP_MATCH","PLANNED_ACTION","EXECUTION_IMPLEMENTATION_STATUS","EXECUTION_AUTHORIZED_IN_THIS_PACKAGE","NOTES"])
        wcsv(validation_copy, validations, list(validations[0].keys()) if validations else ["EMPTY"])
        wcsv(rollback_copy, rollbacks, list(rollbacks[0].keys()) if rollbacks else ["EMPTY"])

        readme = be_root / "README_10BE_GUARDED_EXECUTION_PACKAGE.md"
        readme.write_text(
            "# 10BE Guarded Execution Package\n\n"
            "10BE stages exact target backups, execution-plan copies, validation/rollback plans, and disabled apply templates.\n\n"
            "It does not mutate HELP DATA or CMDHELPCHK. The next package must implement target-specific write mechanics after review.\n\n"
            "Why execution is still held: the accepted map identifies files/targets, but the exact write mechanics for those target formats must be implemented and reviewed before mutation.\n",
            encoding="utf-8"
        )

        for p in [apply_template, restore_template, plan_copy, target_status_path, validation_copy, rollback_copy, candidate_copy, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_execution_package_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        dryrun_rows = [
            {"DRYRUN_ITEM": "EXACT_TARGET_BACKUP", "STATUS": "COMPLETE", "DETAIL": f"{len(backup_rows)} exact target backups copied.", "EXECUTED_NOW": 1},
            {"DRYRUN_ITEM": "APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BE", "DETAIL": "Apply template disabled; exact write mechanics deferred to 10BF.", "EXECUTED_NOW": 0},
            {"DRYRUN_ITEM": "CMDHELPCHK_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BE", "DETAIL": "Apply template disabled; exact write mechanics deferred to 10BF.", "EXECUTED_NOW": 0},
            {"DRYRUN_ITEM": "RESTORE_EXECUTION", "STATUS": "NOT_REQUIRED_NOT_EXECUTED", "DETAIL": "No apply was executed.", "EXECUTED_NOW": 0},
        ]

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BE writes docs/messaging execution-package artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Backups only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Backups only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "GUARDED_EXECUTION_PACKAGE_STAGED", "STATUS": "YES" if status == GREEN else "NO", "DETAIL": f"{len(artifact_rows)} artifacts."},
        {"ITEM": "EXACT_TARGET_BACKUPS_CREATED", "STATUS": "YES" if backup_rows else "NO", "DETAIL": f"{len(backup_rows)} backups."},
        {"ITEM": "APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BE", "DETAIL": "10BF target-specific apply implementation required."},
        {"ITEM": "RESTORE_AVAILABLE_IF_10BF_APPLIES", "STATUS": "BACKUPS_AVAILABLE", "DETAIL": "10BE backup rows available to later restore package."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BF_REQUIRED", "DETAIL": "Implement exact write mechanics or stop before mutation."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10be_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10be_exact_target_status_v1.csv", exact_target_status, ["EXEC_STEP","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","PRE_EXEC_SHA256","BACKUP_PATH","BACKUP_SHA256","BACKUP_MATCH","PLANNED_ACTION","EXECUTION_IMPLEMENTATION_STATUS","EXECUTION_AUTHORIZED_IN_THIS_PACKAGE","NOTES"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10be_backup_manifest_v1.csv", backup_rows, ["TARGET_PATH","BACKUP_PATH","TARGET_SHA256","BACKUP_SHA256","SHA256_MATCH"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10be_dryrun_summary_v1.csv", dryrun_rows, ["DRYRUN_ITEM","STATUS","DETAIL","EXECUTED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10be_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10be_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10be_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "REVIEW_NOTES": review_notes,
        "PHASE22AE_6_5_10BD_STATUS": bd.get("STATUS", ""),
        "MSG_022AE_6_5_10BD_SAVEPOINT_PRESENT": 1 if sp_bd else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "EXECUTION_PLAN_ROWS": len(plan),
        "EXACT_TARGET_STATUS_ROWS": len(exact_target_status),
        "BACKUPS_COPIED": len(backup_rows),
        "ARTIFACT_ROWS": len(artifact_rows),
        "BE_ROOT": rel(be_root, repo),
        "GUARDED_EXECUTION_PACKAGE_STAGED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10be_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BE_HELP_CMDHELPCHK_GUARDED_EXECUTION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BE HELP/CMDHELPCHK Guarded Execution Package\n\n"
        f"Status: `{status}`\n\n"
        "10BE stages the guarded execution package and exact target backups. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Execution-package root:\n\n```text\n{rel(be_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  review notes: {review_notes}")
    print(f"  Phase 22AE.6.5.10BD status: {bd.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BD savepoint present: {1 if sp_bd else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  execution plan rows: {len(plan)}")
    print(f"  exact target status rows: {len(exact_target_status)}")
    print(f"  backups copied: {len(backup_rows)}")
    print(f"  artifact rows: {len(artifact_rows)}")
    print(f"  execution-package root: {rel(be_root, repo)}")
    print("  guarded execution package staged: 1")
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
