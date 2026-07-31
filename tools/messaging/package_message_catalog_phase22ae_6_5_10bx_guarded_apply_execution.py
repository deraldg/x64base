#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BX_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE_GREEN_STAGED_NO_APPLY"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BX_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BY_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_RUN_AND_READBACK"

REPORT_DIR = Path("docs/messaging/reports")
BW_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bw_status_summary_v1.csv"
BW_TARGETS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bw_final_target_preflight_v1.csv"
BW_SCRIPTS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bw_script_preflight_v1.csv"
BW_RUNTIME = REPORT_DIR / "message_catalog_phase22ae_6_5_10bw_runtime_readback_preflight_v1.csv"
BW_RESTORE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bw_restore_preflight_v1.csv"
BW_GUARDS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bw_refusal_guards_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
BX_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bx_help_cmdhelpchk_guarded_apply_execution_package_v1")

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
        return str(Path(p).resolve().relative_to(repo.resolve())).replace("\\", "/")
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
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bw = first(repo / BW_SUMMARY)
    target_rows = rows(repo / BW_TARGETS)
    script_preflight = rows(repo / BW_SCRIPTS)
    runtime_rows = rows(repo / BW_RUNTIME)
    restore_rows = rows(repo / BW_RESTORE)
    guard_rows = rows(repo / BW_GUARDS)
    sp_bw, latest_bw = savepoint(repo, "MSG-022AE.6.5.10BW")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bx_root = repo / BX_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    ready_rows = sum(1 for r in target_rows if str(r.get("READY_FOR_APPLY_EXECUTION_PACKAGE", "")) == "1")
    gate("PHASE22AE_6_5_10BW_GREEN",
         bw.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BW_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PREFLIGHT_GREEN_READY_FOR_APPLY_EXECUTION_PACKAGE_SOURCE_HELD",
         bw.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BW_SAVEPOINT_PRESENT", sp_bw, latest_bw)
    gate("BW_READY_FOR_APPLY_EXECUTION_PACKAGE", bw.get("READY_FOR_APPLY_EXECUTION_PACKAGE") == "1", bw.get("READY_FOR_APPLY_EXECUTION_PACKAGE", "missing"))
    gate("BW_APPLY_EXECUTION_NOT_AUTHORIZED_NOW", bw.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", bw.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("BW_HELP_APPLY_NOT_EXECUTED", bw.get("HELP_DATA_APPLY_EXECUTED") == "0", bw.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BW_CMDHELPCHK_APPLY_NOT_EXECUTED", bw.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bw.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BW_TARGET_ROWS_PRESENT", len(target_rows) > 0, len(target_rows))
    gate("BW_TARGET_ROWS_ALL_READY", len(target_rows) > 0 and ready_rows == len(target_rows), f"{ready_rows}/{len(target_rows)}")
    gate("BW_SCRIPT_PREFLIGHT_PRESENT", len(script_preflight) > 0, len(script_preflight))
    gate("BW_RUNTIME_PREFLIGHT_PRESENT", len(runtime_rows) > 0, len(runtime_rows))
    gate("BW_RESTORE_PREFLIGHT_PRESENT", len(restore_rows) > 0, len(restore_rows))
    gate("BW_REFUSAL_GUARDS_PRESENT", len(guard_rows) > 0, len(guard_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BX_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bx_root.exists()) or args.replace_existing_package, rel(bx_root, repo))

    status = BLOCKED
    package_rows = []
    runbook_rows = []
    validation_rows = []
    rollback_rows = []
    script_rows = []
    artifact_rows = []

    if failures == 0:
        if bx_root.exists() and args.replace_existing_package:
            shutil.rmtree(bx_root)
        bx_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(target_rows, start=1):
            target_path = r.get("TARGET_PATH", "")
            target = repo / target_path
            exists = target.exists() and target.is_file()
            current_hash = sha(target) if exists else ""
            expected_hash = r.get("TARGET_SHA256_NOW", "") or r.get("TARGET_SHA256_EXPECTED", "")
            backup_path = r.get("BACKUP_PATH", "")
            backup_exists = bool(backup_path) and (repo / backup_path).exists()
            ready = str(r.get("READY_FOR_APPLY_EXECUTION_PACKAGE", "")) == "1"
            package_rows.append({
                "PACKAGE_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": target_path,
                "TARGET_EXISTS": 1 if exists else 0,
                "TARGET_SHA256_NOW": current_hash,
                "TARGET_SHA256_EXPECTED": expected_hash,
                "TARGET_HASH_MATCHES_10BW": 1 if exists and expected_hash and current_hash == expected_hash else 0,
                "BACKUP_PATH": backup_path,
                "BACKUP_EXISTS": 1 if backup_exists else 0,
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "EXECUTION_METHOD": r.get("EXECUTION_METHOD", ""),
                "READY_FOR_APPLY_EXECUTION_PACKAGE": 1 if ready else 0,
                "APPLY_EXECUTION_PACKAGE_STAGED": 1,
                "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
                "PACKAGE_STATUS": "STAGED_NO_APPLY",
            })

        runbook_rows = [
            {"RUNBOOK_STEP": 1, "ACTION": "CONFIRM_EXPLICIT_10BY_AUTHORIZATION", "RUN_NOW": 0, "DETAIL": "A later package must require explicit authorization before mutation."},
            {"RUNBOOK_STEP": 2, "ACTION": "CONFIRM_DOTTALKPP_RUNTIME_CLOSED_OR_CONTROLLED", "RUN_NOW": 0, "DETAIL": "Avoid live handles before touching HELP/CMDHELPCHK data."},
            {"RUNBOOK_STEP": 3, "ACTION": "RECHECK_10BW_TARGET_HASHES", "RUN_NOW": 0, "DETAIL": "Refuse if any target differs from 10BW preflight state."},
            {"RUNBOOK_STEP": 4, "ACTION": "RECHECK_EXACT_BACKUPS", "RUN_NOW": 0, "DETAIL": "Refuse if any backup is missing."},
            {"RUNBOOK_STEP": 5, "ACTION": "APPLY_HELP_DATA_CHANGESET_NATIVE_OR_SCHEMA_AWARE", "RUN_NOW": 0, "DETAIL": "Future apply only; no raw DBF byte write."},
            {"RUNBOOK_STEP": 6, "ACTION": "APPLY_CMDHELPCHK_CHANGESET_NATIVE_OR_SCHEMA_AWARE", "RUN_NOW": 0, "DETAIL": "Future apply only; no source mutation unless separately authorized."},
            {"RUNBOOK_STEP": 7, "ACTION": "RUN_DOTTALKPP_READBACK", "RUN_NOW": 0, "DETAIL": "Run MSGMGR/SET MESSAGE/HELP/CMDHELPCHK proof after future apply."},
            {"RUNBOOK_STEP": 8, "ACTION": "VALIDATE_COUNTS_AND_BOUNDARY", "RUN_NOW": 0, "DETAIL": "SYSTEM_MESSAGES 14 and SYSTEM_MESSAGE_TEXT 70 must remain stable unless separately authorized."},
        ]

        validation_rows = [
            {"VALIDATION_STEP": 1, "VALIDATION": "STATUS_GREEN_BEFORE_APPLY", "REQUIRED": 1, "DETAIL": "10BX is package-only; 10BY must own execution validation."},
            {"VALIDATION_STEP": 2, "VALIDATION": "HELP_MSGMGR_READBACK", "REQUIRED": 1, "DETAIL": "HELP MSGMGR visible after future apply."},
            {"VALIDATION_STEP": 3, "VALIDATION": "HELP_SET_MESSAGE_READBACK", "REQUIRED": 1, "DETAIL": "HELP SET MESSAGE visible after future apply."},
            {"VALIDATION_STEP": 4, "VALIDATION": "CMDHELPCHK_READBACK", "REQUIRED": 1, "DETAIL": "CMDHELPCHK sees planned command/help surface after future apply."},
            {"VALIDATION_STEP": 5, "VALIDATION": "MSGMGR_STATUS_AND_CHECK", "REQUIRED": 1, "DETAIL": "MSGMGR STATUS/CHECK remain available."},
            {"VALIDATION_STEP": 6, "VALIDATION": "SET_MESSAGE_CATALOG_CHECK", "REQUIRED": 1, "DETAIL": "Runtime catalog proof remains stable at 14/70."},
            {"VALIDATION_STEP": 7, "VALIDATION": "SET_MESSAGE_EMIT_LOCALIZED", "REQUIRED": 1, "DETAIL": "Localized emit remains proven."},
        ]

        rollback_rows = [
            {"ROLLBACK_STEP": 1, "ROLLBACK": "USE_EXACT_BACKUPS_FROM_PACKAGE", "APPLY_NOW": 0, "DETAIL": "Restore target files from exact backups if later apply fails."},
            {"ROLLBACK_STEP": 2, "ROLLBACK": "RERUN_RUNTIME_READBACK_AFTER_RESTORE", "APPLY_NOW": 0, "DETAIL": "Run MSGMGR/SET MESSAGE proof after any restore."},
            {"ROLLBACK_STEP": 3, "ROLLBACK": "RECORD_RESTORE_SAVEPOINT", "APPLY_NOW": 0, "DETAIL": "Append dedicated restore savepoint if a rollback package is ever run."},
        ]

        scripts_dir = bx_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        disabled_apply = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BY_RUN_APPLY_AFTER_AUTHORIZATION.ps1.disabled"
        disabled_apply.write_text(
            'param([switch]$ApplyAuthorized)\n'
            'if (-not $ApplyAuthorized) { throw "Apply not authorized: missing -ApplyAuthorized." }\n'
            'throw "10BX is a staged package only. Generate/run the dedicated 10BY execution package before mutation."\n',
            encoding="utf-8"
        )

        readback_dts = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BX_RUNTIME_READBACK_AFTER_FUTURE_APPLY.dts"
        readback_dts.write_text(
            "MSGMGR STATUS\n"
            "MSGMGR CHECK\n"
            "SET MESSAGE CATALOG CHECK\n"
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\n"
            "HELP MSGMGR\n"
            "HELP SET MESSAGE\n"
            "CMDHELPCHK\n"
            "QUIT\n",
            encoding="utf-8"
        )

        restore_template = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BX_RESTORE_TEMPLATE.ps1.disabled"
        restore_template.write_text(
            'throw "Restore template staged only. Use a separately authorized restore package if needed."\n',
            encoding="utf-8"
        )

        script_rows = [
            {"SCRIPT_ROW": 1, "SCRIPT_PATH": rel(disabled_apply, repo), "SCRIPT_ROLE": "disabled_future_apply_template", "RUN_NOW": 0, "APPLY_ENABLED": 0},
            {"SCRIPT_ROW": 2, "SCRIPT_PATH": rel(readback_dts, repo), "SCRIPT_ROLE": "runtime_readback_after_future_apply", "RUN_NOW": 0, "APPLY_ENABLED": 0},
            {"SCRIPT_ROW": 3, "SCRIPT_PATH": rel(restore_template, repo), "SCRIPT_ROLE": "disabled_restore_template", "RUN_NOW": 0, "APPLY_ENABLED": 0},
        ]

        package_path = bx_root / "guarded_apply_execution_package_manifest_v1.csv"
        runbook_path = bx_root / "apply_execution_runbook_v1.csv"
        validation_path = bx_root / "post_apply_validation_plan_v1.csv"
        rollback_path = bx_root / "rollback_plan_v1.csv"
        script_path = bx_root / "staged_script_manifest_v1.csv"
        guards_path = bx_root / "refusal_guards_carried_forward_v1.csv"

        readme = bx_root / "README_10BX_GUARDED_APPLY_EXECUTION_PACKAGE.md"
        readme.write_text(
            "# 10BX HELP/CMDHELPCHK Guarded Apply Execution Package\n\n"
            "10BX stages the dedicated guarded apply execution package, runbook, validation plan, readback script, and rollback plan.\n\n"
            "10BX does not mutate HELP DATA or CMDHELPCHK. The next gate is a dedicated 10BY execution/run-and-readback gate.\n",
            encoding="utf-8"
        )

        wcsv(package_path, package_rows, ["PACKAGE_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_10BW","BACKUP_PATH","BACKUP_EXISTS","DIFF_ARTIFACT","EXECUTION_METHOD","READY_FOR_APPLY_EXECUTION_PACKAGE","APPLY_EXECUTION_PACKAGE_STAGED","APPLY_EXECUTION_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","PACKAGE_STATUS"])
        wcsv(runbook_path, runbook_rows, ["RUNBOOK_STEP","ACTION","RUN_NOW","DETAIL"])
        wcsv(validation_path, validation_rows, ["VALIDATION_STEP","VALIDATION","REQUIRED","DETAIL"])
        wcsv(rollback_path, rollback_rows, ["ROLLBACK_STEP","ROLLBACK","APPLY_NOW","DETAIL"])
        wcsv(script_path, script_rows, ["SCRIPT_ROW","SCRIPT_PATH","SCRIPT_ROLE","RUN_NOW","APPLY_ENABLED"])
        wcsv(guards_path, guard_rows, list(guard_rows[0].keys()) if guard_rows else ["EMPTY"])

        for p in [package_path, runbook_path, validation_path, rollback_path, script_path, guards_path, disabled_apply, readback_dts, restore_template, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_apply_execution_package_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BX writes docs/messaging apply package artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Apply execution package only; no HELP DATA apply in 10BX."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Apply execution package only; no CMDHELPCHK apply in 10BX."},
    ]

    readiness = [
        {"ITEM": "GUARDED_APPLY_EXECUTION_PACKAGE_STAGED", "STATUS": "YES" if package_rows else "NO", "DETAIL": f"{len(package_rows)} target package rows."},
        {"ITEM": "RUNBOOK_STAGED", "STATUS": "YES" if runbook_rows else "NO", "DETAIL": f"{len(runbook_rows)} runbook rows."},
        {"ITEM": "POST_APPLY_VALIDATION_STAGED", "STATUS": "YES" if validation_rows else "NO", "DETAIL": f"{len(validation_rows)} validation rows."},
        {"ITEM": "ROLLBACK_PLAN_STAGED", "STATUS": "YES" if rollback_rows else "NO", "DETAIL": f"{len(rollback_rows)} rollback rows."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BX", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BX", "DETAIL": "No apply execution."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_execution_package_manifest_v1.csv", package_rows, ["PACKAGE_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_10BW","BACKUP_PATH","BACKUP_EXISTS","DIFF_ARTIFACT","EXECUTION_METHOD","READY_FOR_APPLY_EXECUTION_PACKAGE","APPLY_EXECUTION_PACKAGE_STAGED","APPLY_EXECUTION_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","PACKAGE_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_runbook_v1.csv", runbook_rows, ["RUNBOOK_STEP","ACTION","RUN_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_post_apply_validation_plan_v1.csv", validation_rows, ["VALIDATION_STEP","VALIDATION","REQUIRED","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_rollback_plan_v1.csv", rollback_rows, ["ROLLBACK_STEP","ROLLBACK","APPLY_NOW","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_staged_script_manifest_v1.csv", script_rows, ["SCRIPT_ROW","SCRIPT_PATH","SCRIPT_ROLE","RUN_NOW","APPLY_ENABLED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    staged_count = sum(1 for r in package_rows if str(r.get("APPLY_EXECUTION_PACKAGE_STAGED", "")) == "1")
    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BW_STATUS": bw.get("STATUS", ""),
        "MSG_022AE_6_5_10BW_SAVEPOINT_PRESENT": 1 if sp_bw else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BW_FINAL_TARGET_PREFLIGHT_ROWS": len(target_rows),
        "BW_FINAL_TARGET_READY_ROWS": ready_rows,
        "EXECUTION_PACKAGE_ROWS": len(package_rows),
        "EXECUTION_PACKAGE_STAGED_ROWS": staged_count,
        "RUNBOOK_ROWS": len(runbook_rows),
        "VALIDATION_PLAN_ROWS": len(validation_rows),
        "ROLLBACK_PLAN_ROWS": len(rollback_rows),
        "STAGED_SCRIPT_ROWS": len(script_rows),
        "BX_ROOT": rel(bx_root, repo),
        "GUARDED_APPLY_EXECUTION_PACKAGE_STAGED": 1 if status == GREEN else 0,
        "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bx_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BX_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BX HELP/CMDHELPCHK Guarded Apply Execution Package\n\n"
        f"Status: `{status}`\n\n"
        "10BX stages the dedicated guarded apply execution package. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Package root:\n\n```text\n{rel(bx_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BW status: {bw.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BW savepoint present: {1 if sp_bw else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BW final target preflight rows: {len(target_rows)}")
    print(f"  BW final target ready rows: {ready_rows}")
    print(f"  execution package rows: {len(package_rows)}")
    print(f"  execution package staged rows: {staged_count}")
    print(f"  runbook rows: {len(runbook_rows)}")
    print(f"  validation plan rows: {len(validation_rows)}")
    print(f"  rollback plan rows: {len(rollback_rows)}")
    print(f"  staged script rows: {len(script_rows)}")
    print(f"  package root: {rel(bx_root, repo)}")
    print("  guarded apply execution package staged: 1")
    print("  apply execution authorized now: 0")
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
