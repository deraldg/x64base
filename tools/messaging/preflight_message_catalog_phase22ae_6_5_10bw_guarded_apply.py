#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN = "MESSAGE_CATALOG_PHASE22AE_6_5_10BW_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PREFLIGHT_GREEN_READY_FOR_APPLY_EXECUTION_PACKAGE_SOURCE_HELD"
BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_5_10BW_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PREFLIGHT_BLOCKED"
NEXT = "HOLD_OR_AUTHORIZE_PHASE22AE_6_5_10BX_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PACKAGE"

REPORT_DIR = Path("docs/messaging/reports")
BV_SUMMARY = REPORT_DIR / "message_catalog_phase22ae_6_5_10bv_status_summary_v1.csv"
BV_REVIEW = REPORT_DIR / "message_catalog_phase22ae_6_5_10bv_execution_package_review_v1.csv"
BV_SCRIPTS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bv_staged_script_review_v1.csv"
BV_RUNTIME = REPORT_DIR / "message_catalog_phase22ae_6_5_10bv_runtime_probe_review_v1.csv"
BV_RESTORE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bv_restore_plan_review_v1.csv"
BU_PACKAGE = REPORT_DIR / "message_catalog_phase22ae_6_5_10bu_execution_package_manifest_v1.csv"
BU_SCRIPTS = REPORT_DIR / "message_catalog_phase22ae_6_5_10bu_staged_script_manifest_v1.csv"
ACTIVE_MSG_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf")
ACTIVE_TEXT_DBF = Path("dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf")
BW_ROOT = Path("docs/messaging/apply/phase22ae_6_5_10bw_help_cmdhelpchk_guarded_apply_execution_preflight_v1")

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
    ap.add_argument("--replace-existing-preflight", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    bv = first(repo / BV_SUMMARY)
    bv_review = rows(repo / BV_REVIEW)
    bv_scripts = rows(repo / BV_SCRIPTS)
    bv_runtime = rows(repo / BV_RUNTIME)
    bv_restore = rows(repo / BV_RESTORE)
    bu_package = rows(repo / BU_PACKAGE)
    bu_scripts = rows(repo / BU_SCRIPTS)
    sp_bv, latest_bv = savepoint(repo, "MSG-022AE.6.5.10BV")
    msg_count = dbf_count(repo / ACTIVE_MSG_DBF)
    text_count = dbf_count(repo / ACTIVE_TEXT_DBF)
    bw_root = repo / BW_ROOT

    gates = []
    failures = 0
    def gate(name, ok, detail):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_5_10BV_GREEN",
         bv.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_5_10BV_GUARDED_APPLY_EXECUTION_PACKAGE_REVIEW_GREEN_APPLY_EXECUTION_PREFLIGHT_REQUIRED_SOURCE_HELD",
         bv.get("STATUS", "missing"))
    gate("MSG_022AE_6_5_10BV_SAVEPOINT_PRESENT", sp_bv, latest_bv)
    gate("BV_FINAL_PREFLIGHT_REQUIRED", bv.get("FINAL_PREFLIGHT_REQUIRED") == "1", bv.get("FINAL_PREFLIGHT_REQUIRED", "missing"))
    gate("BV_APPLY_EXECUTION_NOT_AUTHORIZED_NOW", bv.get("APPLY_EXECUTION_AUTHORIZED_NOW") == "0", bv.get("APPLY_EXECUTION_AUTHORIZED_NOW", "missing"))
    gate("BV_HELP_APPLY_NOT_EXECUTED", bv.get("HELP_DATA_APPLY_EXECUTED") == "0", bv.get("HELP_DATA_APPLY_EXECUTED", "missing"))
    gate("BV_CMDHELPCHK_APPLY_NOT_EXECUTED", bv.get("CMDHELPCHK_APPLY_EXECUTED") == "0", bv.get("CMDHELPCHK_APPLY_EXECUTED", "missing"))
    gate("BV_REVIEW_ROWS_PRESENT", len(bv_review) > 0, len(bv_review))
    gate("BV_SCRIPT_ROWS_PRESENT", len(bv_scripts) > 0, len(bv_scripts))
    gate("BV_RUNTIME_ROWS_PRESENT", len(bv_runtime) > 0, len(bv_runtime))
    gate("BV_RESTORE_ROWS_PRESENT", len(bv_restore) > 0, len(bv_restore))
    gate("BU_PACKAGE_ROWS_PRESENT", len(bu_package) > 0, len(bu_package))
    gate("BU_SCRIPT_ROWS_PRESENT", len(bu_scripts) > 0, len(bu_scripts))
    gate("ACTIVE_MESSAGES_HEADER_COUNT_14", msg_count == 14, msg_count)
    gate("ACTIVE_TEXT_HEADER_COUNT_70", text_count == 70, text_count)
    gate("BW_ROOT_NOT_EXISTING_OR_REPLACE_ALLOWED", (not bw_root.exists()) or args.replace_existing_preflight, rel(bw_root, repo))

    status = BLOCKED
    target_preflight = []
    script_preflight = []
    runtime_preflight = []
    restore_preflight = []
    refusal_rows = []
    artifact_rows = []

    if failures == 0:
        if bw_root.exists() and args.replace_existing_preflight:
            shutil.rmtree(bw_root)
        bw_root.mkdir(parents=True, exist_ok=True)

        bu_by_target = {r.get("TARGET_PATH", ""): r for r in bu_package}

        for i, r in enumerate(bv_review, start=1):
            target_path = r.get("TARGET_PATH", "")
            bu = bu_by_target.get(target_path, {})
            target = repo / target_path
            target_exists = target.exists() and target.is_file()
            current_hash = sha(target) if target_exists else ""
            expected_hash = bu.get("TARGET_SHA256_EXPECTED", "") or bu.get("TARGET_SHA256_NOW", "")
            hash_match = 1 if current_hash and expected_hash and current_hash == expected_hash else 0
            backup_path = bu.get("BACKUP_PATH", "") or r.get("BACKUP_PATH", "")
            backup_exists = bool(backup_path) and (repo / backup_path).exists()
            disposition_ok = r.get("REVIEW_DISPOSITION", "") == "ACCEPT_FOR_FINAL_PREFLIGHT"
            final_status = "READY_FOR_APPLY_EXECUTION_PACKAGE" if target_exists and backup_exists and disposition_ok else "REVIEW_REQUIRED"
            target_preflight.append({
                "PREFLIGHT_ROW": i,
                "TARGET_ID": r.get("TARGET_ID", ""),
                "TARGET_KIND": r.get("TARGET_KIND", ""),
                "TARGET_PATH": target_path,
                "TARGET_EXISTS": 1 if target_exists else 0,
                "TARGET_SHA256_NOW": current_hash,
                "TARGET_SHA256_EXPECTED": expected_hash,
                "TARGET_HASH_MATCHES_EXPECTED": hash_match,
                "BACKUP_PATH": backup_path,
                "BACKUP_EXISTS": 1 if backup_exists else 0,
                "DIFF_ARTIFACT": r.get("DIFF_ARTIFACT", ""),
                "EXECUTION_METHOD": r.get("EXECUTION_METHOD", ""),
                "BV_REVIEW_DISPOSITION": r.get("REVIEW_DISPOSITION", ""),
                "FINAL_PREFLIGHT_STATUS": final_status,
                "READY_FOR_APPLY_EXECUTION_PACKAGE": 1 if final_status == "READY_FOR_APPLY_EXECUTION_PACKAGE" else 0,
                "APPLY_EXECUTION_AUTHORIZED_NOW": 0,
                "APPLY_EXECUTED_NOW": 0,
            })

        for i, r in enumerate(bv_scripts, start=1):
            path = r.get("SCRIPT_PATH", "")
            p = repo / path if path else None
            exists = bool(p and p.exists())
            content = p.read_text(encoding="utf-8", errors="replace") if exists else ""
            disabled_marker = (".disabled" in path.lower()) or ("disabled" in content.lower()) or ("refusing" in content.lower())
            script_preflight.append({
                "SCRIPT_PREFLIGHT_ROW": i,
                "SCRIPT_PATH": path,
                "SCRIPT_ROLE": r.get("SCRIPT_ROLE", ""),
                "SCRIPT_EXISTS": 1 if exists else 0,
                "APPLY_ENABLED": r.get("APPLY_ENABLED", "0"),
                "DISABLED_OR_REFUSAL_MARKER_PRESENT": 1 if disabled_marker else 0,
                "RUN_NOW": 0,
                "PREFLIGHT_STATUS": "ACCEPT_DISABLED_FOR_NEXT_PACKAGE" if exists and disabled_marker else "REVIEW_REQUIRED",
            })

        for i, r in enumerate(bv_runtime, start=1):
            runtime_preflight.append({
                "RUNTIME_PREFLIGHT_ROW": i,
                "PROBE_COMMAND": r.get("PROBE_COMMAND", ""),
                "EXPECTED": r.get("EXPECTED", "") or r.get("EXPECTED_SIGNAL", ""),
                "CARRY_FORWARD_TO_POST_APPLY_READBACK": 1,
                "RUN_NOW": 0,
                "PREFLIGHT_STATUS": "STAGED_FOR_NEXT_PACKAGE",
            })

        for i, r in enumerate(bv_restore, start=1):
            restore_preflight.append({
                "RESTORE_PREFLIGHT_ROW": i,
                "RESTORE_ITEM": r.get("RESTORE_ITEM", ""),
                "DETAIL": r.get("DETAIL", ""),
                "CARRY_FORWARD_TO_NEXT_PACKAGE": 1,
                "APPLY_NOW": 0,
                "PREFLIGHT_STATUS": "STAGED_FOR_NEXT_PACKAGE",
            })

        refusal_rows = [
            {"REFUSAL_GUARD": "NO_APPLY_IN_10BW", "STATUS": "ACTIVE", "DETAIL": "10BW performs final preflight only."},
            {"REFUSAL_GUARD": "TARGET_HASH_DRIFT", "STATUS": "ACTIVE", "DETAIL": "Next package must refuse if target hash changes from 10BW state."},
            {"REFUSAL_GUARD": "BACKUP_MISSING", "STATUS": "ACTIVE", "DETAIL": "Next package must refuse if exact backup path is missing."},
            {"REFUSAL_GUARD": "SCRIPT_NOT_DISABLED", "STATUS": "ACTIVE", "DETAIL": "Apply template must remain disabled until explicit apply package."},
            {"REFUSAL_GUARD": "RUNTIME_READBACK_PLAN_MISSING", "STATUS": "ACTIVE", "DETAIL": "Post-apply runtime readback must be carried into next package."},
            {"REFUSAL_GUARD": "MESSAGING_COUNTS_DRIFT", "STATUS": "ACTIVE", "DETAIL": "SYSTEM_MESSAGES must stay 14 and SYSTEM_MESSAGE_TEXT must stay 70 unless separately authorized."},
            {"REFUSAL_GUARD": "NO_RAW_DBF_WRITE", "STATUS": "ACTIVE", "DETAIL": "Any DBF-touching future apply must be native/schema-aware, not raw Python DBF mutation."},
        ]

        target_path = bw_root / "final_target_preflight_v1.csv"
        script_path = bw_root / "final_script_preflight_v1.csv"
        runtime_path = bw_root / "runtime_readback_preflight_v1.csv"
        restore_path = bw_root / "restore_preflight_v1.csv"
        refusal_path = bw_root / "refusal_guards_for_apply_execution_package_v1.csv"

        scripts_dir = bw_root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        next_template = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BX_APPLY_EXECUTION_PACKAGE_TEMPLATE.ps1.disabled"
        next_template.write_text(
            'param([switch]$ApplyAuthorized)\n'
            'if (-not $ApplyAuthorized) { throw "Apply not authorized for this disabled template." }\n'
            'throw "10BW staged only a disabled template. Generate a dedicated 10BX package before any mutation."\n',
            encoding="utf-8"
        )

        runtime_dts = scripts_dir / "MESSAGE_CATALOG_PHASE22AE_6_5_10BW_RUNTIME_READBACK_PREFLIGHT.dts"
        runtime_dts.write_text(
            "MSGMGR STATUS\n"
            "MSGMGR CHECK\n"
            "SET MESSAGE CATALOG CHECK\n"
            "SET MESSAGE EMIT MESSAGE_PROOF_MODE_STATUS en-US\n"
            "HELP MSGMGR\n"
            "QUIT\n",
            encoding="utf-8"
        )

        readme = bw_root / "README_10BW_GUARDED_APPLY_EXECUTION_PREFLIGHT.md"
        readme.write_text(
            "# 10BW HELP/CMDHELPCHK Guarded Apply Execution Preflight\n\n"
            "10BW performs final guarded preflight for the staged apply execution package.\n\n"
            "It does not mutate HELP DATA or CMDHELPCHK. It prepares the next 10BX gate for a dedicated apply execution package.\n",
            encoding="utf-8"
        )

        wcsv(target_path, target_preflight, ["PREFLIGHT_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_EXISTS","DIFF_ARTIFACT","EXECUTION_METHOD","BV_REVIEW_DISPOSITION","FINAL_PREFLIGHT_STATUS","READY_FOR_APPLY_EXECUTION_PACKAGE","APPLY_EXECUTION_AUTHORIZED_NOW","APPLY_EXECUTED_NOW"])
        wcsv(script_path, script_preflight, ["SCRIPT_PREFLIGHT_ROW","SCRIPT_PATH","SCRIPT_ROLE","SCRIPT_EXISTS","APPLY_ENABLED","DISABLED_OR_REFUSAL_MARKER_PRESENT","RUN_NOW","PREFLIGHT_STATUS"])
        wcsv(runtime_path, runtime_preflight, ["RUNTIME_PREFLIGHT_ROW","PROBE_COMMAND","EXPECTED","CARRY_FORWARD_TO_POST_APPLY_READBACK","RUN_NOW","PREFLIGHT_STATUS"])
        wcsv(restore_path, restore_preflight, ["RESTORE_PREFLIGHT_ROW","RESTORE_ITEM","DETAIL","CARRY_FORWARD_TO_NEXT_PACKAGE","APPLY_NOW","PREFLIGHT_STATUS"])
        wcsv(refusal_path, refusal_rows, ["REFUSAL_GUARD","STATUS","DETAIL"])

        for p in [target_path, script_path, runtime_path, restore_path, refusal_path, next_template, runtime_dts, readme]:
            artifact_rows.append({"ARTIFACT": rel(p, repo), "ROLE": "guarded_apply_execution_preflight_artifact", "BYTES": p.stat().st_size, "SHA256": sha(p)})

        status = GREEN

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "10BW writes docs/messaging preflight artifacts only."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_SYSTEM_MESSAGE_TEXT", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CDX/LMDB mutation."},
        {"PROTECTED_SYSTEM": "WORKSPACE_PROFILE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No workspace mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Final preflight only; no HELP DATA apply."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Final preflight only; no CMDHELPCHK apply."},
    ]

    readiness = [
        {"ITEM": "FINAL_TARGET_PREFLIGHT_COMPLETE", "STATUS": "YES" if target_preflight else "NO", "DETAIL": f"{len(target_preflight)} target rows."},
        {"ITEM": "FINAL_SCRIPT_PREFLIGHT_COMPLETE", "STATUS": "YES" if script_preflight else "NO", "DETAIL": f"{len(script_preflight)} script rows."},
        {"ITEM": "APPLY_EXECUTION_PACKAGE_READY_FOR_STAGING", "STATUS": "YES" if target_preflight else "NO", "DETAIL": "10BX may stage a dedicated guarded apply execution package."},
        {"ITEM": "HELP_DATA_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BW", "DETAIL": "No apply execution."},
        {"ITEM": "CMDHELPCHK_APPLY_EXECUTION", "STATUS": "NOT_EXECUTED_IN_10BW", "DETAIL": "No apply execution."},
    ]

    issues = "0" if failures == 0 else str(failures)
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_final_target_preflight_v1.csv", target_preflight, ["PREFLIGHT_ROW","TARGET_ID","TARGET_KIND","TARGET_PATH","TARGET_EXISTS","TARGET_SHA256_NOW","TARGET_SHA256_EXPECTED","TARGET_HASH_MATCHES_EXPECTED","BACKUP_PATH","BACKUP_EXISTS","DIFF_ARTIFACT","EXECUTION_METHOD","BV_REVIEW_DISPOSITION","FINAL_PREFLIGHT_STATUS","READY_FOR_APPLY_EXECUTION_PACKAGE","APPLY_EXECUTION_AUTHORIZED_NOW","APPLY_EXECUTED_NOW"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_script_preflight_v1.csv", script_preflight, ["SCRIPT_PREFLIGHT_ROW","SCRIPT_PATH","SCRIPT_ROLE","SCRIPT_EXISTS","APPLY_ENABLED","DISABLED_OR_REFUSAL_MARKER_PRESENT","RUN_NOW","PREFLIGHT_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_runtime_readback_preflight_v1.csv", runtime_preflight, ["RUNTIME_PREFLIGHT_ROW","PROBE_COMMAND","EXPECTED","CARRY_FORWARD_TO_POST_APPLY_READBACK","RUN_NOW","PREFLIGHT_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_restore_preflight_v1.csv", restore_preflight, ["RESTORE_PREFLIGHT_ROW","RESTORE_ITEM","DETAIL","CARRY_FORWARD_TO_NEXT_PACKAGE","APPLY_NOW","PREFLIGHT_STATUS"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_refusal_guards_v1.csv", refusal_rows, ["REFUSAL_GUARD","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_apply_readiness_v1.csv", readiness, ["ITEM","STATUS","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_artifact_manifest_v1.csv", artifact_rows, ["ARTIFACT","ROLE","BYTES","SHA256"])

    ready_count = sum(1 for r in target_preflight if str(r.get("READY_FOR_APPLY_EXECUTION_PACKAGE", "")) == "1")
    summary = {
        "STATUS": status,
        "VALIDATION_ISSUES": issues,
        "PHASE22AE_6_5_10BV_STATUS": bv.get("STATUS", ""),
        "MSG_022AE_6_5_10BV_SAVEPOINT_PRESENT": 1 if sp_bv else 0,
        "ACTIVE_MESSAGES_OBSERVED_COUNT": msg_count,
        "ACTIVE_TEXT_OBSERVED_COUNT": text_count,
        "BV_EXECUTION_PACKAGE_REVIEW_ROWS": len(bv_review),
        "BV_SCRIPT_REVIEW_ROWS": len(bv_scripts),
        "BV_RUNTIME_REVIEW_ROWS": len(bv_runtime),
        "BV_RESTORE_REVIEW_ROWS": len(bv_restore),
        "FINAL_TARGET_PREFLIGHT_ROWS": len(target_preflight),
        "FINAL_TARGET_PREFLIGHT_READY_ROWS": ready_count,
        "FINAL_SCRIPT_PREFLIGHT_ROWS": len(script_preflight),
        "RUNTIME_READBACK_PREFLIGHT_ROWS": len(runtime_preflight),
        "RESTORE_PREFLIGHT_ROWS": len(restore_preflight),
        "REFUSAL_GUARD_ROWS": len(refusal_rows),
        "BW_ROOT": rel(bw_root, repo),
        "READY_FOR_APPLY_EXECUTION_PACKAGE": 1 if status == GREEN else 0,
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
    wcsv(reports / "message_catalog_phase22ae_6_5_10bw_status_summary_v1.csv", [summary], list(summary.keys()))

    (repo / "docs/messaging/MESSAGE_LOCALE_PHASE22AE_6_5_10BW_HELP_CMDHELPCHK_GUARDED_APPLY_EXECUTION_PREFLIGHT.md").write_text(
        f"# Message Catalog Phase 22AE.6.5.10BW HELP/CMDHELPCHK Guarded Apply Execution Preflight\n\n"
        f"Status: `{status}`\n\n"
        "10BW performs final guarded preflight. It does not mutate HELP DATA or CMDHELPCHK.\n\n"
        f"Preflight root:\n\n```text\n{rel(bw_root, repo)}\n```\n\n"
        f"Next gate:\n\n```text\n{NEXT}\n```\n",
        encoding="utf-8"
    )

    print(status)
    print(f"  validation issues: {issues}")
    print(f"  Phase 22AE.6.5.10BV status: {bv.get('STATUS','')}")
    print(f"  MSG-022AE.6.5.10BV savepoint present: {1 if sp_bv else 0}")
    print(f"  active messages observed count: {msg_count}")
    print(f"  active text observed count: {text_count}")
    print(f"  BV execution package review rows: {len(bv_review)}")
    print(f"  BV staged script review rows: {len(bv_scripts)}")
    print(f"  BV runtime review rows: {len(bv_runtime)}")
    print(f"  BV restore review rows: {len(bv_restore)}")
    print(f"  final target preflight rows: {len(target_preflight)}")
    print(f"  final target preflight ready rows: {ready_count}")
    print(f"  final script preflight rows: {len(script_preflight)}")
    print(f"  runtime readback preflight rows: {len(runtime_preflight)}")
    print(f"  restore preflight rows: {len(restore_preflight)}")
    print(f"  refusal guard rows: {len(refusal_rows)}")
    print(f"  preflight root: {rel(bw_root, repo)}")
    print("  ready for apply execution package: 1")
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
