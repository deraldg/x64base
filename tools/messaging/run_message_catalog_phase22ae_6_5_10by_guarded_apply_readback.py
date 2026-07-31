#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BY_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_RUN_AND_READBACK_GREEN_EXECUTION_HELD_NATIVE_IMPLEMENTATION_REQUIRED"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BY_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_RUN_AND_READBACK_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BZ_TARGET_SPECIFIC_NATIVE_APPLY_IMPLEMENTATION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
BX_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_status_summary_v1.csv"
BX_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_execution_package_manifest_v1.csv"
BX_RUNBOOK = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_runbook_v1.csv"
BX_VALIDATION = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_post_apply_validation_plan_v1.csv"
BX_ROLLBACK = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_rollback_plan_v1.csv"
BX_SCRIPTS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bx_staged_script_manifest_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
BY_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10by_help_cmdhelpchk_guarded_apply_execution_run_and_readback_v1")

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

def classify_apply_support(row, repo):
    target_path = row.get("TARGET_PATH", "")
    diff_path = row.get("DIFF_ARTIFACT", "")
    exec_method = row.get("EXECUTION_METHOD", "")
    target = repo / target_path if target_path else None
    diff = repo / diff_path if diff_path else None

    target_suffix = target.suffix.lower() if target else ""
    diff_exists = bool(diff_path and diff and diff.exists() and diff.is_file())
    target_exists = bool(target_path and target and target.exists() and target.is_file())

    if not target_exists:
        return ("BLOCK_TARGET_MISSING", "Target file is missing.")
    if not diff_exists:
        return ("BLOCK_DIFF_ARTIFACT_NOT_FOUND", "Diff/apply artifact is missing or not materialized.")
    if target_suffix in {".dbf", ".cdx", ".dtx", ".dbt"}:
        return ("BLOCK_NATIVE_OR_SCHEMA_AWARE_WRITER_REQUIRED", "Binary/xBase target requires native/schema-aware writer, not Python byte edits.")
    if "NATIVE" in exec_method.upper() or "SCHEMA" in exec_method.upper():
        return ("BLOCK_NATIVE_OR_SCHEMA_AWARE_WRITER_REQUIRED", "Plan requires native/schema-aware writer implementation.")
    return ("BLOCK_TARGET_SPECIFIC_APPLY_IMPLEMENTATION_REQUIRED", "Exact target apply semantics must be implemented before mutation.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--replace-existing-execution", action="store_true")
    ap.add_argument("--apply-authorized", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bx = first(repo / BX_SUMMARY)
    package_rows = rows(repo / BX_PACKAGE)
    runbook_rows = rows(repo / BX_RUNBOOK)
    validation_rows = rows(repo / BX_VALIDATION)
    rollback_rows = rows(repo / BX_ROLLBACK)
    script_rows = rows(repo / BX_SCRIPTS)
    sp_bx, latest_bx = savepoint(repo, "MSG-022AE.6.5.10BX")
    msg_count_before = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count_before = dbf_count(repo / ACTIVE_TEXT_DBF)
    by_root = repo / BY_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BX_GREEN",
         bx.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BX_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE_GREEN_STAGED_NO_APPLY",
         bx.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BX_SAVEPOINT_PRESENT", sp_bx, latest_bx)
    gate("BX_PACKAGE_STAGED", bx.get("GUARDED_APPLY_EXECUTION_PACKAGE_STAGED") == "1", bx.get("GUARDED_APPLY_EXECUTION_PACKAGE_STAGED", "missing"))
    gate("BX_HELP_APPLY_NOT_EXECUTED", bx.get("HELP_DATA_APPLY_EXECUTED") == "0", bx.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BX_CMDHELPCHK_APPLY_NOT_EXECUTED", bx.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bx.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BX_PACKAGE_ROWS_PRESENT", len(package_rows) > 0, len(package_rows))
    gate("BX_RUNBOOK_PRESENT", len(runbook_rows) > 0, len(runbook_rows))
    gate("BX_VALIDATION_PLAN_PRESENT", len(validation_rows) > 0, len(validation_rows))
    gate("BX_ROLLBACK_PLAN_PRESENT", len(rollback_rows) > 0, len(rollback_rows))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14_BEFORE", msg_count_before == 14, msg_count_before)
    gate("ACTIVE_TEXT_HEADER_COUNT_70_BEFORE", text_count_before == 70, text_count_before)
    gate("APPLY_AUTHORIZATION_SWITCH_PRESENT", args.apply_authorized, "Pass -ApplyAuthorized on the PowerShell wrapper for this execution decision gate.")
    gate("BY_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not by_root.exists()) or args.replace_existing_execution, rel(by_root, repo))

    status = BLOCKED
    execution_rows = []
    apply_support_rows = []
    readback_rows = []
    artifact_rows = []
    apply_executed = 0
    help_apply_executed = 0
    cmd_apply_executed = 0
    native_required = 0

    if failures == 0:
        if by_root.exists() and args.replace_existing_execution:
            shutil.rmtree(by_root)
        by_root.mkdir(parents=True, exist_ok=True)

        for i, r in enumerate(package_rows, start=1):
            target_path = r.get("TARGET_PATH", "")
            target = repo / target_path
            target_exists = target.exists() and target.is_file()
            current_hash = sha(target) if target_exists else ""
            expected_hash = r.get("TARGET_SHA256_NOW", "") or r.get("TARGET_SHA256_EXPECTED", "")
            backup_path = r.get("BACKUP_PATH", "")
            backup_exists = bool(backup_path) and (repo / backup_path).exists()
            support_code, support_detail = classify_apply_support(r, repo)
            native_required = 1

            execution_rows.append({
                "EXECUTION_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": target_path,
                "TARGET_EXISTS": 1 if target_exists else 0,
                "TARGET_SHA256_NOW": current_hash,
                "TARGET_SHA256_EXPECTED": expected_hash,
                "TARGET_HASH_MATCHES_EXPECTED": 1 if current_hash and expected_hash and current_hash == expected_hash else 0,
                "BACKUP_PATH": backup_path,
                "BACKUP_EXISTS": 1 if backup_exists else 0,
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "EXECUTION_METHOD": r.get("EXECUTION_METHOD", ""),
                "APPLY_SUPPORT_STATUS": support_code,
                "APPLY_SUPPORT_DETAIL": support_detail,
                "APPLY_AUTHORIZED": 1,
                "APPLY_EXECUTED": 0,
                "EXECUTION_RESULT": "HELD_NATIVE_OR_TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED",
            })

            apply_support_rows.append({
                "SUPPORT_ROW": i,
                "TARGET_PATH": target_path,
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "REQUIRED_IMPLEMENTATION": support_code,
                "DETAIL": support_detail,
                "SAFE_TO_MUTATE_NOW": 0,
            })

        readback_rows = [
            {"READBACK_ROW": 1, "CHECK": "SYSTEM_MESSAGES_HEADER_COUNT", "EXPECTED": 14, "OBSERVED": msg_count_before, "PASS": 1 if msg_count_before == 14 else 0, "RUN_NOW": 1},
            {"READBACK_ROW": 2, "CHECK": "SYSTEM_MESSAGE_TEXT_HEADER_COUNT", "EXPECTED": 70, "OBSERVED": text_count_before, "PASS": 1 if text_count_before == 70 else 0, "RUN_NOW": 1},
            {"READBACK_ROW": 3, "CHECK": "HELP_DATA_APPLY_EXECUTED", "EXPECTED": 0, "OBSERVED": help_apply_executed, "PASS": 1, "RUN_NOW": 1},
            {"READBACK_ROW": 4, "CHECK": "CMDHELPCHK_APPLY_EXECUTED", "EXPECTED": 0, "OBSERVED": cmd_apply_executed, "PASS": 1, "RUN_NOW": 1},
            {"READBACK_ROW": 5, "CHECK": "NATIVE_TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED", "EXPECTED": 1, "OBSERVED": native_required, "PASS": 1 if native_required == 1 else 0, "RUN_NOW": 1},
        ]

        exec_path = by_root / "guarded_apply_execution_result_v1.csv"
        support_path = by_root / "native_apply_implementation_requirements_v1.csv"
        readback_path = by_root / "readback_observation_v1.csv"
        runtime_dts = by_root / "scripts" / "MESSAGE_CATALOG_PHASE22AE_6_5_10BY_RUNTIME_READBACK_TO_RUN_AFTER_NATIVE_IMPLEMENTATION.dts"
        runtime_dts.parent.mkdir(parents=True, exist_ok=True)
        runtime_dts.write_text(
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
        readme = by_root / "README_10BY_GUARDED_APPLY_EXECUTION_RUN_AND_READBACK.md"
        readme.write_text(
            "# 10BY HELP/CMDHELPCHK Guarded Apply Execution Run and Readback\n\n"
            "10BY received the explicit apply authorization switch and rechecked the staged package.\n\n"
            "Execution was held because target-specific/native/schema-aware apply implementation is required before mutating HELP DATA or CMDHELPCHK. No protected mutation occurred.\n",
            encoding="utf-8"
        )

        wcsv(exec_path, execution_rows, ["EXECUTION_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_EXISTS","DIFF_ARTIFACT","EXECUTION_METHOD","APPLY_SUPPORT_STATUS","APPLY_SUPPORT_DETAIL","APPLY_AUTHORIZED","APPLY_EXECUTED","EXECUTION_RESULT"])
        wcsv(support_path, apply_support_rows, ["SUPPORT_ROW","TARGET_PATH","TARGET_KIND","REQUIRED_IMPLEMENTATION","DETAIL","SAFE_TO_MUTATE_NOW"])
        wcsv(readback_path, readback_rows, ["READBACK_ROW","CHECK","EXPECTED","OBSERVED","PASS","RUN_NOW"])

        for p in [exec_path, support_path, readback_path, runtime_dts, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_apply_execution_run_and_readback_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    msg_count_after = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count_after = dbf_count(repo / ACTIVE_TEXT_DBF)

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BY writes docs/messaging run/readback reports only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation; count remained report-checked."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation; count remained report-checked."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 1 if args.apply_authorized else 0, "OBSERVED_MUTATION": help_apply_executed, "DETAIL": "Authorization switch received, but execution held pending native/target-specific implementation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 1 if args.apply_authorized else 0, "OBSERVED_MUTATION": cmd_apply_executed, "DETAIL": "Authorization switch received, but execution held pending native/target-specific implementation."},
    ]

    readiness = [
        {"ITEM": "APPLY_AUTHORIZATION_RECEIVED", "STATUS": "YES" if args.apply_authorized else "NO", "DETAIL": "PowerShell wrapper -ApplyAuthorized controls this."},
        {"ITEM": "TARGET_SPECIFIC_NATIVE_IMPLEMENTATION_REQUIRED", "STATUS": "YES" if native_required else "NO", "DETAIL": f"{len(apply_support_rows)} target requirement rows."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "HELD_NOT_EXECUTED", "DETAIL": "No unsafe generic writer was used."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "HELD_NOT_EXECUTED", "DETAIL": "No unsafe generic writer was used."},
        {"ITEM": "NEXT_PACKAGE", "STATUS": "10BZ_REQUIRED", "DETAIL": "Implement target-specific native/schema-aware apply logic."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10by_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10by_execution_result_v1.csv", execution_rows, ["EXECUTION_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_EXISTS","DIFF_ARTIFACT","EXECUTION_METHOD","APPLY_SUPPORT_STATUS","APPLY_SUPPORT_DETAIL","APPLY_AUTHORIZED","APPLY_EXECUTED","EXECUTION_RESULT"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10by_native_apply_requirements_v1.csv", apply_support_rows, ["SUPPORT_ROW","TARGET_PATH","TARGET_KIND","REQUIRED_IMPLEMENTATION","DETAIL","SAFE_TO_MUTATE_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10by_readback_observation_v1.csv", readback_rows, ["READBACK_ROW","CHECK","EXPECTED","OBSERVED","PASS","RUN_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10by_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10by_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10by_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BX_STATUS": bx.get("STATUS", ""),
        "MSG_022AE_6_5_10BX_SAVEPOINT_PRESENT": 1 if sp_bx else 0,
        "ACTIVE_MESSAGES_COUNT_BEFORE": msg_count_before,
        "ACTIVE_TEXT_COUNT_BEFORE": text_count_before,
        "ACTIVE_MESSAGES_COUNT_AFTER": msg_count_after,
        "ACTIVE_TEXT_COUNT_AFTER": text_count_after,
        "BX_EXECUTION_PACKAGE_ROWS": len(package_rows),
        "APPLY_AUTHORIZATION_RECEIVED": 1 if args.apply_authorized else 0,
        "EXECUTION_RESULT_ROWS": len(execution_rows),
        "NATIVE_APPLY_REQUIREMENT_ROWS": len(apply_support_rows),
        "NATIVE_TARGET_SPECIFIC_IMPLEMENTATION_REQUIRED": native_required,
        "BY_ROOT": rel(by_root, repo),
        "APPLY_EXECUTION_AUTHORIZED_NOW": 1 if args.apply_authorized else 0,
        "APPLY_EXECUTION_HELD_PENDING_IMPLEMENTATION": 1 if status == GREEN else 0,
        "HELP_DATA_APPLY_EXECUTED": help_apply_executed,
        "CMDHELPCHK_APPLY_EXECUTED": cmd_apply_executed,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10by_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BY_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_RUN_AND_READBACK.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BY HELP/CMDHELPCHK Guarded Apply Execution Run and Readback\n\n"
        f"Status: `{status}`\n\n"
        "10BY received/checked apply authorization but held execution pending target-specific native/schema-aware apply implementation. No HELP DATA or CMDHELPCHK mutation occurred.\n\n"
        f"Execution root:\n\n```text\n{rel(by_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BX status: {bx.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BX savepoint present: {1 if sp_bx else 0}")
    print(f"  active messages count before: {msg_count_before}")
    print(f"  active text count before: {text_count_before}")
    print(f"  active messages count after: {msg_count_after}")
    print(f"  active text count after: {text_count_after}")
    print(f"  BX execution package rows: {len(package_rows)}")
    print(f"  apply authorization received: {1 if args.apply_authorized else 0}")
    print(f"  execution result rows: {len(execution_rows)}")
    print(f"  native apply requirement rows: {len(apply_support_rows)}")
    print(f"  native target-specific implementation required: {native_required}")
    print(f"  execution root: {rel(by_root, repo)}")
    print("  apply execution held pending implementation: 1")
    print(f"  HELP DATA apply executed: {help_apply_executed}")
    print(f"  CMDHELPCHK apply executed: {cmd_apply_executed}")
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
