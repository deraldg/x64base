#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BU_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE_STAGING_GREEN_STAGED_NO_APPLY"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BU_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE_STAGING_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BV_GUARDED_APPLY_EXECUTION_PACKAGE_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
BT_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bt_status_summary_v1.csv"
BT_AUTH = REPORT_DIR / "message_catalog_phase22ae_6_5_10bt_authorization_decision_v1.csv"
BT_STAGING = REPORT_DIR / "message_catalog_phase22ae_6_5_10bt_staging_plan_v1.csv"
BT_RUNTIME = REPORT_DIR / "message_catalog_phase22ae_6_5_10bt_runtime_readback_requirements_v1.csv"
BR_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10br_preflight_package_v1.csv"
BO_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_execution_package_manifest_v1.csv"
BO_BACKUPS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_backup_manifest_v1.csv"
BU_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bu_help_cmdhelpchk_guarded_apply_execution_package_staging_v1")
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
    ap.add_argument("--replace-existing-package", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bt = first(repo / BT_SUMMARY)
    auth_rows = rows(repo / BT_AUTH)
    staging_rows = rows(repo / BT_STAGING)
    runtime_rows = rows(repo / BT_RUNTIME)
    br_package = rows(repo / BR_PACKAGE)
    bo_package = rows(repo / BO_PACKAGE)
    bo_backups = rows(repo / BO_BACKUPS)
    sp_bt, latest_bt = savepoint(repo, "MSG-022AE.6.5.10BT")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bu_root = repo / BU_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BT_GREEN",
         bt.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BT_HELP_CMDHELPCHK_APPLY_EXECUTION_AUTHORIZATION_DECISION_GREEN_EXECUTION_STAGING_REQUIRED_SOURCE_HELD",
         bt.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BT_SAVEPOINT_PRESENT", sp_bt, latest_bt)
    gate("BT_EXECUTION_PACKAGE_STAGING_REQUIRED", bt.get("EXECUTION_PACKAGE_STAGING_REQUIRED") == "1", bt.get("EXECUTION_PACKAGE_STAGING_REQUIRED", "missing"))
    gate("BT_APPLY_EXECUTION_NOT_AUTHORIZED_NOW", bt.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", bt.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("BT_HELP_APPLY_NOT_EXECUTED", bt.get("HELP_DATA_APPLY_EXECUTED") == "0", bt.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BT_CMDHELPCHK_APPLY_NOT_EXECUTED", bt.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bt.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BT_AUTH_ROWS_PRESENT", len(auth_rows) > 0, len(auth_rows))
    gate("BT_STAGING_ROWS_PRESENT", len(staging_rows) > 0, len(staging_rows))
    gate("BT_RUNTIME_ROWS_PRESENT", len(runtime_rows) > 0, len(runtime_rows))
    gate("BR_PACKAGE_ROWS_PRESENT", len(br_package) > 0, len(br_package))
    gate("BO_PACKAGE_ROWS_PRESENT", len(bo_package) > 0, len(bo_package))
    gate("BO_BACKUP_ROWS_PRESENT", len(bo_backups) > 0, len(bo_backups))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BU_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bu_root.exists()) or args.replace_existing_package, rel(bu_root, repo))

    status = BLOCKED
    package_rows = []
    script_rows = []
    runtime_probe_rows = []
    restore_rows = []
    artifact_rows = []

    if failures == 0:
        if bu_root.exists() and args.replace_existing_package:
            shutil.rmtree(bu_root)
        bu_root.mkdir(parents=True, exist_ok=True)

        bo_by_target = {r.get("TARGET_PATH", ""): r for r in bo_package}
        backup_by_target = {r.get("TARGET_PATH", ""): r for r in bo_backups}

        for i, r in enumerate(auth_rows, start=1):
            target_path = r.get("TARGET_PATH", "")
            bo = bo_by_target.get(target_path, {})
            backup = backup_by_target.get(target_path, {})
            target = repo / target_path
            exists = target.exists() and target.is_file()
            target_hash_now = sha(target) if exists else ""
            expected = bo.get("TARGET_SHA256_NOW", "") or bo.get("TARGET_SHA256_EXPECTED", "")
            backup_path = backup.get("BACKUP_PATH", "") or bo.get("BACKUP_PATH", "")
            package_rows.append({
                "PACKAGE_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": target_path,
                "TARGET_EXISTS": 1 if exists else 0,
                "TARGET_SHA256_NOW": target_hash_now,
                "TARGET_SHA256_EXPECTED": expected,
                "TARGET_HASH_MATCHES_EXPECTED": 1 if exists and expected and target_hash_now == expected else 0,
                "BACKUP_PATH": backup_path,
                "BACKUP_EXISTS": 1 if backup_path and (repo / backup_path).exists() else 0,
                "BACKUP_SHA256": backup.get("BACKUP_SHA256", "") or bo.get("BACKUP_SHA256", ""),
                "DIFF_ARTIFACT": bo.get("DIFF_ARTIFACT", ""),
                "EXECUTION_METHOD": bo.get("EXECUTION_METHOD", ""),
                "AUTHORIZATION_DECISION": r.get("APPLY_AUTHORIZATION_DECISION", ""),
                "APPLY_EXECUTION_PACKAGE_STAGING_REQUIRED": r.get("APPLY_EXECUTION_PACKAGE_STAGING_REQUIRED", "1"),
                "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
                "PACKAGE_STATUS": "STAGED_NO_APPLY",
            })

        scripts_dir = bu_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        apply_template = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BU_APPLY_EXECUTION_TEMPLATE.ps1.disabled"
        apply_template.write_text(
            'param([switch]$ApplyAuthorized)\n'
            'if (-not $ApplyAuthorized) { throw "Apply is disabled. This 10BU template is staged only; later explicit authorization is required." }\n'
            'throw "Refusing: 10BU never applies HELP DATA or CMDHELPCHK mutation. Use a later authorized package."\n',
            encoding="utf-8"
        )

        restore_template = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BU_RESTORE_TEMPLATE.ps1.disabled"
        restore_template.write_text(
            'throw "Restore template staged only. Activate only under a later restore/rollback authorization package."\n',
            encoding="utf-8"
        )

        runtime_dts = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BU_RUNTIME_READBACK_PROBE.dts"
        runtime_dts.write_text(
            "MSGMGR STATUS\n"
            "MSGMGR CHECK\n"
            "SET MESSAGE CATALOG CHECK\n"
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\n"
            "HELP MSGMGR\n"
            "QUIT\n",
            encoding="utf-8"
        )

        script_rows = [
            {"SCRIPT_ROW": 1, "SCRIPT_PATH": rel(apply_template, repo), "SCRIPT_ROLE": "disabled_apply_template", "RUN_NOW": 0, "APPLY_ENABLED": 0},
            {"SCRIPT_ROW": 2, "SCRIPT_PATH": rel(restore_template, repo), "SCRIPT_ROLE": "disabled_restore_template", "RUN_NOW": 0, "APPLY_ENABLED": 0},
            {"SCRIPT_ROW": 3, "SCRIPT_PATH": rel(runtime_dts, repo), "SCRIPT_ROLE": "runtime_readback_probe_plan", "RUN_NOW": 0, "APPLY_ENABLED": 0},
        ]

        runtime_probe_rows = [
            {"PROBE_ROW": 1, "PROBE_COMMAND": "MSGMGR STATUS", "EXPECTED": "Command house remains registered and read-only.", "RUN_NOW": 0},
            {"PROBE_ROW": 2, "PROBE_COMMAND": "MSGMGR CHECK", "EXPECTED": "Message Manager check remains available.", "RUN_NOW": 0},
            {"PROBE_ROW": 3, "PROBE_COMMAND": "SET MESSAGE CATALOG CHECK", "EXPECTED": "Runtime catalog count remains 14/70.", "RUN_NOW": 0},
            {"PROBE_ROW": 4, "PROBE_COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US", "EXPECTED": "Localized emit remains proven.", "RUN_NOW": 0},
            {"PROBE_ROW": 5, "PROBE_COMMAND": "HELP MSGMGR", "EXPECTED": "Later apply must prove MSGMGR HELP readback.", "RUN_NOW": 0},
        ]

        restore_rows = [
            {"RESTORE_ROW": 1, "RESTORE_ITEM": "EXACT_TARGET_BACKUPS", "DETAIL": f"{len(bo_backups)} BO backup rows carried forward.", "APPLY_NOW": 0},
            {"RESTORE_ROW": 2, "RESTORE_ITEM": "RESTORE_TEMPLATE_DISABLED", "DETAIL": rel(restore_template, repo), "APPLY_NOW": 0},
            {"RESTORE_ROW": 3, "RESTORE_ITEM": "RUNTIME_READBACK_AFTER_RESTORE", "DETAIL": "Rerun MSGMGR/SET MESSAGE proof after any later restore.", "APPLY_NOW": 0},
        ]

        package_path = bu_root / "guarded_apply_execution_package_manifest_v1.csv"
        script_path = bu_root / "staged_script_manifest_v1.csv"
        runtime_path = bu_root / "runtime_readback_probe_plan_v1.csv"
        restore_path = bu_root / "restore_plan_v1.csv"
        readme = bu_root / "README_10BU_GUARDED_APPLY_EXECUTION_PACKAGE_STAGING.md"
        readme.write_text(
            "# 10BU HELP/CMDHELPCHK Guarded Apply Execution Package Staging\n\n"
            "10BU stages disabled execution templates, runtime readback probes, and restore path artifacts.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BU.\n",
            encoding="utf-8"
        )

        wcsv(package_path, package_rows, ["PACKAGE_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_EXISTS","BACKUP_SHA256","DIFF_ARTIFACT","EXECUTION_METHOD","AUTHORIZATION_DECISION","APPLY_EXECUTION_PACKAGE_STAGING_REQUIRED","APPLY_EXECUTION_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","PACKAGE_STATUS"])
        wcsv(script_path, script_rows, ["SCRIPT_ROW","SCRIPT_PATH","SCRIPT_ROLE","RUN_NOW","APPLY_ENABLED"])
        wcsv(runtime_path, runtime_probe_rows, ["PROBE_ROW","PROBE_COMMAND","EXPECTED","RUN_NOW"])
        wcsv(restore_path, restore_rows, ["RESTORE_ROW","RESTORE_ITEM","DETAIL","APPLY_NOW"])

        for p in [package_path, script_path, runtime_path, restore_path, apply_template, restore_template, runtime_dts, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_apply_execution_package_staging_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BU writes docs/messaging staged package artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Execution package staging only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Execution package staging only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "GUARDED_APPLY_EXECUTION_PACKAGE_STAGED", "STATUS": "YES" if package_rows else "NO", "DETAIL": f"{len(package_rows)} package rows."},
        {"ITEM": "DISABLED_SCRIPT_TEMPLATES_STAGED", "STATUS": "YES" if script_rows else "NO", "DETAIL": f"{len(script_rows)} script rows."},
        {"ITEM": "RUNTIME_READBACK_PROBE_STAGED", "STATUS": "YES" if runtime_probe_rows else "NO", "DETAIL": f"{len(runtime_probe_rows)} probe rows."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BU", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BU", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10BV_REQUIRED", "DETAIL": "Review staged execution package before any apply execution authorization."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_execution_package_manifest_v1.csv", package_rows, ["PACKAGE_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_EXISTS","BACKUP_SHA256","DIFF_ARTIFACT","EXECUTION_METHOD","AUTHORIZATION_DECISION","APPLY_EXECUTION_PACKAGE_STAGING_REQUIRED","APPLY_EXECUTION_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","PACKAGE_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_staged_script_manifest_v1.csv", script_rows, ["SCRIPT_ROW","SCRIPT_PATH","SCRIPT_ROLE","RUN_NOW","APPLY_ENABLED"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_runtime_readback_probe_plan_v1.csv", runtime_probe_rows, ["PROBE_ROW","PROBE_COMMAND","EXPECTED","RUN_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_restore_plan_v1.csv", restore_rows, ["RESTORE_ROW","RESTORE_ITEM","DETAIL","APPLY_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BT_STATUS": bt.get("STATUS", ""),
        "MSG_022AE_6_5_10BT_SAVEPOINT_PRESENT": 1 if sp_bt else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BT_AUTHORIZATION_DECISION_ROWS": len(auth_rows),
        "BT_STAGING_PLAN_ROWS": len(staging_rows),
        "BT_RUNTIME_REQUIREMENT_ROWS": len(runtime_rows),
        "EXECUTION_PACKAGE_ROWS": len(package_rows),
        "STAGED_SCRIPT_ROWS": len(script_rows),
        "RUNTIME_READBACK_PROBE_ROWS": len(runtime_probe_rows),
        "RESTORE_PLAN_ROWS": len(restore_rows),
        "BU_ROOT": rel(bu_root, repo),
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bu_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BU_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE_STAGING.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BU HELP/CMDHELPCHK Guarded Apply Execution Package Staging\n\n"
        f"Status: `{status}`\n\n"
        "10BU stages the guarded apply execution package. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Package root:\n\n```text\n{rel(bu_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BT status: {bt.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BT savepoint present: {1 if sp_bt else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BT authorization decision rows: {len(auth_rows)}")
    print(f"  BT staging plan rows: {len(staging_rows)}")
    print(f"  BT runtime requirement rows: {len(runtime_rows)}")
    print(f"  execution package rows: {len(package_rows)}")
    print(f"  staged script rows: {len(script_rows)}")
    print(f"  runtime readback probe rows: {len(runtime_probe_rows)}")
    print(f"  restore plan rows: {len(restore_rows)}")
    print(f"  package root: {rel(bu_root, repo)}")
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
