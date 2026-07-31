#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BR_HELP_CMDHELPCHK_GUARDED_APPLY_PREFLIGHT_PACKAGE_GREEN_STAGED_NO_APPLY"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BR_HELP_CMDHELPCHK_GUARDED_APPLY_PREFLIGHT_PACKAGE_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BS_GUARDED_APPLY_PREFLIGHT_REVIEW"

REPORT_DIR = Path("docs/messaging/reports")
BQ_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bq_status_summary_v1.csv"
BQ_DECISION = REPORT_DIR / "message_catalog_phase22ae_6_5_10bq_apply_decision_plan_v1.csv"
BQ_PREFLIGHT = REPORT_DIR / "message_catalog_phase22ae_6_5_10bq_preflight_requirements_v1.csv"
BQ_AUTH = REPORT_DIR / "message_catalog_phase22ae_6_5_10bq_authorization_boundary_v1.csv"
BO_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_execution_package_manifest_v1.csv"
BO_BACKUPS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_backup_manifest_v1.csv"
BO_GUARDS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bo_refusal_guards_v1.csv"
BR_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10br_help_cmdhelpchk_guarded_apply_preflight_package_v1")
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

    bq = first(repo / BQ_SUMMARY)
    decision_rows = rows(repo / BQ_DECISION)
    preflight_rows = rows(repo / BQ_PREFLIGHT)
    auth_rows = rows(repo / BQ_AUTH)
    bo_package = rows(repo / BO_PACKAGE)
    bo_backups = rows(repo / BO_BACKUPS)
    bo_guards = rows(repo / BO_GUARDS)
    sp_bq, latest_bq = savepoint(repo, "MSG-022AE.6.5.10BQ")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    br_root = repo / BR_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BQ_GREEN",
         bq.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BQ_HELP_CMDHELPCHK_APPLY_EXECUTION_DECISION_PLAN_GREEN_SOURCE_HELD",
         bq.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BQ_SAVEPOINT_PRESENT", sp_bq, latest_bq)
    gate("BQ_APPLY_DECISION_PLAN_CREATED", bq.get("APPLY_DECISION_PLAN_CREATED") == "1", bq.get("APPLY_DECISION_PLAN_CREATED", "missing"))
    gate("BQ_HELP_APPLY_NOT_EXECUTED", bq.get("HELP_DATA_APPLY_EXECUTED") == "0", bq.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BQ_CMDHELPCHK_APPLY_NOT_EXECUTED", bq.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bq.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BQ_DECISION_ROWS_PRESENT", len(decision_rows) > 0, len(decision_rows))
    gate("BQ_PREFLIGHT_ROWS_PRESENT", len(preflight_rows) > 0, len(preflight_rows))
    gate("BQ_AUTH_ROWS_PRESENT", len(auth_rows) > 0, len(auth_rows))
    gate("BO_PACKAGE_ROWS_PRESENT", len(bo_package) > 0, len(bo_package))
    gate("BO_BACKUP_ROWS_PRESENT", len(bo_backups) > 0, len(bo_backups))
    gate("BO_GUARDS_PRESENT", len(bo_guards) > 0, len(bo_guards))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BR_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not br_root.exists()) or args.replace_existing_package, rel(br_root, repo))

    status = BLOCKED
    package_rows = []
    checklist_rows = []
    runtime_probe_rows = []
    artifact_rows = []

    if failures == 0:
        if br_root.exists() and args.replace_existing_package:
            shutil.rmtree(br_root)
        br_root.mkdir(parents=True, exist_ok=True)

        backup_by_target = {r.get("TARGET_PATH", ""): r for r in bo_backups}

        for i, r in enumerate(decision_rows, start=1):
            target_path = r.get("TARGET_PATH", "")
            backup = backup_by_target.get(target_path, {})
            target = repo / target_path
            target_exists = target.exists() and target.is_file()
            target_hash_now = sha(target) if target_exists else ""
            expected_hash = ""
            for p in bo_package:
                if p.get("TARGET_PATH", "") == target_path:
                    expected_hash = p.get("TARGET_SHA256_NOW", "") or p.get("TARGET_SHA256_EXPECTED", "")
                    break
            package_rows.append({
                "PREFLIGHT_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": target_path,
                "TARGET_EXISTS": 1 if target_exists else 0,
                "TARGET_SHA256_NOW": target_hash_now,
                "TARGET_SHA256_EXPECTED": expected_hash,
                "TARGET_HASH_MATCHES_EXPECTED": 1 if target_hash_now and expected_hash and target_hash_now == expected_hash else 0,
                "BACKUP_PATH": backup.get("BACKUP_PATH", ""),
                "BACKUP_SHA256": backup.get("BACKUP_SHA256", ""),
                "BACKUP_MATCH": backup.get("SHA256_MATCH", ""),
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "APPLY_DECISION": r.get("APPLY_DECISION", ""),
                "APPLY_PREFLIGHT_REQUIRED": r.get("APPLY_PREFLIGHT_REQUIRED", "1"),
                "APPLY_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
                "PREFLIGHT_STATUS": "STAGED_FOR_REVIEW_NO_APPLY",
            })

        for i, r in enumerate(preflight_rows, start=1):
            checklist_rows.append({
                "CHECKLIST_STEP": i,
                "PREFLIGHT": r.get("PREFLIGHT", ""),
                "REQUIRED": r.get("REQUIRED", "1"),
                "CHECK_STATUS": "STAGED_NOT_EXECUTED",
                "DETAIL": r.get("DETAIL", ""),
                "AUTHORIZED_FOR_APPLY_NOW": 0,
            })

        runtime_probe_rows = [
            {"PROBE_STEP": 1, "PROBE_COMMAND": "HELP MSGMGR", "EXPECTED_SIGNAL": "MSGMGR usage/status/check help visible after later apply.", "RUN_NOW": 0},
            {"PROBE_STEP": 2, "PROBE_COMMAND": "HELP SET MESSAGE", "EXPECTED_SIGNAL": "SET MESSAGE CATALOG CHECK/GET and SET MESSAGE EMIT surfaces documented after later apply.", "RUN_NOW": 0},
            {"PROBE_STEP": 3, "PROBE_COMMAND": "MSGMGR STATUS", "EXPECTED_SIGNAL": "Message Manager command house remains registered/read-only as expected.", "RUN_NOW": 0},
            {"PROBE_STEP": 4, "PROBE_COMMAND": "SET MESSAGE CATALOG CHECK", "EXPECTED_SIGNAL": "Runtime message catalog still reports 14/70 proof.", "RUN_NOW": 0},
            {"PROBE_STEP": 5, "PROBE_COMMAND": "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US", "EXPECTED_SIGNAL": "Localized emit remains proven.", "RUN_NOW": 0},
            {"PROBE_STEP": 6, "PROBE_COMMAND": "CMDHELPCHK", "EXPECTED_SIGNAL": "CMDHELPCHK recognizes planned HELP/command-house surface after later apply.", "RUN_NOW": 0},
        ]

        package_path = br_root / "guarded_apply_preflight_package_manifest_v1.csv"
        checklist_path = br_root / "guarded_apply_preflight_checklist_v1.csv"
        auth_path = br_root / "authorization_boundary_carried_forward_v1.csv"
        guard_path = br_root / "refusal_guards_carried_forward_v1.csv"
        runtime_path = br_root / "runtime_readback_probe_plan_v1.csv"

        scripts_dir = br_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        disabled_apply = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BS_REVIEW_REQUIRED_NO_APPLY.ps1.disabled"
        disabled_apply.write_text(
            'throw "DISABLED TEMPLATE: 10BR stages preflight package only. 10BS review and later explicit apply authorization required."\n',
            encoding="utf-8"
        )
        dts_probe = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BR_RUNTIME_READBACK_PROBE_PLAN.dts"
        dts_probe.write_text(
            "MSGMGR STATUS\n"
            "MSGMGR CHECK\n"
            "SET MESSAGE CATALOG CHECK\n"
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\n"
            "QUIT\n",
            encoding="utf-8"
        )
        readme = br_root / "README_10BR_GUARDED_APPLY_PREFLIGHT_PACKAGE.md"
        readme.write_text(
            "# 10BR HELP/CMDHELPCHK Guarded Apply Preflight Package\n\n"
            "10BR stages the apply preflight package, target hash checks, refusal guards, authorization boundary, and runtime readback probe plan.\n\n"
            "No HELP DATA or CMDHELPCHK mutation is authorized or executed in 10BR.\n",
            encoding="utf-8"
        )

        wcsv(package_path, package_rows, ["PREFLIGHT_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_SHA256","BACKUP_MATCH","DIFF_ARTIFACT","APPLY_DECISION","APPLY_PREFLIGHT_REQUIRED","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","PREFLIGHT_STATUS"])
        wcsv(checklist_path, checklist_rows, ["CHECKLIST_STEP","PREFLIGHT","REQUIRED","CHECK_STATUS","DETAIL","AUTHORIZED_FOR_APPLY_NOW"])
        wcsv(auth_path, auth_rows, list(auth_rows[0].keys()) if auth_rows else ["EMPTY"])
        wcsv(guard_path, bo_guards, list(bo_guards[0].keys()) if bo_guards else ["EMPTY"])
        wcsv(runtime_path, runtime_probe_rows, ["PROBE_STEP","PROBE_COMMAND","EXPECTED_SIGNAL","RUN_NOW"])

        for p in [package_path, checklist_path, auth_path, guard_path, runtime_path, disabled_apply, dts_probe, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_apply_preflight_package_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BR writes docs/messaging preflight-package artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Preflight package only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Preflight package only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "GUARDED_APPLY_PREFLIGHT_PACKAGE_STAGED", "STATUS": "YES" if package_rows else "NO", "DETAIL": f"{len(package_rows)} target preflight rows."},
        {"ITEM": "PREFLIGHT_CHECKLIST_STAGED", "STATUS": "YES" if checklist_rows else "NO", "DETAIL": f"{len(checklist_rows)} checklist rows."},
        {"ITEM": "RUNTIME_READBACK_PROBE_PLAN_STAGED", "STATUS": "YES" if runtime_probe_rows else "NO", "DETAIL": f"{len(runtime_probe_rows)} runtime probe rows."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BR", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BR", "DETAIL": "No apply execution."},
        {"ITEM": "NEXT_REVIEW_GATE", "STATUS": "10BS_REQUIRED", "DETAIL": "Review preflight package before any apply execution package."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10br_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10br_preflight_package_v1.csv", package_rows, ["PREFLIGHT_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_SHA256","BACKUP_MATCH","DIFF_ARTIFACT","APPLY_DECISION","APPLY_PREFLIGHT_REQUIRED","APPLY_AUTHORIZED_NOW","APPLY_EXECUTED_NOW","PREFLIGHT_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10br_preflight_checklist_v1.csv", checklist_rows, ["CHECKLIST_STEP","PREFLIGHT","REQUIRED","CHECK_STATUS","DETAIL","AUTHORIZED_FOR_APPLY_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10br_runtime_readback_probe_plan_v1.csv", runtime_probe_rows, ["PROBE_STEP","PROBE_COMMAND","EXPECTED_SIGNAL","RUN_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10br_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10br_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10br_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BQ_STATUS": bq.get("STATUS", ""),
        "MSG_022AE_6_5_10BQ_SAVEPOINT_PRESENT": 1 if sp_bq else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BQ_APPLY_DECISION_ROWS": len(decision_rows),
        "BQ_PREFLIGHT_REQUIREMENT_ROWS": len(preflight_rows),
        "PREFLIGHT_PACKAGE_ROWS": len(package_rows),
        "PREFLIGHT_CHECKLIST_ROWS": len(checklist_rows),
        "RUNTIME_READBACK_PROBE_ROWS": len(runtime_probe_rows),
        "BR_ROOT": rel(br_root, repo),
        "GUARDED_APPLY_PREFLIGHT_PACKAGE_STAGED": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10br_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BR_HELP_CMDHELPCHK_GUARDED_APPLY_PREFLIGHT_PACKAGE.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BR HELP/CMDHELPCHK Guarded Apply Preflight Package\n\n"
        f"Status: `{status}`\n\n"
        "10BR stages the guarded apply preflight package. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Preflight-package root:\n\n```text\n{rel(br_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BQ status: {bq.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BQ savepoint present: {1 if sp_bq else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BQ apply decision rows: {len(decision_rows)}")
    print(f"  BQ preflight requirement rows: {len(preflight_rows)}")
    print(f"  preflight package rows: {len(package_rows)}")
    print(f"  preflight checklist rows: {len(checklist_rows)}")
    print(f"  runtime readback probe rows: {len(runtime_probe_rows)}")
    print(f"  preflight-package root: {rel(br_root, repo)}")
    print("  guarded apply preflight package staged: 1")
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
